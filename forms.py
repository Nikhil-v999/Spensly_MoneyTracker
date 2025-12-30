from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField,DecimalField,SelectField,DateField
from wtforms.validators import DataRequired, URL,Optional
from datetime import date

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")



class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In!")


class ExpenseForm(FlaskForm):
    amount = DecimalField("Amount",
                          places=2,
                          validators=[DataRequired()],
                          render_kw={"step": "0.01"})

    description = StringField("Description",validators=[Optional()])
    date = DateField("Expense Date", default=date.today, validators=[DataRequired()])
    category = SelectField("Category",
                           choices=[
                               ("Food & Dining", "Food & Dining"),       #Each tuple in choices is (value, label):.value = what gets stored in the database when selected.
                                ("Transportation", "Transportation"),    #label = what the user sees in the dropdown
                               ("Entertainment", "Entertainment"),
                               ("Personal Care", "Personal Care"),
                               ("Clothing", "Clothing"),
                               ("Other", "Other")
                           ],
                           validators=[DataRequired()])

    submit = SubmitField("Add Expense")
