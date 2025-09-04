from flask import Flask, render_template,url_for,redirect
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,Date,Float
from datetime import datetime
from forms import  RegisterForm, LoginForm
app = Flask(__name__)
bootstrap = Bootstrap5(app)
class Base(DeclarativeBase):
    pass

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spensly.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)
class User(UserMixin, db.Model):
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    email:Mapped[str] = mapped_column(String(100), unique=True)
    password_hash : Mapped[str] = mapped_column(String(100))
    name : Mapped[str] = mapped_column(String(100))
    expenses = db.relationship('Expense', backref='author', lazy=True)

class Expense():
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)


@app.route('/register')
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
        return redirect #redirect to home page for this specific user
    return render_template("register.html", form=form, current_user=current_user)







@app.route('/login')
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
            return redirect('home')
    return render_template("login.html",form=form,current_user=current_user)









@app.route('/')
def home():
    return render_template("index.html")

@app.route('/dashboard')
def dashboard():
    # This is the main app page after login
    return render_template("dashboard.html")




if __name__ == "__main__":
    app.run(debug=True)
