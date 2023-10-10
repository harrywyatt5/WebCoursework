from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from markupsafe import escape
import time
import enum

db = SQLAlchemy()
hashing = Bcrypt()

class TransactionStatus(enum.Enum):
    # Others might include chargeback or cancelled
    in_progress = 0
    successful = 1
    expired = 2

class AddonType(enum.Enum):
    # Values above 100 indicate they are EXCLUSIVE (the addon set must only have one option)
    toppings = 0
    extra = 1
    cheese = 100


class ProductType(enum.Enum):
    pizzas = 0
    sides = 1
    drinks = 2


class ProductAddon(db.Model):
    __tablename__ = "addons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(18), index=True, unique=True)
    type = db.Column(db.Enum(AddonType))
    value = db.Column(db.Float)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(18), index=True, unique=True)
    type = db.Column(db.Enum(ProductType))
    requires_customisation = db.Column(db.Boolean)
    # For what options are available, we are just going to use JSON
    options = db.Column(db.String(512))
    description = db.Column(db.String(128))
    env_impact = db.Column(db.Integer)
    value = db.Column(db.Float)


class CarouselImage(db.Model):
    __tablename__ = "carousel_images"

    # It is important to note that the 'id' will be where we look for the image in static/carousel
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32))
    description = db.Column(db.String(128))
    imgDescription = db.Column(db.String(64))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.mapped_column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), index=True, unique=True)
    email = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(128))
    transactions = db.relationship("Transaction", back_populates="user") 

    def set_password(self, password):
        self.password_hash = hashing.generate_password_hash(password)

    def check_password(self, attempt):
        return hashing.check_password_hash(self.password_hash, attempt)
    
    @staticmethod
    def create_user(username, password, email):
        new_user = User(username=escape(username), email=escape(email))
        new_user.set_password(escape(password))
        db.session.add(new_user)
        db.session.commit()
        return new_user
    
    

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.mapped_column(db.ForeignKey("users.id"))
    status = db.Column(db.Enum(TransactionStatus))
    products = db.Column(db.String(2048))   # JSON data including what is being bought
    price = db.Column(db.Float)
    last_update = db.Column(db.Integer)     # Last update in seconds since UNIX EPOCH
    user = db.relationship("User", back_populates="transactions")

    def update_status(self, new_status):
        self.status = new_status
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_new_transaction(user_id, products, price):
        new_transaction = Transaction(
            user_id=user_id,
            status=TransactionStatus.in_progress,
            products=products,
            price=price,
            last_update=round(time.time())
        )

        db.session.add(new_transaction)
        db.session.commit()
        return new_transaction
