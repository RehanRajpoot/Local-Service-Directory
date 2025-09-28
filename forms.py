from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class ProviderForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact = StringField('Contact', validators=[DataRequired()])
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    submit = SubmitField('Register')
