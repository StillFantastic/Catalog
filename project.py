from flask import Flask, render_template, redirect, request, url_for
import psycopg2
import random
import string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import time


app = Flask(__name__)


restaurants_columns = ["id", "name", "description", "picture", "user_id"]
menus_columns = ["id", "name", "price", "description", "picture",
                 "restaurnt_id"]


def connectdb(dbname="catalog"):
    try:
        db = psycopg2.connect("dbname=" + dbname)
        return db
    except psycopg2.OperationalError, e:
        print("Error connecting database: %s" % (e))


def restaurant_name_exist(restaurant_name):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM restaurants WHERE name=(%s);", (restaurant_name,))
    restaurant = c.fetchone()
    db.close()
    if restaurant is None:
        return None
    else:
        return restaurant


def menu_id_exist(menu_id):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM menus WHERE id=(%s);", (menu_id,))
    menu = c.fetchone()
    db.close()
    if menu is None:
        return None
    else:
        return menu


def authorized(name, user_id):
    return name == user_id


@app.route("/restaurant/")
def showRestaurants():
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM restaurants ORDER BY id ASC;")
    restaurants = c.fetchall()
    db.close()
    return render_template("showRestaurants.html",
                           restaurants=restaurants,
                           inHome=True,
                           login_session=login_session)


@app.route("/restaurant/<restaurant_name>/")
def showMenus(restaurant_name):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM restaurants WHERE name=(%s);", (restaurant_name,))
    restaurant = c.fetchone()
    if restaurant is None:
        return redirect("/restaurant/")
    c.execute("SELECT * FROM menus WHERE restaurant_id=(%s);",
              (restaurant[0],))
    menus = c.fetchall()
    db.close()
    return render_template("showMenus.html",
                           restaurant=restaurant,
                           menus=menus,
                           inRestaurant=True,
                           login_session=login_session)


@app.route("/restaurant/<restaurant_name>/<int:menu_id>/")
def showSingleMenu(restaurant_name, menu_id):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM restaurants WHERE name=(%s);",
              (restaurant_name,))
    restaurant = c.fetchone()
    if restaurant is None:
        return redirect("/restaurant/")
    c.execute("SELECT * FROM menus WHERE id=(%s);", (menu_id,))
    menu = c.fetchone()
    db.close()
    return render_template("showSingleMenu.html",
                           restaurant=restaurant,
                           menu=menu,
                           inMenu=True,
                           login_session=login_session)


@app.route("/restaurant/new/", methods=["get", "post"])
def newRestaurant():
    if login_session.get("user_id") is None:
        return redirect(url_for("showRestaurants"))

    if request.method == "GET":
        return render_template("newRestaurant.html",
                               restaurant={},
                               login_session=login_session)
    elif request.method == "POST":
        restaurant = {}
        restaurant["name"] = request.form["name"]
        restaurant["picture"] = request.form["picture"]
        restaurant["description"] = request.form["description"].replace("\n",
                                                                        "<br>")
        if (not request.form["name"] or not request.form["picture"] or
           not request.form["description"]):
            error = "Please fill in all of the text box."
            return render_template("newRestaurant.html",
                                   restaurant=restaurant,
                                   error=error,
                                   login_session=login_session)
        db = connectdb()
        c = db.cursor()
        c.execute("""INSERT INTO restaurants (name, picture, description, user_id)
                  VALUES ((%s), (%s), (%s), (%s));""",
                  (restaurant["name"],
                   restaurant["picture"],
                   restaurant["description"],
                   login_session["user_id"]))
        db.commit()
        db.close()
        return redirect(url_for("showRestaurants"))


@app.route("/restaurant/<restaurant_name>/new", methods=["get", "post"])
def newMenu(restaurant_name):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM restaurants WHERE name=(%s)", (restaurant_name,))
    restaurant = c.fetchone()
    db.close()
    if restaurant is None:
        return redirect(url_for("showRestaurants"))
    if not authorized(restaurant[4], login_session.get("user_id")):
        return redirect(url_for("showRestaurants"))
    if request.method == "GET":
        return render_template("newMenu.html",
                               menu={},
                               login_session=login_session)
    elif request.method == "POST":
        menu = {}
        menu["name"] = request.form["name"]
        menu["price"] = request.form["price"]
        menu["picture"] = request.form["picture"]
        menu["restaurant_id"] = restaurant[0]
        menu["description"] = \
            request.form["description"].replace("\n", "<br>")
        if (not request.form["name"] or not request.form["price"] or
           not request.form["picture"] or not request.form["description"] or
           not request.form["price"].isdigit()):
            error = "Please fill in all of the text box."
            return render_template("newMenu.html",
                                   menu=menu,
                                   error=error,
                                   login_session=login_session)
        db = connectdb()
        c = db.cursor()
        c.execute("""INSERT INTO menus (name, price, picture, restaurant_id, description)
                  VALUES ((%s), (%s), (%s), (%s), (%s));""",
                  (menu["name"],
                   menu["price"],
                   menu["picture"],
                   menu["restaurant_id"],
                   menu["description"]))
        db.commit()
        db.close()
        return redirect(url_for("showMenus", restaurant_name=restaurant_name))


@app.route("/restaurant/<restaurant_name>/edit", methods=["get", "post"])
def editRestaurant(restaurant_name):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM restaurants WHERE name=(%s);", (restaurant_name,))
    restaurant = c.fetchone()
    if restaurant is None:
        return redirect(url_for("showRestaurants"))
    if not authorized(restaurant[4], login_session.get("user_id")):
        return redirect(url_for("showRestaurants"))
    db.close()
    sz = len(restaurant)
    restaurant_dict = {}
    for i in range(sz):
        restaurant_dict[restaurants_columns[i]] = restaurant[i]
    if request.method == "GET":
        return render_template("newRestaurant.html",
                               restaurant=restaurant_dict,
                               login_session=login_session)
    elif request.method == "POST":
        restaurant_dict["name"] = request.form["name"]
        restaurant_dict["picture"] = request.form["picture"]
        restaurant_dict["description"] = request.form["description"]
        if (not request.form["name"] or not request.form["picture"] or
           not request.form["description"]):
            error = "Please fill in all of the text boxes."
            return render_template("newRestaurant.html",
                                   restaurant=restaurant_dict,
                                   login_session=login_session)
        db = connectdb()
        c = db.cursor()
        c.execute("""UPDATE restaurants SET name=(%s), picture=(%s),
                  description=(%s) WHERE name=(%s)
                  """, (restaurant_dict["name"],
                        restaurant_dict["picture"],
                        restaurant_dict["description"],
                        restaurant_name))
        db.commit()
        db.close()
        return redirect(url_for("showRestaurants"))


@app.route("/restaurant/<restaurant_name>/delete", methods=["get", "post"])
def deleteRestaurant(restaurant_name):
    restaurant = restaurant_name_exist(restaurant_name)
    if not restaurant:
        return redirect(url_for("showRestaurants"))
    if not authorized(restaurant[4], login_session.get("user_id")):
        return redirect(url_for("showRestaurants"))
    if request.method == "GET":
        return render_template("deleteRestaurant.html",
                               restaurant_name=restaurant_name,
                               login_session=login_session)
    elif request.method == "POST":
        db = connectdb()
        c = db.cursor()
        c.execute("DELETE FROM menus WHERE restaurant_id=(%s);",
                  (restaurant[0],))
        c.execute("DELETE FROM restaurants WHERE name=(%s);",
                  (restaurant_name,))
        db.commit()
        return redirect(url_for("showRestaurants"))


@app.route("/restaurant/<restaurant_name>/<int:menu_id>/edit",
           methods=["get", "post"])
def editMenu(restaurant_name, menu_id):
    restaurant = restaurant_name_exist(restaurant_name)
    menu = menu_id_exist(menu_id)
    if restaurant is None or menu is None:
        return redirect(url_for("showMenus", restaurant_name=restaurant_name))
    if not authorized(restaurant[4], login_session.get("user_id")):
        return redirect(url_for("showMenus", restaurant_name=restaurant_name))
    menu_dict = {}
    for i in range(len(menus_columns)):
        menu_dict[menus_columns[i]] = menu[i]
    if request.method == "GET":
        return render_template("newMenu.html",
                               menu=menu_dict,
                               login_session=login_session)
    elif request.method == "POST":
        menu_dict["name"] = request.form["name"]
        menu_dict["price"] = request.form["price"]
        menu_dict["picture"] = request.form["picture"]
        menu_dict["description"] = \
            request.form["description"].replace("\n", "<br>")
        if (not request.form["name"] or not request.form["price"] or
           not request.form["picture"] or
           not request.form["description"] or
           not request.form["price"].isdigit()):
            error = "Please fill in all of the text box."
            return render_template("newMenu.html",
                                   menu=menu,
                                   error=error,
                                   login_session=login_session)
        db = connectdb()
        c = db.cursor()
        c.execute("""UPDATE menus SET name=(%s), price=(%s), picture=(%s),
                  description=(%s) WHERE id=(%s);""",
                  (menu_dict["name"],
                   menu_dict["price"],
                   menu_dict["picture"],
                   menu_dict["description"],
                   menu_dict["id"]))
        db.commit()
        db.close()
        return redirect(url_for("showSingleMenu",
                        restaurant_name=restaurant_name,
                        menu_id=menu_id))


@app.route("/restaurant/<restaurant_name>/<int:menu_id>/delete",
           methods=["post", "get"])
def deleteMenu(restaurant_name, menu_id):
    restaurant = restaurant_name_exist(restaurant_name)
    menu = menu_id_exist(menu_id)
    if restaurant is None or menu is None:
        return redirect(url_for("showSingleMenu",
                        restaurant_name=restaurant_name,
                        menu_id=menu_id))
    if not authorized(restaurant[4], login_session.get("user_id")):
        return redirect(url_for("showSingleMenu",
                        restaurant_name=restaurant_name,
                        menu_id=menu_id))
    if request.method == "GET":
        return render_template("deleteMenu.html",
                               restaurant_name=restaurant_name,
                               menu_id=menu_id,
                               login_session=login_session)
    elif request.method == "POST":
        db = connectdb()
        c = db.cursor()
        c.execute("DELETE FROM menus WHERE id=(%s);", (menu_id,))
        db.commit()
        db.close()
        return redirect(url_for("showSingleMenu",
                        restaurant_name=restaurant_name,
                        menu_id=menu_id))


@app.route("/login/")
def login():
    if login_session.get("user_id"):
        return redirect(url_for("showRestaurants"))
    state = "".join(random.choice(string.ascii_uppercase + string.digits)
                    for _ in range(32))
    login_session["state"] = state
    return render_template("login.html",
                           state=state,
                           login_session=login_session)


def getUserID(email):
    db = connectdb()
    c = db.cursor()
    c.execute("SELECT * FROM users where email=(%s);", (email,))
    user = c.fetchone()
    db.close()
    if user is None:
        return None
    return user[0]


def createUser(login_session):
    db = connectdb()
    c = db.cursor()
    c.execute("""INSERT INTO users (name, picture, email)
              VALUES ((%s), (%s), (%s));""", (login_session["username"],
              login_session["picture"],
              login_session["email"]))
    db.commit()
    c.execute("SELECT * FROM users WHERE email=(%s);",
              (login_session["email"],))
    user = c.fetchone()
    db.close()
    return user[0]


@app.route("/gconnect", methods=["post"])
def gconnect():
    client_id = json.loads(open("google_client_secrets.json", "r").read())
    client_id = client_id["web"]["client_id"]

    if request.args.get("state") != login_session["state"]:
        response = make_response(json.dumps("Invalid state parameter"), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets("google_client_secrets.json",
                                             scope="")
        oauth_flow.redirect_uri = "postmessage"
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
                json.dumps("Failed to upgrade the authorization code."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    access_token = credentials.access_token
    url = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s" \
          % access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, "GET")[1])
    if result.get("error") is not None:
        response = make_response(json.dumps(result.get("error")), 500)
        response.headers["Content-Type"] = "application/json"
        return response

    gplus_id = credentials.id_token["sub"]

    if result["user_id"] != gplus_id:
        response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."),
                401)
        response.headers["Content-Type"] = "application/json"
        return response

    if result["issued_to"] != client_id:
        response = make_response(
                json.dumps("Token's client id doesn't match your app's"), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    stored_access_token = login_session.get("access_token")
    stored_gplus_id = login_session.get("gplus_id")

    if stored_access_token is not None and stored_gplus_id == gplus_id:
        response = make_response(
                json.dumps("Current user is already connected."), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    login_session["provider"] = "google"
    login_session["access_token"] = credentials.access_token
    login_session["gplus_id"] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt": "json"}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]
    login_session["email"] = data["email"]

    user_id = getUserID(login_session["email"])
    if user_id is None:
        user_id = createUser(login_session)
    login_session["user_id"] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;-webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;"> '
    print "done!"
    return output


@app.route("/fbconnect", methods=["post"])
def fbconnect():
    if request.args.get("state") != login_session["state"]:
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    access_token = request.data
    app_id = json.loads(open("fb_client_secrets.json", "r").read())
    app_id = app_id["web"]["app_id"]
    app_secret = json.loads(open("fb_client_secrets.json", "r").read())
    app_secret = app_secret["web"]["app_secret"]
    url = ("https://graph.facebook.com/oauth/access_token?grant_type=fb_exc"
           "hange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s") \
        % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, "GET")[1]
    token = result.split(",")[0].split(":")[1].replace('"', "")
    url = """https://graph.facebook.com/v2.2/me?access_token=%s&fields=
name,id,email""" % token
    h = httplib2.Http()
    result = h.request(url, "GET")[1]
    data = json.loads(result)
    login_session["provider"] = "facebook"
    login_session["username"] = data["name"]
    login_session["email"] = data["email"]
    login_session["facebook_id"] = data["id"]
    login_session["access_token"] = token

    url = """https://graph.facebook.com/v2.8/me/picture?access_token=
%s&redirect=0&height=200&width=200""" % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    user_id = getUserID(login_session["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session["user_id"] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ " style = "width: 300px; height: 300px;border
-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">"""
    return output


@app.route("/logout/")
def logout():
    if login_session["provider"] == "google":
        access_token = login_session.get("access_token")
        if access_token is None:
            return redirect(url_for("showRestaurants"))
        url = "https://accounts.google.com/o/oauth2/revoke?token=%s" \
            % access_token
        h = httplib2.Http()
        result = h.request(url, "GET")[0]
        del login_session["access_token"]
        del login_session["gplus_id"]
        del login_session["username"]
        del login_session["email"]
        del login_session["picture"]
        del login_session["user_id"]
        return redirect(url_for("showRestaurants"))
    elif login_session["provider"] == "facebook":
        facebook_id = login_session["facebook_id"]
        access_token = login_session["access_token"]
        if access_token is None:
            return redirect(url_for("showRestaurants"))
        url = "https://graph.facebook.com/%s/permissions?access_token=%s" \
            % (facebook_id, access_token)
        h = httplib2.Http()
        h.request(url, "DELETE")
        del login_session["username"]
        del login_session["email"]
        del login_session["picture"]
        del login_session["access_token"]
        del login_session["facebook_id"]
        del login_session["user_id"]
        return redirect(url_for("showRestaurants"))


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.secret_key = "my_secret_key"
    app.run(host="0.0.0.0", port=5000)
