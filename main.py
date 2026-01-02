
from flask import Flask, render_template,url_for,redirect,flash,request
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,Date,Float,func,extract
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from forms import  RegisterForm, LoginForm,ExpenseForm,BudgetForm         #import from other file(forms.py)
import os
from dotenv import load_dotenv
load_dotenv()




app = Flask(__name__)
bootstrap = Bootstrap5(app)
class Base(DeclarativeBase):
    pass



app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
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


class Budget(db.Model):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–12
    year: Mapped[int] = mapped_column(Integer, nullable=False)


    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))

    # back reference to user
    user = db.relationship("User", back_populates="budgets")
    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', 'year', name='unique_user_month_budget'),
    )

class Expense(db.Model):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

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
    budgets = db.relationship("Budget",back_populates="user")

with app.app_context():
    db.create_all()


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        #check for already registered users
        existing_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if existing_user :
            flash('Account Already exits!!,Please Login',"success")
            return redirect(url_for('login'))

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
            flash("That email does not exist. Please try again.","warning")#success,danger,warning,info
            #after flash msg it store in get_flashed_message() and it will print in next render template and redirect(first one only)and not any other second ,third gets nothing flash msgs
            return redirect(url_for('login'))
            #return render_template("login.html", form=LoginForm())

        elif not check_password_hash(user.password, passw):
            flash("Password incorrect. Please try again.","danger")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))




    return render_template("login.html",form=form,current_user=current_user)




@app.route('/')
def home():
    return render_template("index.html")

@app.route('/dashboard')
@login_required
def dashboard():


    form = ExpenseForm()
    now = datetime.now()
    selected = request.args.get("month") #removed this form, as we will use this idea in analysis to show monthly summary cards with insights and in whatsapp "I" u have mont/year selecter code

    if selected:
        current_year, current_month = map(int, selected.split("-"))
    else:
        now = datetime.now()
        current_year = now.year
        current_month = now.month

    # current_month = now.month
    # current_year = now.year

    # Query: Total Spent for the current month
    total_this_month_result = db.session.query(
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).scalar()
    total_this_month = total_this_month_result if total_this_month_result else 0.0

    # Query: Total Number of Transactions (for all time or this month)
    total_transactions_result = db.session.query(
        func.count(Expense.id).label('count')
    ).filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).scalar()
    total_transactions = total_transactions_result if total_transactions_result else 0

    # Query: Top Category (for current month)
    top_category_result = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).first()

    top_category = top_category_result[0] if top_category_result else "N/A"
    top_category_amount = top_category_result[1] if top_category_result else 0


    #FOR BUDGET SUMMARY CARD
    #month_budget = db.session.query(Budget.amount).filter_by(Budget.user_id==current_user.id,Budget.month==current_month,Budget.year==current_year).scalar()
    # month_budget = db.session.query(        #for saftey for no result,we can use 'if' but coalsec is better as it works with database“I prefer COALESCE because it ensures aggregate queries never return NULL, enforcing data safety at the database layer and reducing error-prone checks in application code.”
    #     func.coalesce(Budget.amount, 0)
    # ).filter_by(
    #     user_id=current_user.id,
    #     month=current_month,
    #     year=current_year
    # ).scalar()
    month_budget = (
                       db.session.query(Budget.amount)
                       .filter(
                           Budget.user_id == current_user.id,
                           Budget.month == current_month,
                           Budget.year == current_year
                       )
                       .scalar()
                   ) or 0.0

    left = month_budget-total_this_month
    percentage = 0
    if month_budget > 0:
        percentage = min(100, (total_this_month / month_budget) * 100)

    # if form.validate_on_submit():
    #     new_expense = Expense(
    #         amount=form.amount.data,
    #         description=form.description.data,   #make description such that many lines of description look neatly
    #         category=form.category.data,
    #         date=form.date.data,
    #         user_id=current_user.id
    #     )
    #     db.session.add(new_expense)
    #     db.session.commit()
    #     flash("Expense added successfully!", "success")
    #     return redirect(url_for("dashboard"))

    expenses = (
                Expense.query
                .filter_by(user_id=current_user.id)
                .order_by(Expense.date.desc(), Expense.id.desc())
                .limit(10)              #limitng no.of trans to be shown
                .all()
                )


    # all_expenses = (
    #             Expense.query
    #             .filter_by(user_id=current_user.id)
    #             .order_by(Expense.date.desc(), Expense.id.desc())
    #             .all()
    #             )
    insight_text = "dsfiosdfgjfbbbsdgfsgfsdgggggsfgd"
    overspent = total_this_month > month_budget and month_budget > 0
    overspend_amount = max(0, total_this_month - month_budget)

    overspend_category = top_category if overspent else None
    overspend_percent = (
        (top_category_amount / total_this_month) * 100
        if total_this_month > 0 else 0
    )

    return render_template("dashboard.html",
                           form=form,
                           overspend_category=overspend_category,
                           overspend_amount=overspend_amount,
                           overspend_percent=overspend_percent,
                           overspent=overspent,
                           expenses=expenses,
                           month_budget=month_budget,
                           left=left,
                           selected_month=current_month,
                           selected_year=current_year,
                           percentage=percentage,
                           total_this_month=total_this_month,
                           total_transactions=total_transactions,
                           top_category=top_category,
                           top_category_amount=top_category_amount)

@app.route('/expense/add', methods=["POST"])
@login_required
def add_expense():
    form = ExpenseForm()

    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            category=form.category.data,
            date=form.date.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully!", "success")

    return redirect(url_for("dashboard"))

@app.route("/delete/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    expense_to_delete = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404() #when user may change in link website like /15 -> /5
    db.session.delete(expense_to_delete)
    db.session.commit()
    flash("Expense deleted successfully!", "success")
    return redirect(url_for('view_trans'))





@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    form = ExpenseForm(obj=expense)  # pre-fill form with expense data

    if form.validate_on_submit():
        expense.category = form.category.data
        expense.description = form.description.data
        expense.amount = form.amount.data
        expense.date = form.date.data
        db.session.commit()
        flash("Expense updated successfully!", "success")
        return redirect(url_for("view_trans"))

    return render_template("edit_expense.html", form=form)



@app.route("/transactions", methods=["GET"])
@login_required
def view_trans():

    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    sort = request.args.get("sort")

    query = Expense.query.filter(
        Expense.user_id == current_user.id
    )

    if category:
        query = query.filter(Expense.category == category)

    if start_date:
        query = query.filter(Expense.date >= start_date)

    if end_date:
        query = query.filter(Expense.date <= end_date)

    if sort == "date_asc":
        query = query.order_by(Expense.date.asc(), Expense.id.asc())

    elif sort == "date_desc":
        query = query.order_by(Expense.date.desc(), Expense.id.desc())

    elif sort == "amount_asc":
        query = query.order_by(Expense.amount.asc(), Expense.id.desc())

    elif sort == "amount_desc":
        query = query.order_by(Expense.amount.desc(), Expense.id.desc())

    else:
        query = query.order_by(Expense.date.desc(), Expense.id.desc())

    all_expenses = query.all()

    return render_template(
        "transactions.html",
        all_expenses=all_expenses
    )


@app.route('/budget',methods=["GET", "POST"])
@login_required
def add_budget():
    b_form = BudgetForm()
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    #COALESCE is the database equivalent of writing an if to replace None with 0.
    # total_this_month_result = db.session.query(
    #     func.sum(Expense.amount).label('total')
    # ).filter(
    #     Expense.user_id == current_user.id,
    #     extract('month', Expense.date) == current_month,
    #     extract('year', Expense.date) == current_year
    # ).scalar()
    # total_this_month = total_this_month_result if total_this_month_result else 0.0

    total_this_month = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).scalar()
    if current_month == 1:
        last_month = 12
        last_year = current_year - 1
    else:
        last_month = current_month - 1
        last_year = current_year

    last_month_spent = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.date) == last_month,
        extract('year', Expense.date) == last_year
    ).scalar()

    last_month_budget_obj = Budget.query.filter_by(
        user_id=current_user.id,
        month=last_month,
        year=last_year
    ).first()

    last_month_budget = (
        last_month_budget_obj.amount if last_month_budget_obj else None
    )
    if b_form.validate_on_submit():
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            month=current_month,
            year=current_year
        ).first()

        if existing_budget:
            existing_budget.amount = b_form.amount.data
        else:
            new_budget = Budget(
                amount=b_form.amount.data,
                month=current_month,
                year=current_year,
                user_id=current_user.id
            )
            db.session.add(new_budget)

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("budget.html",
                           form=b_form,total_this_month=total_this_month,
                           last_month_spent=last_month_spent,
                           last_month_budget=last_month_budget)





@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
