import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required
import datetime


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}



# Configure application
app = Flask(__name__)

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show all mails"""
    user = session["user_id"]
    usernamedb = db.execute("SELECT * FROM users WHERE id = ?", user)
    username = usernamedb[0]["username"]
    emails = db.execute("SELECT * FROM emails WHERE recipient = ?", username)
    return render_template("mails.html", emails=emails)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    """Compose a mail"""
    if request.method == "GET":
        senderdb = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        sender = senderdb[0]["username"]
        return render_template("compose.html")

    else:
        senderdb = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        sender = senderdb[0]["username"]
        recipient = request.form.get("recipient")
        subject = request.form.get("subject")
        body = request.form.get("body")

        recieverdb = db.execute("SELECT * FROM users WHERE username = ?", recipient)
        try:
            reciever = recieverdb[0]["username"]
        except:
            return apology("Invalid recipient")

        now = datetime.datetime.now()
        date = now.strftime("%B %d, %Y")
        time = now.strftime("%I:%M %p")

        if 'file' not in request.files:
            db.execute("INSERT INTO emails (sender, recipient, subject, body, date, time) VALUES(?,?,?,?,?,?)", sender, recipient, subject, body, date, time)
            flash("Mail sent!")
            return redirect("/")

        file = request.files['file']

        if file.filename == '':
            db.execute("INSERT INTO emails (sender, recipient, subject, body, date, time) VALUES(?,?,?,?,?,?)", sender, recipient, subject, body, date, time)
            flash("Mail sent!")
            return redirect("/")

        if file and allowed_file(file.filename):
            data = file.read()
            filename = file.filename
            db.execute("INSERT INTO emails (sender, recipient, subject, body, date, time, filename, file) VALUES(?,?,?,?,?,?,?,?)", sender, recipient, subject, body, date, time, filename, data)
            flash("Mail sent!")
            return redirect("/")


@app.route("/sent")
@login_required
def sent():
    """Show sent mails"""
    user = session["user_id"]
    usernamedb = db.execute("SELECT * FROM users WHERE id = ?", user)
    username = usernamedb[0]["username"]
    emails = db.execute("SELECT * FROM emails WHERE sender = ?", username)
    return render_template("sent.html", emails=emails)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return apology("User dose not exist!", 403)

        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmpassword")

        if not username or not password or not confirm:
            return apology("Fill the empty fields")

        if password != confirm:
            return apology("Password does not match")

        mail = username
        valid = re.search(".@exmail.com", mail)

        if not valid:
            return apology("Please use exmail.com")
        else:
            hash = generate_password_hash(password)

            try:
                new_user = db.execute("INSERT INTO users (username, hash) VALUES(?,?)",username, hash)
            except:
                return apology("Username already exists")

            session["user_id"] = new_user
            return redirect("/")


@app.route("/view", methods=["POST"])
@login_required
def view():
    """To view the body"""
    if request.method == "POST":
        id = request.form.get("id")
        emaildb = db.execute("SELECT * FROM emails WHERE id = ?", id)
        email = emaildb[0]

        if email['filename'] == None:
            return render_template("view.html",email=email)
        else:
            return render_template("view2.html",email=email)


@app.route('/download/<file_name>')
def download_file(file_name):
    filedb = db.execute("SELECT file FROM emails WHERE filename = ?", file_name)
    blob_data = filedb[0]['file']

    with open('/workspaces/121373441/project/files/' + file_name, 'wb') as file:
        file.write(blob_data)

    return send_file('/workspaces/121373441/project/files/' + file_name, as_attachment=True)


@app.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():
    """To delete a mail"""
    if request.method == "POST":
        id = request.form.get("id")
        db.execute("UPDATE emails SET favorite = 'yes' WHERE id = ?", id)
        flash("Marked!")
        return redirect("/")
    else:
        id = session["user_id"]
        usernamedb = db.execute("SELECT username FROM users WHERE id = ?", id)
        username = usernamedb[0]["username"]
        emailsdb = db.execute("SELECT * FROM emails WHERE recipient = ? AND favorite = ?", username, "yes")
        return render_template("favorites.html", emails=emailsdb)


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """To delete a mail"""
    if request.method == "POST":
        id = request.form.get("id")
        db.execute("DELETE FROM emails WHERE id = ?", id)
        flash("Mail deleted!")
        return redirect("/")


@app.route("/remove", methods=["POST"])
@login_required
def remove():
    """To remove mail from important"""
    if request.method == "POST":
        id = request.form.get("id")
        db.execute("UPDATE emails SET favorite = 'no' WHERE id = ?", id)
        return redirect("/favorites")


if __name__ == "__main__":
    app.run(debug=false,host='0.0.0.0')