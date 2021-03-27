import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, spacexlaunches, calculate_prices

import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///spacecargo.db")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure company name was submitted
        if not request.form.get("customer_name"):
            return apology("must provide company name", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for customer
        rows = db.execute("SELECT * FROM customers WHERE customer_name = :name",
                          name=request.form.get("customer_name"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/")
@login_required
def index():
    """User intro page"""

    return render_template("index.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure the registrant submitted a username
        if not request.form.get("customer_name"):
            return apology("must provide company name", 403)

        # Ensure the registrant submitted a password
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure the confirmation fits the password
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation differ", 403)

        # Query database for username to ensure that the username does not already exist in the database
        rows = db.execute("SELECT * FROM customers WHERE customer_name = :name",
                          name=request.form.get("customer_name"))
        if len(rows) > 0:
            return apology("company already registered", 403)

        # Register company by adding them to the spacecargo.db database
        db.execute("INSERT INTO customers (customer_name, hash) VALUES (:name, :password)",
                   name=request.form.get("customer_name"), password=generate_password_hash(request.form.get("password")))

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link)
    else:
        return render_template("register.html")


@app.route("/launches", methods=["GET", "POST"])
@login_required
def launches():
    """Show upcoming launches"""

    years = db.execute("SELECT DISTINCT(launch_year) FROM launches ORDER BY launch_year ASC")
    destinations = db.execute("SELECT DISTINCT(destination) FROM launches")

    if request.method == "POST":
        try:
            selected_year = int(request.form.get("year")) # In db launch_year is an integer, user input is always a string!
        except:
            selected_year = None

        if not request.form.get("year") and not request.form.get("destination"):
            launches = db.execute("SELECT * FROM launches ORDER BY launch_date")
        elif not request.form.get("year"):
            launches = db.execute("SELECT * FROM launches WHERE destination = :destination ORDER BY launch_date",
                                  destination=request.form.get("destination"))
        elif not request.form.get("destination"):
            launches = db.execute("SELECT * FROM launches WHERE launch_year = :year ORDER BY launch_date",
                                  year=request.form.get("year"))
        else:
            launches = db.execute("SELECT * FROM launches WHERE launch_year = :year AND destination = :destination ORDER BY launch_date",
                                  year=request.form.get("year"), destination=request.form.get("destination"))

        # Update any old launch dates so they cannot be booked anymore (not flawless)
        for launch in launches:
            if (launch["launch_date"]) < str(datetime.date.today()):
                db.execute("UPDATE launches SET bookable = :not_available WHERE id = :id",
                           not_available="False", id=launch["id"])

        return render_template("launches.html", launches=launches, years=years, destinations=destinations, selected_year=selected_year)

    else:
        launches = db.execute("SELECT * FROM launches ORDER BY launch_date")
        return render_template("launches.html", launches=launches, years=years, destinations=destinations)


@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    """Book a space cargo slot"""

    years = db.execute("SELECT DISTINCT(launch_year) FROM launches ORDER BY launch_year ASC")
    destinations = db.execute("SELECT DISTINCT(destination) FROM launches")
    select_type = ['Satellite', 'Experiment', 'Telescope', 'Rover']

    year = request.form.get("year")
    destination = request.form.get("destination")
    payload_weight = request.form.get("payload_weight")
    payload_type = request.form.get("payload_type")

    if request.method == "POST":
        selected_year = int(year) # In db launch_year is an integer, user input is always a string!

        available_launches = db.execute("SELECT id, launch_company, launch_date, spaceport, av_payload, bookable FROM launches WHERE launch_year = :year AND destination = :destination ORDER BY launch_date",
                              year=year, destination=destination)

        explanation = ""
        for launch in available_launches:
            if (launch["av_payload"] - int(payload_weight)) < 0:
                launch["bookable"] = "False"
                explanation = "Not enough available payload"
            if (launch["launch_date"]) < str(datetime.date.today()):
                explanation = "Launch date has already passed"

        price_comparison = calculate_prices(db, destination, payload_weight, payload_type)

        return render_template("book.html", years=years, destinations=destinations, select_type=select_type, selected_year=selected_year,
                               price_comparison=price_comparison, available_launches=available_launches, explanation=explanation)

    else:
        return render_template("book.html", years=years, destinations=destinations, select_type=select_type)


@app.route("/bookings", methods=["GET", "POST"])
@login_required
def bookings():
    """View customer bookings"""

    if request.method == "POST":
        launch = db.execute("SELECT launch_company, launch_date, spaceport, destination, av_payload FROM launches WHERE id = :id",
                            id=request.form.get("mission_id"))

        av_payload_new = launch[0]["av_payload"] - int(request.form.get("payload_weight"))
        db.execute("UPDATE launches SET av_payload = :payload_weight WHERE id = :id",
                   payload_weight=av_payload_new, id=request.form.get("mission_id"))

        price_comparison = calculate_prices(db, launch[0]["destination"], request.form.get("payload_weight"), request.form.get("payload_type"))

        db.execute("INSERT INTO bookings (customer_id, launch_date, spaceport, destination, payload_weight, payload_type, price, booking_date, mission_id) VALUES (:id, :date, :port, :dest, :weight, :p_type, :price, CURRENT_TIMESTAMP, :mission_id)",
                   id=session["user_id"], date=launch[0]["launch_date"], port=launch[0]["spaceport"], dest=launch[0]["destination"],
                   weight=request.form.get("payload_weight"), p_type=request.form.get("payload_type"), price=price_comparison[launch[0]["launch_company"]], mission_id=request.form.get("mission_id"))

        if av_payload_new == 0:
            db.execute("UPDATE launches SET bookable = :not_available WHERE id = :id",
                       not_available="False", id=request.form.get("mission_id"))

        return redirect("/bookings")

    else:
        bookings = db.execute("SELECT * FROM bookings WHERE customer_id = :customer_id ORDER BY launch_date",
                              customer_id=session["user_id"])
        return render_template("bookings.html", bookings=bookings)


@app.route("/cancel", methods=["GET", "POST"])
@login_required
def cancel():
    """Cancel a single booking"""

    if request.method == "POST":
        booking_id = request.form.get("booking_id")
        launch_data = db.execute("SELECT mission_id, payload_weight FROM bookings WHERE booking_id = :booking_id",
                                 booking_id=booking_id)
        mission_id = launch_data[0]["mission_id"]
        payload_weight = launch_data[0]["payload_weight"]

        # Update available payload weight in table launches, set availability back to True
        launch = db.execute("SELECT av_payload FROM launches WHERE id = :id",
                            id=mission_id)
        av_payload_new = launch[0]["av_payload"] + payload_weight

        db.execute("UPDATE launches SET av_payload = :av_payload_new WHERE id = :id",
                   av_payload_new=av_payload_new, id=mission_id)
        db.execute("UPDATE launches SET bookable = :available WHERE id = :id",
                   available="True", id=mission_id)

        # Delete booking from table bookings
        db.execute("DELETE FROM bookings WHERE booking_id = :booking_id",
                   booking_id=booking_id)
        return render_template("cancel.html")

    else:
        return render_template("cancel.html")


@app.route("/realdata")
def realdata():
    spacex_launches = spacexlaunches()

    return render_template("realdata.html", spacex_launches=spacex_launches)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
