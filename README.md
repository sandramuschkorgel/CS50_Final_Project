# CS50 Final Project: space.one
Space.one is a website that allows users to easily compare, book, and cancel space cargo flights. The target customers are satellite providers, research institutes, and government agencies.

## Description
The web app is created in a Flask environment and makes use of SQLite for managing the database structure. It consists of several dynamically created HTML pages. A helpers.py file supports the application by requesting data from an API and creating an apology page in case something went wrong.

## Installation
Using the CS50 IDE
```bash
cd [path to app.py]
flask run
```
Using your local terminal
```bash
pip install Flask
pip install Flask-Session
pip install requests

cd [path to app.py on your PC]
export FLASK_APP=app.py
flask run
```

## A short video explaining space.one
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/8bdbM5GhkTY/0.jpg)](https://youtu.be/8bdbM5GhkTY)

## A note on sources
* API storing data on [SpaceX launches](https://docs.spacexdata.com/?version=latest#intro)
* Launch dates are derived from real world data. Prices are entirely made up.
* Picture from pixabay: [Milky Way](https://pixabay.com/photos/milky-way-starry-sky-night-sky-star-2695569/)
