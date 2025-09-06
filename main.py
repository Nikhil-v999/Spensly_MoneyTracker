
from flask import Flask, render_template,url_for,redirect,flash
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,Date,Float
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from forms import  RegisterForm, LoginForm,ExpenseForm
app = Flask(__name__)
bootstrap = Bootstrap5(app)
class Base(DeclarativeBase):
    pass

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

login_manager.login_view = "login"  # redirects here if not logged in
login_manager.login_message = "Please log in to access the dashboard."
login_manager.login_message_category = "warning"


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spensly.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Expense(db.Model):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))

    # back reference to user
    user = db.relationship("User", back_populates="expenses")

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    email:Mapped[str] = mapped_column(String(100), unique=True)
    password : Mapped[str] = mapped_column(String(100))
    name : Mapped[str] = mapped_column(String(100))
    expenses = db.relationship("Expense", back_populates="user")


with app.app_context():
    db.create_all()


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        #need to salt or hash pass
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form, current_user=current_user)







@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        passw = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("The email doest exist,try again bro!!")
            return redirect(url_for('login'))
        # elif not #for password correct or wrong

        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html",form=form,current_user=current_user)











@app.route('/')
def home():
    return render_template("index.html")

@app.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():


    form = ExpenseForm()
    if form.validate_on_submit():
        new_expense = Expense(
            amount=form.amount.data,
            description=form.description.data,   #make description such that many lines of description look neatly
            category=form.category.data,
            date=form.date.data,
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for("dashboard"))

    expenses = (Expense.query
                .filter_by(user_id=current_user.id)
                .order_by(Expense.date.desc(), Expense.id.desc())
                .all())

    return render_template("dashboard.html", form=form, expenses=expenses)


@app.route("/delete/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    expense_to_delete = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense_to_delete)
    db.session.commit()
    flash("Expense deleted successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route("/edit/<int:expense_id>")
@login_required
def edit_expense(expense_id):
    expense_to_edit = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense_to_delete)
    db.session.commit()
    flash("Expense edited successfully!", "success")
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
