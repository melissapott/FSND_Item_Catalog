# Import required libraries
from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask import make_response, send_file, flash
# we're already using the word session for db session
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
import random
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import json
import httplib2
import requests
import os
import sys
from werkzeug.utils import secure_filename
from flask import send_from_directory


app = Flask(__name__)

# image uploads
# image upload folder and allowable file extensions
UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'JPG', 'PNG', 'GIF'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def uploadFile(userfile):
    # avoid filename crashes - assign a random name and check if it exists
    if userfile:
        new_name = ''.join(random.choice(string.ascii_uppercase + string.
                                         digits)for x in xrange(8))

        userfile.filename = new_name + "." + \
            userfile.filename.rsplit('.', 1)[1]

        # check that the file name isn't already in use - if it is, assign a
        # new one
        while os.path.isfile('images/' + userfile.filename):
            new_name = ''.join(random.choice(string.ascii_uppercase + string.
                                             digits)for x in xrange(8))
            userfile.filename = new_name + "." + \
                userfile.filename.rsplit('.', 1)[1]

        # now that we have a good filename, do the upload
        file = userfile
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return userfile.filename
    else:
        return None

# for displaying an uploaded file


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# Set up a connection to the database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Show the main page
@app.route('/')
def home():
    categories = session.query(Category)
    return render_template('home.html', categories=categories,
                           user_status=userStatus())


# route and method for creating a new category
@app.route('/category/new', methods=['GET', 'POST'])
def addCategory():
    # only logged in users can add a category - so check login status first
    if 'user_id' not in login_session:
        flash('You must be logged in to add a new category')
        return redirect(url_for('showLogin'))

    # get the user-entered information from the form and add it to the
    # database
    if request.method == 'POST':
        filename = uploadFile(request.files['userfilename'])
        newCategory = Category(name=request.form['name'], description=request.
                               form['description'], icon=filename,
                               user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("New Category %s has been created!" % newCategory.name)
        return redirect(url_for('home'))
    else:
        return render_template('addcategory.html')


# route and method for listing all items by category
@app.route('/category/<int:category_id>')
def itemsByCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('category.html', category=category, items=items,
                           user_status=userStatus(category.user_id))


# route and method for editing an existing category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    # retrieve the category record from the database
    category = session.query(Category).filter_by(id=category_id).one()

    # check to make sure that the user is logged in and is the author of the
    # category before allowing an edit
    if 'user_id' not in login_session:
        flash('You must be logged in as author of this category to edit it.')
        return redirect(url_for('showLogin'))
    if login_session['user_id'] != category.user_id:
        flash('Only the author of the category may edit.')
        return redirect(url_for('itemsByCategory', category_id=category_id))

    # get the user entered information from the form and update the database
    # record
    if request.method == 'POST':
        filename = uploadFile(request.files['userfilename'])
        category.name = request.form['name']
        category.description = request.form['description']
        category.icon = filename
        session.add(category)
        session.commit()
        flash("Category %s has been edited!" % category.name)
        return redirect(url_for('itemsByCategory', category_id=category_id))
    else:
        return render_template('editcategory.html', category=category)


# route and method for deleting a category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    # retrieve the category record from the database
    category = session.query(Category).filter_by(id=category_id).one()

    # check to make sure that the user is logged in and is the author of the
    # category before allowing an edit
    if ('user_id' not in login_session or
            category.user_id != login_session['user_id']):
        flash('You must be logged in as author of this category to edit it.')
        return redirect(url_for('itemsByCategory', category_id=category_id))

    # delete the selected record from the database
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash("The category has been deleted.")
        return redirect(url_for('home'))
    else:
        return render_template('deletecategory.html', category=category)


# route and method for creating a new item
@app.route('/item/new/<int:category_id>', methods=['GET', 'POST'])
def addItem(category_id):
    # users must be logged in to create a new item
    if 'user_id' not in login_session:
        flash('You must be logged in to add a new item')
        return redirect(url_for('showLogin'))

    # get a list of categories from the database to populate radio buttons on
    # the form
    categories = session.query(Category)

    # get the user entered data from the form and save it in the database
    if request.method == 'POST':
        filename = uploadFile(request.files['userfilename'])
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       image=filename,
                       category_id=request.form['category'],
                       user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("Item %s has been created!" % newItem.name)
        return redirect(url_for('itemsByCategory',
                        category_id=newItem.category_id))
    else:
        return render_template('addItem.html', categories=categories,
                               category_id=category_id)


# route and method for displaying item detail
@app.route('/item/<int:item_id>/detail')
def itemDetail(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=item.category_id).one()
    return render_template('itemdetail.html', item=item, category=category,
                           user_status=userStatus(item.user_id))


# route and method for editing an existing item
@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    # get the item record to be edited from the database
    item = session.query(Item).filter_by(id=item_id).one()

    # check to make sure that the user is logged in and is the creator of the
    # item before allowing an edit
    if 'user_id' not in login_session:
        flash('You must be logged in as the creator to perform an edit')
        return redirect(url_for('showLogin'))
    if login_session['user_id'] != item.user_id:
        flash('Only the creator of the item may perform an edit.')
        return redirect(url_for('itemDetail', item_id=item_id))

    # get the edited information from the form and update the database record
    if request.method == 'POST':
        filename = uploadFile(request.files['userfilename'])
        item.name = request.form['name']
        item.description = request.form['description']
        item.price = request.form['price']
        item.image = filename
        item.category_id = request.form['category']
        session.add(item)
        session.commit()
        flash("Item %s has been edited." % item.name)
        return redirect(url_for('itemDetail', item_id=item.id))
    else:
        categories = session.query(Category)
        return render_template('editItem.html', item=item,
                               categories=categories)


# route and method for deleting an item
@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    # get the record to be deleted from the database
    item = session.query(Item).filter_by(id=item_id).one()

    # only the creator of the item will be allowed to delete - check to make
    # sure that the user is logged in as the original creator
    if 'user_id' not in login_session:
        flash('You must be logged in as the item creator to delete.')
        return redirect(url_for('showLogin'))
    if login_session['user_id'] != item.user_id:
        flash('Only the creator of an item may delete it.')
        return redirect(url_for('itemDetail', item_id=item_id))

    # delete the record from the database
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item has been deleted.")
        return redirect(url_for('itemsByCategory',
                                category_id=item.category_id))
    else:
        return render_template('deleteitem.html', item=item)


def userStatus(creator_id=None):
    # this function will be used by the template engine to show
    # or hide add, edit and delete links
    if 'user_id' not in login_session:
        return 'guest'
    if login_session['user_id'] != creator_id:
        return 'user'
    if login_session['user_id'] == creator_id:
        return 'creator'


# use JSONIFY to return JSON endpoints for categories, items by category,
# and item details

# creates a JSON endpoint containing a list of all categories
@app.route('/categories/json')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


# create a JSON endpoint containing a list of all items in a given category
@app.route('/category/<int:category_id>/json')
def itemsByCategoryJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id)
    return jsonify(items=[i.serialize for i in items])


# create a JSON endpoint for all items grouped by category
@app.route('/catalog/json')
def itemsAllJSON():
    catalog = []
    categories = session.query(Category).all()
    for c in categories:
        c_group = c.serialize
        items = session.query(Item).filter_by(category_id=c.id).all()
        item_list = []
        for i in items:
            item_list.append(i.serialize)
        c_group['items'] = item_list
        catalog.append(c_group)
    return jsonify(catalog=[catalog])


# create a JSON endpoint for a specific item
@app.route('/item/<int:item_id>/json')
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=[item.serialize])


# code for dealing with logging users in and out
# from Udacity Authorization and Authentication class

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    newUser = User(name=login_session[
                   'username'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(user_id=user_id).one()
    return user

# get the Google API client information
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog"


@app.route('/login')
def showLogin():
    # create a random string to be used as a CSRF token - we'll check it again
    # later and if it doesn't match, there may have been a hijack
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Google Login
@app.route('/gconnect', methods=['POST'])
def gConnect():
    # Validate state token - check for hijack
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code - obtained from javascript in login.html
    code = request.data

    try:
        # exchange the authorization code for a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except:
        response = make_response(json.dumps('authorization unsucessful'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token

    # check that the access token we got is valid
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps("result.get('error')"), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # is the access token issued for the intended user?
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        response = make_response(json.dumps(
            "Token ID doesn't match User"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # is the access token valid for this application?
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "token not valid for this app"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # is the user already logged in?
    stored_credentials = login_session.get('credentials')
    stored_g_id = login_session.get('g_id')
    if stored_credentials is not None and g_id == stored_g_id:
        response = make_response(json.dumps('user is already logged in'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # everything checks out, so save the credentials to the session
    login_session['credentials'] = credentials.access_token
    login_session['g_id'] = g_id

    # get the user info from the Google API
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    reply = requests.get(userinfo_url, params=params)
    data = reply.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # does the user already exist in the database?  If not, create a new user
    # entry
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    flash("You are now logged in as %s" % login_session['username'])
    return output


# Facebook Login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    # Exchange client token for long-lived server-side token

    app_id = json.loads(open('fb_client_secrets.json',
                             'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json',
                                 'r').read())['web']['app_secret']

    url = ('https://graph.facebook.com/oauth/access_token?'
           'grant_type=fb_exchange_token&client_id=%s&client_secret=%s'
           '&fb_exchange_token=%s' % (app_id, app_secret, access_token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # use token to get user infor from API
    userinfo_url = 'https://graph.facebook.com/v2.2/me'
    # strip expire tage from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.2/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'

    flash("You are now logged in as %s" % login_session['username'])
    return output
# Disconnect from either Facebook or Google


@app.route('/logout')
def logout():
    if login_session:
        if login_session['provider'] == 'google':
            response = gdisconnect()
        elif login_session['provider'] == 'facebook':
            response = fbdisconnect()
    else:
        response = "user is not logged in"
    flash(response)
    return redirect(url_for('home'))

# Facebook Disconnect


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    login_session.clear()
    return "you have been logged out"

# Google Disconnect


@app.route("/gdisconnect")
def gdisconnect():
    credentials = login_session.get('credentials')

    if credentials is None:
        response = make_response(json.dumps(
            'Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session
        login_session.clear()
        response = "Successfully Disconnected"
        return response
    else:
        # an error where the given token was invalid
        response = "Error logging out"
        return response


if __name__ == '__main__':
    app.secret_key = 'blahblahblah'
    app.debug = True
    app.run(host='0.0.0', port=8000)
