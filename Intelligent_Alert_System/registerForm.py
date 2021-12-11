from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators, FileField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import Length, Email, EqualTo, DataRequired

class RegisterForm(FlaskForm):
    # username = StringField(label='User Name: ', validators=[Length(min=5, max=20), DataRequired()])
    # user_firstname = StringField(label='First Name: ', validators=[Length(min=1, max=20), DataRequired()])
    # user_lastname = StringField(label='Last Name: ', validators=[Length(min=1, max=20), DataRequired()])
    # phone = StringField(label='Phone Number: ', validators=[DataRequired(), Length(10)])
    # email_address = StringField(label='Email Address: ', validators=[Email(), DataRequired()])
    # password = PasswordField(label='Password: ', validators=[Length(min=5), DataRequired()])
    # confirmed_password = PasswordField(label='Confirm Password: ',validators=[EqualTo('password'), DataRequired()])
    # submit = SubmitField(label='Create Your Account')

    username = StringField(label='User Name: ',validators=[Length(min=3, max=30),DataRequired()])
    user_firstname = StringField(label='First Name: ',validators=[DataRequired()])
    user_lastname = StringField(label='Last Name: ',validators=[DataRequired()])
    phone = StringField(label='Phone Number: ',validators=[DataRequired()])
    email_address = StringField(label='Email Address: ', validators=[Email(),DataRequired()])
    password = PasswordField(label='Password: ', validators=[Length(min=5),DataRequired()])
    confirmed_password = PasswordField(label='Confirm Password: ',validators=[EqualTo('password'), DataRequired()])
    
    submit = SubmitField(label='Create Your Account')

class LoginForm(FlaskForm):
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')

class AddVictim(FlaskForm):
    user_firstname = StringField(label='First Name: ',validators=[DataRequired()])
    user_lastname = StringField(label='Last Name: ',validators=[DataRequired()])
    phone = StringField(label='Phone Number: ',validators=[DataRequired()])
    email_address = StringField(label='Email Address: ', validators=[DataRequired()])
    photo = FileField(label='Photo: ', validators=[FileRequired()])
    submit = SubmitField(label='Add Victim')

    
class RequestResetForm(FlaskForm):
    email = StringField(label = 'Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send')
    

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password: ', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password: ', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset')