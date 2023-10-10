from database import Product, ProductAddon
from datetime import datetime
import json



def group_per_type(items):
    '''
    Takes an array of Items and checks the type attribute,
    ultimately forming a dictionary of {Enum: [...], Enum: [...]}
    '''

    final_dict = {}
    for item in items:
        item_type = item.type

        if item_type in final_dict:
            final_dict[item_type].append(item)
        else:
            final_dict[item_type] = [item]

    return final_dict


def get_date_from_epoch(time):
    '''
    Takes an EPOCH timestamp and converts it into a short date
    dd/mm/yy
    '''
    return datetime.fromtimestamp(time).strftime("%d/%m/%y")


class PotentialProduct:
    def __init__(self , product_id, options=[]):
        # If they didn't pass a product_id, skip looking it up
        self.product = Product.query.filter_by(id=product_id).first() if product_id != None else None
        self.options = options  # Options are only looked-up on get_options
    
    def does_exist(self):
        '''
        Check to see if the product 'exists'
        However, further integrity of the product is not performed
        Returns Product class, or None
        '''
        return self.product

    def get_options_and_price(self, check_integrity=False):
        '''
        Gets all the options of the PotentialProduct and their total price
        If check_integrity = True, will raise ValueError on invalid option for product
        Returns a tuple of the price and a list of ProductAddons
        '''
        final_list = []
        total_price = 0.0
        product_options = None if not check_integrity else json.loads(self.product.options)
        
        for option in self.options:
            # Ensure option is an id
            option = int(option)
            option_in_db = ProductAddon.query.filter_by(id=option).first()

            if option_in_db == None:
                if not check_integrity: continue
                if check_integrity: raise ValueError("Option could not be found")

            if not check_integrity or check_integrity and option_in_db.id in product_options:
                total_price += option_in_db.value
                final_list.append(option_in_db)
            else:
                raise ValueError("Option does not belong to this Product")

        return (total_price, final_list)
    
    def __dict__(self):
        '''
        Allow this entity to be serialised to JSON easier
        '''
        addons_price, options = self.get_options_and_price()

        return {
            "productId": self.product.id,
            "productName": self.product.name,
            "productDescription": self.product.description,
            "options": [{"optionId": option.id, "optionName": option.name} for option in options],
            "productPrice": self.product.value + addons_price
        }