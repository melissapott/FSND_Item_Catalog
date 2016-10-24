# Item Catalog
This program was produced as a project submission for Udacity's FSND Item Catalog Project.

It will display a website for an item catalog which will allow users to log in and out, add, edit or delete items and categories of items as appropriate based on their login status, and provides JSON endpoints for lists of items and categories that have been stored in the database.

##Requirements:
- a computer running a virtual webserver such as Virtualbox/Vagrant, Sqlite, and Python
- The following files and folders included in this repository:
  - **database_setup.py** - this file creates the database tables used to store the tables used by the catalog: Category, Item, and User
  - **catalog.py** - this file contains python fuctions that render the various web pages used to display the item catalog, allow users to log in and out, and to create, read, update and delete items from the catalog.
  - **templates folder** - this folder contains the HTML template files which define the web pages:
  	- **addcategory.html**
  	- **additem.html**
  	- **category.html**
  	- **deletecategory.html**
  	- **deleteitem.html**
  	- **editcategory.html**
  	- **header.html**
  	- **home.html**
  	- **itemdetail.html**
  	- **login.html**
  	- **main.html**
  - **static folder** - this folder contains the following items used to display the site banner and stylesheet:
  	- **banner.png**
  	- **styles.css**
  - **images folder** - this folder will contain images uploaded by the users as category icons and product images.
  - **client_secrets.json** - this file contains the client secret key used for the Google login function
  - **fb_clien_secrets.json** - this file contains the client secret key used for the Facebook login function

##Included, but not required:
- **catalog.db** is a database that is included with some sample entries, as well as some sample pictures in the /images folder.  These are not necesaary, and if not used, a blank database will be created.

##Usage:
1.  Copy or clone the repository to the local machine.
2.  Start the virtual webserver and log in to it.
3.  Navigate to the directory containing the repository.
4.  Enter "python catalog.py" in the server terminal window.
5.  Open a web browser and enter http://localhost:8000 in the URL box.# FSND_Item_Catalog
