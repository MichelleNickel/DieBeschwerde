from flask import Flask, render_template, redirect, flash, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3


app = Flask(__name__)

# Ensure the session is not permanent and expires at some point.
app.config["SESSION_PERMANENT"] = False
# Use a Filesystem and store data in the hard drive in a /flask_session folder. An alternative to using a database.
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize database
#db = "beschwerde.db"
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
        return render_template("home.html")
    else:
        return redirect("/about")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register(): 
    if request.method == "GET":
        return render_template("register.html")
    
    elif request.method == "POST":
        # Ensure user typed in a username
        if not request.form.get("username"):
            #flash error message on top of site
            flash("Please enter a username.", 'danger')
            return render_template("register.html")
        # Ensure user typed in a password and repeated it
        elif not request.form.get("password") or not request.form.get("confirmPassword"):
            #return error message on top of site
            flash("Please enter a pasword and repeat it.", 'danger')
            return render_template("register.html")
        # Ensure the password was repeated correctly
        elif not request.form.get("password") == request.form.get("confirmPassword"):
            #return yet another error message.
            flash("Please ensure that the passwords match.", 'danger')
            return render_template("register.html")

        # Assign the values to variables
        username = request.form.get("username")
        password = request.form.get("password")

        dbCursor.execute("SELECT * FROM Users WHERE username = ?", [username])
        if len(dbCursor.fetchall()) != 0:
            # return error message, username exists already.
            flash("This username already exists.", 'danger')
            return render_template("register.html")

        if not check_password_validity(password):
            # return errormessage, password not conform to rules
            flash("Your password does not meet our requirements.", 'danger')
            return render_template("register.html")
        else:
            passwordHash = generate_password_hash(password)

        print(username)
        print(password)
        print(passwordHash)
        dbCursor.execute("""INSERT INTO Users (username, password_hash) 
        VALUES (?,?)""", (username, passwordHash))

        # Query the database again
        dbCursor.execute("SELECT * FROM users WHERE username = ?", [username])

        # Check if a user is already logged in and clear session if yes, 
        # So the old user is logged out.
        if "user_id" in session:
            session.clear()

        # Log user in
        #session["user_id"] = dbCursor.fetchall()[0]["id"]
        session["user_id"] = dbCursor.fetchone()[0]
        print(session["user_id"])
        # display "you are registered!"
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
    

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "GET":
        return render_template("logout.html")
    else:
        session.clear()
        return render_template("logout.html")
    

@app.route("/faq")
def faq():
    return render_template("faq.html")


# Close the db connection if not needed anymore
# connecc.close()

if __name__ == "__main__":
    app.run()