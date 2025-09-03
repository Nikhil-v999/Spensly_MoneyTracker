from flask import Flask, render_template,url_for
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,Date,Float
from datetime import datetime

app = Flask(__name__)
bootstrap = Bootstrap5(app)
class Base(DeclarativeBase):
    pass
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















@app.route('/')
def home():
    return render_template("index.html")

@app.route('/dashboard')
def dashboard():
    # This is the main app page after login
    return render_template("dashboard.html")




if __name__ == "__main__":
    app.run(debug=True)
