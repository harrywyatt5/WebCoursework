'''
Name: custom_validators.py
Student No.: 22033329

Custom validators for the purpose of making sure our form entries are correct
Info on how to do this is here: https://wtforms.readthedocs.io/en/2.3.x/validators/#custom-validators
'''
from wtforms.validators import ValidationError
from database import User

class IsUnique(object):
    def __init__(self, table, table_column, message=None):
        self.table = table # Of type db.Model
        self.table_column = table_column
        if message == None:
            self.message = f'Account already exists wih that {table_column}'
        else:
            self.message = message

    def __call__(self, form, field):
        args = {self.table_column: field.data}
        result = self.table.query.filter_by(**args).first()

        if result != None: raise ValidationError(self.message)


class IsValidCredentials(object):
    def __init__(self, form_username, form_password, message=None):
        self.username = form_username
        self.password = form_password

        if message == None:
            self.message = 'Incorrect username or password'
        else:
            self.message = message

    def __call__(self, form, field):
        if not self.username in form.__dict__ and not self.password in form.__dict__:
            raise TypeError("Username and password fields could not be found in the form")
        
        # Find the user first
        username = form.__dict__[self.username]
        user = User.query.filter_by(username=username.data).first()

        if not user: raise ValidationError(self.message)
        if not user.check_password(form.__dict__[self.password].data): raise ValidationError(self.message)
