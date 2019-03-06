#!/usr/bin/env python3

from flask import (Flask, request, jsonify, render_template,
                   redirect, session as login_session, make_response, flash)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from create_db import Base, Category, Item
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import random
import string
import httplib2
import json
import requests

# create flask app
app = Flask(__name__)

# make client id and application name
CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# create engine
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


# main route
@app.route('/')
def main():
    session = DBSession()
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return render_template('catalog.html',
                               categories=categories, username=False)
    else:
        return render_template('catalog.html',
                               categories=categories, username=True)


# main route json path
@app.route('/JSON')
def main_json():
    session = DBSession()
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


# create anti forgery token
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# login user
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Check that state tokens are the same
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Get the data from the request
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()

    # Decode response
    correct_response = h.request(url, 'GET')[1].decode('utf-8')
    result = json.loads(correct_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Make sure the access token is for the correct user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ style = 'width: 300px; height: 300px;border-radius: 150px;
                  -webkit-border-radius: 150px;-moz-border-radius: 150px;'> """

    return output


# logout user
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')

    # If user isn't connected then return Curent user not connected
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = ("https://accounts.google.com/o/oauth2/revoke?token=%s"
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    # if access token succesfully revoked remove current user
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# category route
@app.route('/<category>')
def category_view(category):
    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()
    items = session.query(Item).filter(
            Item.category_id == parent_category.id).all()
    if 'username' not in login_session:
        return render_template('category.html', category=parent_category,
                               items=items, username=False)
    else:
        return render_template('category.html', category=parent_category,
                               items=items, username=True)


# category json route
@app.route('/<category>/JSON')
def category_json(category):
    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()
    items = session.query(Item).filter(
            Item.category_id == parent_category.id).all()
    return jsonify(category=parent_category.serialize,
                   items=[i.serialize for i in items])


# add item route
@app.route('/<category>/add', methods=['GET', 'POST'])
def add_item(category):
    # check to see if they are logged in
    if 'username' not in login_session:
        return redirect('/login')

    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()

    if request.method == 'POST':
        item_name = request.form['itemName']
        item_description = request.form['itemDescription']

        # check to see if dollar sign is added in
        if '$' not in request.form['itemPrice']:
            item_price = '$' + request.form['itemPrice']
        else:
            item_price = request.form['itemPrice']

        item = Item(name=item_name, description=item_description,
                    price=item_price, category=parent_category,
                    creator=login_session['gplus_id'])
        session.add(item)
        session.commit()
        return redirect('/' + category)

    return render_template('add.html', category=parent_category)


# item_view route
@app.route('/<category>/items/<item>')
def item_view(category, item):
    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()
    full_item = session.query(Item).filter(Item.name == item).first()

    if 'username' not in login_session:
        return render_template('item.html', category=parent_category,
                               item=full_item, username=False)
    else:
        return render_template('item.html', category=parent_category,
                               item=full_item, username=True)


# route for deleting items
@app.route('/<category>/items/<item>/delete')
def delete_item(category, item):
    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()
    full_item = session.query(Item).filter(Item.name == item).first()

    if 'username' not in login_session:
        return redirect('/login')

    # check for permission via gplus_id
    if full_item.creator != login_session['gplus_id']:
        return redirect('/{}/items/{}'.format(category, item))

    session.delete(full_item)
    session.commit()
    return redirect('/{}'.format(category))


# route for json item
@app.route('/<category>/items/<item>/JSON')
def item_json(category, item):
    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()
    full_item = session.query(Item).filter(Item.name == item).first()
    return jsonify(item=full_item.serialize)


# edit item route
@app.route('/<category>/items/<item>/edit', methods=['GET', 'POST'])
def edit_item(category, item):
    # if user isn't logged in redirect them to login page
    if 'username' not in login_session:
        return redirect('/login')

    session = DBSession()
    parent_category = session.query(Category).filter(
                      Category.name == category).first()
    full_item = session.query(Item).filter(Item.name == item).first()

    # check for permission via gplus_id
    if full_item.creator != login_session['gplus_id']:
        return redirect('/{}/items/{}'.format(category, item))

    # Edit the item and redirect them back to item page
    if request.method == 'POST':
        full_item.name = request.form['itemName']
        full_item.description = request.form['itemDescription']

        # check to see if dollar sign exists or not
        if '$' not in request.form['itemPrice']:
            full_item.price = '$' + request.form['itemPrice']
        else:
            full_item.price = request.form['itemPrice']

        session.add(full_item)
        session.commit()
        return redirect('/' + category + '/items/' + full_item.name)

    return render_template('edit.html', category=parent_category,
                           item=full_item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(debug=True, host='0.0.0.0')
