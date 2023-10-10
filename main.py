from flask import Flask, abort, render_template, request, jsonify, url_for, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import *
from forms import *
import Util
import json


MAX_TRANSACTION_TIME = 300   # Time in seconds until a transaction expires

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testKeyRightNow123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
db.init_app(app)
hashing.init_app(app)
lm = LoginManager(app)
lm.login_view = "login"


# Tells the LoginManager how to get a user
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/', methods=['GET'])
def index():
    carousel_items = CarouselImage.query.all()
    products = Product.query.all()

    grouped_products = Util.group_per_type(products)
    return render_template('index.html', carousel_items=carousel_items, products=grouped_products)


@app.route('/product/<int:product_id>', methods=['GET'])
def product_page(product_id):
    # First, find the product in question
    product = Product.query.filter_by(id=product_id).first()

    # quit if the product can't be found
    if product == None: return abort(404)

    # Find and order the associated addons
    addons = []
    addon_data = json.loads(product.options)
    for addon in addon_data:
        addons.append(ProductAddon.query.filter_by(id=addon).first())
    
    return render_template('product.html', product=product, processed_options=Util.group_per_type(addons))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # If the user data is valid, log in
        user = User.query.filter_by(username=form.username.data).first()  
        login_user(user, form.remember_me.data)
        
        return redirect(request.args.get('next') or url_for('index'))
    
    return render_template('login.html', form=form)


@app.route("/acknowledgements", methods=["GET"])
def acknow():
    return render_template("acknowledgements.html")


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()

    return redirect(request.args.get('next') or url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # If we have a valid new user, create them
        new_user = User.create_user(form.username.data, form.password.data, form.email.data)

        # And log this new user in and go to the home page
        login_user(new_user, False)
        return redirect(url_for('index'))

    return render_template("register.html", form=form)


@app.route('/history', methods=['GET'])
@login_required
def history():
    # This page shows the transaction history of the user
    transactions = Transaction.query.filter_by(user_id=current_user.get_id(), status=TransactionStatus.successful)
    transaction_list = []

    # Convert into usable objects
    for transaction in transactions:
        products_bought = json.loads(transaction.products)
        processed_products = []

        # process each product bought
        for product in products_bought:
            potential_product = Util.PotentialProduct(product["itemId"], product["options"])

            # Skip if this product no longer is available
            if not potential_product.does_exist(): continue

            processed_products.append(potential_product.__dict__())

        # Create a usable object entry
        transaction_list.append({
            "id": transaction.id,
            "date": Util.get_date_from_epoch(transaction.last_update),
            "price": transaction.price,
            "products": processed_products
        })

    return render_template("history.html", transactions=transaction_list)



@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    transaction_id = request.args.get('id')

    if transaction_id != None \
        and (transaction := Transaction.query.filter_by(id=transaction_id).first()) != None \
        and transaction.user_id == int(current_user.get_id()) \
        and transaction.status == TransactionStatus.in_progress:

        # If we ran out of time to finish the transaction
        if (time.time() - transaction.last_update) >= MAX_TRANSACTION_TIME:
            transaction.update_status(TransactionStatus.expired)
            return redirect(url_for('index'))
        
        form = PurchaseForm()
        if form.validate_on_submit():
            # Here, we would implement a payment platform to process our monies

            # Mark the order as finished
            transaction.update_status(TransactionStatus.successful)

            # Get what we ordered
            items_bought = json.loads(transaction.products)
            first_obj = Util.PotentialProduct(items_bought[0].get("itemId")).does_exist()

            return render_template('successful_purchase.html', first_item=first_obj, products_count=len(items_bought))

        
        return render_template("purchase.html", purchase_id=transaction_id, form=form)
    else:
        return redirect(url_for('index'))


@app.route('/api/v1/GetItemsData', methods=['POST'])
def find_items():
    '''
    An api endpoint that allows a JSON of a basket in the
    format [ {"itemId": id, "options": [...]}}, ... ]
    and returns info about the basket in the format
    [ {"productId": id, "productName": name, "productDescription": desc, "options": [ {"optionId": id, "optionName": name} ... ]}, ...]
    '''
    data = json.loads(request.data)
    response = []

    for basket_item in data:
        potential_product = Util.PotentialProduct(basket_item.get("itemId"), basket_item.get("options"))

        # Skip over value that don't exist (forigivng)
        if potential_product.does_exist() == None: continue

        # Else, add it to our response
        response.append(potential_product.__dict__())

    return jsonify(response)


@app.route('/api/v1/MakeTransactionContext', methods=['POST'])
def make_transaction():
    '''
    Upon receiving a basket contents in the format
     [ {"itemId": id, "options": [...]}}, ... ]
    makes a Transaction and returns the id
    and total price in format JSON: {"price": x, "transactionId": y}

    Requires all products and addons to exist and be valid, else will bad request returned
    Requires a logged in user, else unauthorised returned
    '''
    # Users must be logged in to make a new content
    if not current_user.is_authenticated: return jsonify({"error": "You must be logged in to do this"}), 401

    incoming_data = json.loads(request.data)
    total_price = 0.0
    # Now check if objects in the order are valid
    # Unlike other API endpoints, objects must be perfect (valid object, valid addon)
    # If not, the whole order transaction will be cancelled
    for basket_item in incoming_data:
        potential_product = Util.PotentialProduct(basket_item.get("itemId"), basket_item.get("options"))

        # Reject request if product does not exist
        product = potential_product.does_exist()
        if product == None: 
            return jsonify({"error": f'{basket_item.get("itemId")} does not exist'}), 400
        
        # Calculate sum of addons and if products are valid
        try:
            total_price += product.value + potential_product.get_options_and_price(check_integrity=True)[0]
        except ValueError as e:
            # If we've got a value error, then one of the options was invalid. Abort
            print("Error: " + str(e))
            return jsonify({"error": f"An addon on {basket_item['itemId']} was invalid"}), 400

    # All items are valid, make a transaction
    transaction = Transaction.create_new_transaction(current_user.get_id(), request.data, total_price)

    return jsonify({"price": total_price, "transactionId": transaction.id})


@app.route('/api/v1/QueryItems', methods=['POST'])
def query_items():
    '''
    Takes a json of {"query": x} and finds items that contain said
    substring in their name

    Returns an array of items, where each item is represented
    {"productId": id, "productName": name, "productEco": eco, "productPrice": price}
    '''
    data = json.loads(request.data)
    query = data.get("query")
    results = []

    if not data.get("query"): return jsonify({"error": f"Query must be specified"}), 400
    
    query_results = []

    if query == "ALL":
        query_results = Product.query.all()
    else:
        query_results = Product.query.filter(Product.name.contains(query))

    for result in query_results:
        results.append({
            "productId": result.id,
            "productName": result.name,
            "productEco": result.env_impact,
            "productPrice": result.value
        })

    return jsonify(results)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()