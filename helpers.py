import os
import requests
import urllib.parse

import locale

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def spacexlaunches():
    url = "https://api.spacexdata.com/v3/launches/upcoming?filter=flight_number,mission_name,launch_year,launch_date_utc,launch_site/site_name_long"

    headers = {}

    # No need for two steps, just helps identify errors if they occur
    # Contact API
    try:
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(e)
        return None

    # Parse input
    try:
        data = response.json()
        # Import method
        # Advanced: Instead of calling the API everytime the user loads the page, I could import the information required and update the db regularly
        return data

    except (KeyError, TypeError, ValueError) as e:
        print(e)
        # Debugging advice: print error message and stack trace
        return None


def calculate_prices(db, destination, payload_weight, payload_type):
    cost = db.execute("SELECT * FROM pricing;")
    prices = {}

    for item in cost:
        company = item["launch_company"]
        for key in item:
            if key == destination:
                weight_cost = int(payload_weight) * item[key]
                item["total"] += weight_cost
            if key == payload_type:
                item["total"] += item[key]
            else:
                continue
        # Integration of commas as thousands separators, returns strings not integers
        prices[company] = f'{item["total"]:,}'

    return prices