# Catalog App
## Project Description

### Requirements

To start the program you will require a few files listed below.
Vagrant: [Vagrant](https://www.vagrantup.com/)
VirtualBox: [VirtualBox](https://www.virtualbox.org/wikiDownload_Old_Builds_5_1)
Flask: [Flask](http://flask.pocoo.org/docs/1.0/installation/)
Oauth2client: [Oauth2client](https://oauth2client.readthedocs.io/en/latest/)


### Start Up

To start the project you must first cd into the directory containing
your virtual machine. From there run vagrant up and wait for the files
to install. Once the files are finished run vagrant ssh and you will be
inside your virtual machine now. Cd into the /vagrant directory and then
cd into the project directory. Next run `python3 create_db.py` and wait for
it to create the database. Afterwards run `python3 application.py` and navigate
to http://localhost:5000. (Note it will run on whatever port you have set to
port 5000 in your vagrant machine.)

### Code Output

The Catalog App runs a sports catalog website with 4 categories. You have
baseball, basketball, soccer, and football. You can access each category by
clicking on their links in the main page. Each category displays a list with
one item by default. You can add items to a category by clicking on the
add item link. You can also view each item in a list individually by clicking
on their link and choose to edit or delete that item. Before you can change
the catalog you will be required to sign in with your google account by
clicking on the login link. You can also view the json endpoints of each list
by adding /JSON onto the end.

### Resources Used

Thanks to the CRUD restaurant project for help with login and logout code.
Some code is reused from that project.

### Special Thanks

Thanks to all Udacity teachers, mentors, and the classroom for their help.
