from flask import Flask, render_template, redirect, flash, request, session
from flask_session import Session
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os


app = Flask(__name__)

# Configure mail properties to be able to send Emails.
app.config["MAIL_SERVER"] = "mail.gmx.net"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "michelle.nickel96@gmx.de"
app.config["MAIL_PASSWORD"] = os.environ.get("DB_PASSWORD")
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
mail = Mail(app)

# Ensure the session is not permanent and expires at some point.
app.config["SESSION_PERMANENT"] = False
# Use a Filesystem and store data in the hard drive in a /flask_session folder. An alternative to using a database.
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize database
connecc = sqlite3.connect('beschwerde.db', check_same_thread=False)
connecc.execute(""" CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL)
""")
# connecc.execute("CREATE IF NOT EXIST UNIQUE INDEX username ON users (username)")
dbCursor = connecc.cursor()


@app.route("/")
def index():
    if "user_id" in session:
        # If a user is logged in, direct them to the homepage
        return render_template("home.html")
    else:
        # If not, direct them to the about page
        return redirect("/about")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register(): 
    # Define a constant variable for register.html site
    REGISTER_PAGE = "register.html"

    # User reached the site via get request
    if request.method == "GET":
        return render_template(REGISTER_PAGE)
    
    # User reached the site via post request
    else:
        # Ensure user typed in a username
        if not request.form.get("username"):
            # Flash error message on top of site
            flash("Please enter a username.", 'danger')
            return render_template(REGISTER_PAGE)
        # Ensure user typed in a password and repeated it
        elif not request.form.get("password") or not request.form.get("confirmPassword"):
            # Return error message on top of site
            flash("Please enter a pasword and repeat it.", 'danger')
            return render_template(REGISTER_PAGE)
        # Ensure the password was repeated correctly
        elif request.form.get("password") != request.form.get("confirmPassword"):
            # Return yet another error message.
            flash("Please ensure that the passwords match.", 'danger')
            return render_template(REGISTER_PAGE)

        # Assign the values to variables
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if user is already saved in database
        dbCursor.execute("SELECT * FROM Users WHERE username = ?", [username])
        if len(dbCursor.fetchall()) != 0:
            # return error message, username exists already.
            flash("This username already exists.", 'danger')
            return render_template(REGISTER_PAGE)

        # Ensure password is conform to rules
        if not check_password_validity(password):
            # return errormessage, password not conform to rules
            flash("Your password does not meet our requirements.", 'danger')
            return render_template(REGISTER_PAGE)
        else:
            # Create a hash value of the password
            passwordHash = generate_password_hash(password)

        # Insert userdata into the db
        dbCursor.execute("""INSERT INTO Users (username, password_hash) 
        VALUES (?,?)""", (username, passwordHash))

        # Query the database again
        dbCursor.execute("SELECT * FROM users WHERE username = ?", [username])

        # Check out old user, if someone is still logged in.
        if "user_id" in session:
            session.clear()

        # Log user in
        session["user_id"] = dbCursor.fetchone()[0]
        # Tell the user that they are logged in.
        flash("You are now registered and logged in. :)", 'success')
        return redirect("/")
    
    
# Check the validity of the password
def check_password_validity(password):
    symbols = '!?-+'
    # Ensure the password is at least 8 characters long
    if (len(password) >= 8 and
        # Ensure the password contains atleast one uppercase letter
            any(c.isupper() for c in password) and
        # Ensure the password contains atleast one lowercase letter
            any(c.islower() for c in password) and
        # Ensure the password contains atleast one number
            any(c.isdigit() for c in password) and
        # Ensure the password contains atleast one symbol (?!-+)
            any(c in symbols for c in password) and
        # Ensure that all of the characters are either a symbol or alphanums
            all(c.isalnum() or c in symbols for c in password)):
        return True
    else:
        return False
    

@app.route("/login", methods=["GET", "POST"])
def login():
    LOGIN_PAGE = "login.html"

    if request.method == "GET":
        return render_template(LOGIN_PAGE)
    else:
        # Ensure user typed in a username
        if not request.form.get("username"):
            # Flash error message on top of site
            flash("Please enter your username.", 'danger')
            return render_template(LOGIN_PAGE)
        # Ensure user typed in a password
        elif not request.form.get("password"):
            # Return error message on top of site
            flash("Please enter your password.", 'danger')
            return render_template(LOGIN_PAGE)

        # Assign variables
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if user exists
        dbCursor.execute("SELECT * FROM Users WHERE username = ?", [username])
        if len(dbCursor.fetchall()) != 1:
            # Return error message, user does not exist yet.
            flash("You do not have an account here. Maybe register first?", 'danger')
            return render_template(LOGIN_PAGE)
        
        # Get password hash from database
        dbCursor.execute("SELECT password_hash FROM Users WHERE username = ?", [username])
        savedHash = dbCursor.fetchone()[0]

        # Compare password hash from db to typed in password by user
        if not check_password_hash(savedHash, password):
            # If not equal, let the user know and do not log them in
            flash("Wrong password. Try again pls, you got this ;).", 'danger')
            return render_template(LOGIN_PAGE)
          
        # Get user_id from database
        dbCursor.execute("SELECT user_id FROM Users WHERE username = ?", [username])
        userID = dbCursor.fetchone()[0]
    
        # Save user_id in session (log them in)
        session["user_id"] = userID
        flash("You are now logged in. Hello :)", 'success')
        return redirect("/")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    # If user reached this site via GET
    if request.method == "GET":
        # Show logout page
        return render_template("logout.html")
    # If user reached this site via POST
    else:
        # Clear the session (log the user out)
        session.clear()
        flash("You are now logged out. Goodbye :)", 'success')
        return redirect("/")
    

@app.route("/faq")
def faq():
    return render_template("faq.html")

# Commit the changes to the database.
connecc.commit()

# Close the db connection if not needed anymore
# connecc.close()


@app.route("/complain")
def complain():
    return render_template("test.html")

if __name__ == "__main__":
    app.run(debug=True)