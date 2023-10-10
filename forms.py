from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Regexp, Optional
from custom_validators import *
from database import User



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1,25), IsValidCredentials("username", "password")])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')



class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1,25), IsUnique(User, "username")])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 128)])
    email = StringField('Email', validators=[DataRequired(), Length(1,32), Email(), IsUnique(User, "email")])
    submit = SubmitField("Submit")



class PurchaseForm(FlaskForm):
    card_number = StringField('Card Number', validators=[DataRequired(), Regexp("^[0-9]{16}$")])
    cvc = StringField('CVC', validators=[DataRequired(), Regexp("^[0-9]{3}$")])
    expiry_month = SelectField("Expiry Month", default=5, choices=list(range(1,13)))
    expiry_year = SelectField("Expiry Month", default=2025, choices=list(range(2023, 2031)))

    name = StringField('Full Name', validators=[DataRequired(), Regexp("^[a-zA-Z\s]{3,26}$")])
    address_1 = StringField('Address 1', validators=[DataRequired(), Regexp("^[0-9A-Za-z\s]{3,32}$")])
    address_2 = StringField('Address 2', validators=[Optional(), Regexp("^[0-9A-Za-z\s]{3,32}$")])
    county = StringField('County', validators=[DataRequired(), Regexp("^[a-zA-Z]{3,12}$")])
    # Regex for postcodes based on p.2 https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/611951/Appendix_C_ILR_2017_to_2018_v1_Published_28April17.pdf
    postcode = StringField('Postcode', validators=[DataRequired(), Regexp("^[a-zA-Z]{1,2}[0-9]{1,2}[a-zA-Z]?\s[0-9][a-zA-Z]{2}$")])
    submit = SubmitField("Submit")

    