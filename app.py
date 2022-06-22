import os

#from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers2 import apology, login_required, lookup, usd

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Configure application
app = Flask(__name__)

#configure SQLAlchemy to use sqlite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance2.db"

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
#tell app to support sessions
Session(app)

"""# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")"""

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#Turn off wanrings when opening the database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#create variable to use for the databases using SQLAlchemy
db = SQLAlchemy(app)

# Make sure API key is set
"""
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
"""

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#Create model for the database
class Users(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False)
    hash = db.Column(db.String(110), nullable=False)
    cash = db.Column(db.Numeric, default=10000.00, nullable=False)
    stocks_user_id = db.relationship('Stocks', backref = "user_stocks")
    transactions_user_id = db.relationship("Transactions", backref = "transactions_user_id")

class Stocks(db.Model):

    __tablename__ = "stocks"
    stock_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    symbol = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Numeric, nullable=False)

class Transactions(db.Model):

    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    symbol = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Numeric, nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    type = db.Column(db.String, nullable=False)
    transaction_time = db.Column(db.DateTime, default=datetime.utcnow)



@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #extracting a list of dictionaries containing the stocks the user holds
    #stocks_owned = db.execute("SELECT * FROM stocks WHERE user_id=?", session["user_id"])
    stocks_owned = Stocks.query.filter_by(user_id = session["user_id"]).all()

    #getting how much cash the user currently holds
    user_cash = Users.query.filter_by(id = session["user_id"]).first()
    cash = user_cash.cash

    #initializing the total assets the user has
    #the for loop below will loop thru each stock the user owns and add onto the grand total
    grand_total = cash

    #creating a list of dictionaries for each stock the user owns
    stocks = []

    #looping thru each stock and adding the name, price, and total value the user holds
    for user_stock in stocks_owned:

        #looking up the stock info
        x = lookup(stocks["symbol"])
        
        #creaing a temp dictionary to fill in the stock info
        tmp = {}

        #filling in the stock info
        tmp["name"] = x["name"]
        tmp["price"] = x["price"]
        tmp["total"] = x["price"] * user_stock.quantity

        #adding to the total amount of money the user currently hold (stocks and cash)
        grand_total += tmp["total"]

        #appending the dictionary of the stock info to the list
        stocks.append(tmp)

    return render_template("index.html", stocks=stocks, grand_total=grand_total, cash=cash)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        #using the API to look up the symbol based on the symbol the user submitted
        info = lookup(request.form.get("symbol"))

        #checking to see if symbol exists
        if not info:
            return apology("Invalid Symbol")

        #getting the number of stocks to buy from the user
        qty = float(request.form.get("shares"))

        #if user inputs a non positive integer for stocks
        if qty < 1:
            return apology("Invalid amount of shares")

        #extracting user's current balance
        #cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        #cash = cash[0]["cash"]
        user_info = Users.query.filter_by(id = session["user_id"]).first()

        #checking whether user has sufficient cash to purchase stocks
        remaining_balance = user_info.cash - info["price"]*qty
        if remaining_balance < 0:
            return apology("Insufficient funds to make purchase")

        #if user does have sufficient cash, update the tables
        #db.execute("UPDATE users SET cash = ? WHERE id = ?", remaining_balance, session["user_id"])
        #db.execute("INSERT INTO transactions (user_id, symbol, quantity, amount, type, transaction_time) VALUES(?,?,?,?,?,DATETIME())", session["user_id"], info["symbol"], qty, info["price"]*qty, "Bought")

        #Updating the users cash in the table if the user has sufficient cash
        user_info.cash = remaining_balance

        #logging the user's transaction by creating a new row in the transactions table
        db.session.add(Transactions(user_id=session["user_id"], symbol=info["symbol"], quantity=qty, amount=info["price"]*qty, type="Bought"))

        #extracting the qty of stocks the user owns for that particular symbol
        #existing_stock = db.execute("SELECT quantity FROM stocks WHERE user_id = ? AND symbol = ?", session["user_id"], info["symbol"])

        #getting the user's balance info for a particular stock
        user_stock = Stocks.query.filter_by(user_id = session["user_id"], symbol=info["symbol"]).first()

        #If user does not own any of that particular stock, add a new row for that stock
        if not user_stock:
            #db.execute("INSERT INTO stocks (user_id, symbol, quantity) VALUES(?,?,?)", session["user_id"], info["symbol"], qty)
            db.session.add(Stocks(user_id=session["user_id"], symbol=info["symbol"], quantity=qty))

        #if user already owns that particular stock
        else:
            #db.execute("UPDATE stocks SET quantity = ? WHERE user_id = ? AND symbol = ?", existing_stock[0]["quantity"] + qty, session["user_id"], info["symbol"])
            user_stock.quantity += qty

        #commiting the changes made to the db variable to the database file
        db.session.commit()
        

        #redirecting the user back to the buy page
        #flashing the user that the purchase was successful
        flash("Purchase successful")
        return redirect("/buy")

    if request.method == "GET":
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    #getting all data from the transaction table
    #rows = db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY transaction_time DESC", session["user_id"])

    user_transactions = Transactions.query.filter_by(user_id=session["user_id"]).order_by(Transactions.transaction_time.desc()).all()

    #going thru each dictionary and adding the full company name using the API

    #creating a dictionary for already existing names to reference off of
    names = {}

    #creating a list of dictionaries for each transaction 
    rows = []
    for transaction in user_transactions:

        #creating a temp dictionary to fill in the transaction info 
        tmp = {}

        #filling in the transaction info
        tmp["quantity"] = transaction.quantity
        tmp["amount"] = transaction.amount
        tmp["type"] = transaction.type
        tmp["transaction_time"] = transaction.transaction_time

        #if the name already exists in the dict use that one otherwise lookup the name with the API
        if transaction.symbol in names:
            tmp["name"] = names[transaction.symbol]
        else:
            tmp["name"] = lookup(transaction.symbol)["name"]
        
        #appending the current transaction info dictionary to the list
        rows.append(tmp)

    #returning the html template while passing on the rows object
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        user_info = Users.query.filter_by(username=username).first()

        # Ensure username exists and password is correct
        if user_info == None or not check_password_hash(user_info.hash, password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user_info.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    #if user is trying to access stock quotes
    if request.method == "GET":
        return render_template("quote.html", alert=False)

    #if user submitted a form to look up the quote
    elif request.method == "POST":

        #getting the symbol the user submitted
        symbol_result = request.form.get("symbol")

        #using the API to look up the symbol
        info = lookup(symbol_result)

        #checking to see if symbol exists
        if not info:
            #use an alert via javascript to tell user symbol does not exist
            #i could also do this:
            #flash("Invalid Symbol")
            return render_template("quote.html", alert=True)

        #return template with the requested stock quotes
        return render_template("/quote_results.html", information = info)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #if user clicked on "register" via the login page
    if request.method == "GET":
        return render_template("register.html")

    #If user has submitted their information to register
    elif request.method == "POST":
        username1 = request.form.get("username")
        password_1 = request.form.get("password_1")
        password_2 = request.form.get("password_2")

        #check if user populated the username and password textboxes
        if not username1 or not password_1:
            return apology("Invalid username or password", 404)

        #check if user input the same password twice
        elif password_1 != password_2:
            return apology("Passwords do not match", 404)

        #make sure username isn't taken by checking length of database query response with said username
        if Users.query.filter_by(username=username1).first() != None:
            return apology("Username already taken", 404)

        #add the new user's information into the user table in the database
        #the user's password is hashed for security purposes
        db.session.add(Users(username=username1, hash=generate_password_hash(password_1)))

        #commit the changes made to the database file
        db.session.commit()

        #Redirect user to the login page
        flash("Registered Successfully")
        return redirect("/login")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        #getting the current stock information
        info = lookup(request.form.get("symbol"))

        #checking to see if symbol exists
        if not info:
            return apology("Invalid Symbol")

        #getting the number of stocks to sell from the user
        qty = float(request.form.get("shares"))

        #if user inputs a non positive integer for stocks
        if qty < 1:
            return apology("Invalid amount of shares")

        #extracting how many shares the user holds for that particular stock
        #stock_qty = stocks[0]["quantity"]

        #extracting how many shares the user holds for that particular stock
        user_stocks = Stocks.query.filter_by(user_id=session["user_id"], symbol=info["symbol"]).first()


        #checking whether user owns enough shares to sell that much stock
        if user_stocks.quantity < qty:
            return apology("Insufficient amount of shares to sell")

        #extracting user's current balance
        #cash = cash[0]["cash"]

        #querying the databse for the user's info
        user_info = Users.query.filter_by(id=session["user_id"]).first()

        #updating new balance for the user after selling stock
        user_info.cash += qty*info["price"]
        
        #logging the user's transaction by creating a new row in the transactions table
        db.session.add(Transactions(user_id=session["user_id"], symbol=info["symbol"], quantity=qty, amount=info["price"]*qty, type="Sold"))

        #Updating the amount of shares left in that stock
        user_stocks.quantity -= qty 

        #committing the changes made to the database file
        db.session.commit()

        #redirecting the user back to the buy page
        #flashing the user that the purchase was successful
        flash("Sold successfully")
        return redirect("/sell")

    if request.method == "GET":
        #Getting the names of the stock the user owns and passing it to the html file
        stocks = Stocks.query.filter_by(user_id=session["user_id"]).all()

        #creating a list of dictionaries of the stock name
        stock_names = []

        #going thru each dictionary and adding the full company name along with the symbol
        for stock in stocks:

            #creating a tmp dictionary to fill in the stock name and symbol
            tmp = {}

            #filling in the stock name and symbol
            tmp["name"] = lookup(stock.symbol)["name"]
            tmp["symbol"] = stock.symbol

            #appending the dictionary to the list
            names.append(tmp)

        return render_template("sell.html", stock_name=stock_names)

@app.route("/change_pswd", methods=["GET", "POST"])
@login_required
def change_pswd():
    """Change the user's password"""

    #if the user submits the form
    if request.method == "POST":

        #Get the user's data from the requesting user
        user_info = Users.query.filter_by(id=session["user_id"])

        #get the user's old password
        old_password = request.form.get("old_password")

        #check the hash of the user's password and compare with the input
        if not check_password_hash(user_info.hash, old_password):

            #redirect to page with message if user inputs incorrect password
            flash("Password is incorrect")
            return redirect("/change_pswd")

        #if user entered the correct password
        else:
            new_password = request.form.get("password_2")

        #changing the password in the sql table
        user_info.hash = generate_password_hash(new_password)

        #commiting the changes made to the database
        db.session.commit()

        #telling the user that the password was updated and redirecting them back to the main page
        flash("Password was successfully updated")
        return redirect("/")

    #if the user is directed to the page
    else:
        return render_template("change_pswd.html")



@app.route("/buy_more", methods=["GET", "POST"])
@login_required
def buy_more():
    """Buy more shares of existing stock"""
    if request.method == "GET":
        """Use method get to receive what stock user wants to buy"""

        #Use request.form.get for Post submitions
        #Use request.args.get for Get submitions
        #use request.values.get if it doesnt matter
        info = lookup(request.args.get("symbol"))

        return render_template("buy_more.html", stock=info)

    elif request.method == "POST":
        #using the API to look up the symbol based on the symbol the user submitted
        info = lookup(str(request.form.get("symbol")))

        #getting the number of stocks to buy from the user
        qty = float(request.form.get("shares"))

        #if user inputs a non positive integer for stocks
        if qty < 1:
            return apology("Invalid amount of shares")

        #extracting user's current balance
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = cash[0]["cash"]

        #Get the user's data from the requesting user
        user_info = Users.query.filter_by(id=session["user_id"])


        #checking whether user has sufficient cash to purchase stocks
        remaining_balance = user_info.cash - info["price"]*qty
        if remaining_balance < 0:
            return apology("Insufficient funds to make purchase")

        #if user does have sufficient cash, update the tables
        db.execute("UPDATE users SET cash = ? WHERE id = ?", remaining_balance, session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, quantity, amount, type, transaction_time) VALUES(?,?,?,?,?,DATETIME())", session["user_id"], info["symbol"], qty, info["price"]*qty, "Bought")

        #Updating the users cash in the table if the user has sufficient cash
        user_info.cash = remaining_balance

        #logging the user's transaction by creating a new row in the transactions table
        db.session.add(Transactions(user_id=session["user_id"], symbol=info["symbol"], quantity=qty, amount=info["price"]*qty, type="Bought"))

        #getting the user's balance info for a particular stock
        user_stock = Stocks.query.filter_by(user_id = session["user_id"], symbol=info["symbol"]).first()

        #updating the amount of stock the user has
        user_stock.quantity += qty

        #commiting the changes made to the db variable to the database file
        db.session.commit()

        #redirecting the user back to the index page
        #flashing the user that the purchase was successful
        flash("Purchase successful")
        return redirect("/")


@app.route("/sell_more", methods=["GET", "POST"])
@login_required
def sell_more():
    """Sell more shares of existing stock"""
    if request.method == "GET":
        info = lookup(request.args.get("symbol"))

        #render the sell_more html file
        return render_template("sell_more.html", stock=info)

    else:
        #getting the current stock information
        info = lookup(request.form.get("symbol"))

        #getting the number of stocks to sell from the user
        qty = float(request.form.get("shares"))

        #if user inputs a non positive integer for stocks
        if qty < 1:
            return apology("Invalid amount of shares")

        #extracting how many shares the user holds for that particular stock
        #stocks = db.execute("SELECT quantity FROM stocks WHERE user_id=? AND symbol=?", session["user_id"], info["symbol"])
        #stock_qty = stocks[0]["quantity"]

        #extracting how many shares the user holds for that particular stock
        user_stocks = Stocks.query.filter_by(user_id=session["user_id"], symbol=info["symbol"]).first()
    
        #checking whether user owns enough shares to sell that much stock
        if user_stocks.quantity < qty:
            return apology("Insufficient amount of shares to sell")

        #extracting user's current balance
        #cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        #cash = cash[0]["cash"]

        #querying the databse for the user's info
        user_info = Users.query.filter_by(id=session["user_id"]).first()

        #updating new balance for the user after selling stock
        user_info.cash += qty*info["price"]

        #logging the user's transaction by creating a new row in the transactions table
        db.session.add(Transactions(user_id=session["user_id"], symbol=info["symbol"], quantity=qty, amount=info["price"]*qty, type="Sold"))

        #Updating the amount of shares left in that stock
        user_stocks.quantity -= qty 

        #committing the changes made to the database file
        db.session.commit()

        #redirecting the user back to the buy page
        #flashing the user that the purchase was successful
        flash("Sold successfully")
        return redirect("/")


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    if request.method == "POST":
        #getting how much cash the user wants to deposit
        deposit_amount = float(request.form.get("quantity"))

        #querying the databse for the user's info
        user_info = Users.query.filter_by(id=session["user_id"]).first()
        
        #Updating the amount of cash the user has
        user_info.cash += deposit_amount

        #committing the changes made to the database file
        db.session.commit()

        #telling the user that the deposit was successful
        flash("Deposit successful")
        return redirect("/")

    else:
        #getting how much cash the user currently holds
        #querying the databse for the user's info
        user_info = Users.query.filter_by(id=session["user_id"]).first()

        #rendering the html template and passing along the cash amount
        return render_template("add_cash.html", cash=user_info.cash)

