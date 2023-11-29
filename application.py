import pymysql
from flask import Flask, render_template, request, redirect, url_for
from flask_session import Session
from Controller import mainController, userController, dbController, reviewProductController, adminController
from password_hashing import encrypt

application = Flask(__name__)
application.config['MYSQL_HOST'] = 'buyadvisordb.ctyxfzfytuey.us-east-1.rds.amazonaws.com'
application.config['MYSQL_USER'] = 'admin'
application.config['MYSQL_PASSWORD'] = 'buyadvisor'
application.config['MYSQL_DB'] = 'buyadvisor'
application.config['PORT'] = 3306
application.config['autocommit'] = True
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
application.config['SECRET_KEY'] = 'wZOCYEMqiZDj69v06Pl1KFOYF1gPxENY'

# Configure session management
Session(application)

# Configure DB connection
db = pymysql.connect(
    host=application.config['MYSQL_HOST'],
    user=application.config['MYSQL_USER'],
    password=application.config['MYSQL_PASSWORD'],
    db=application.config['MYSQL_DB'],
    port=application.config['PORT'],
    autocommit=application.config['autocommit']
)
dbController.openDbConnection(db)


@application.route("/")
def index():
    dbController.openDbConnection(db)
    return render_template("homepage.html")


@application.route("/signIn", methods=['GET', 'POST'])
def signIn():
    return mainController.login(request)


@application.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        passwordEncrypt = encrypt(request.form['password'])
        return userController.register(request.form['firstName'], request.form['lastName'], request.form['email'],
                                       passwordEncrypt)
    return mainController.register()


@application.route("/signOut")
def signOut():
    mainController.logout()
    return redirect("/")


#User Functions
@application.route("/dashboard")
def dashboard():
    return reviewProduct()


@application.route("/editProfile", methods=['GET', 'POST'])
def editProfile():
    userController.editProfile(request)
    return render_template("editProfile.html")


@application.route("/searchHistory", methods=['GET', 'POST'])
def searchHistory():
    userController.searchHistory()
    return render_template("searchHistory.html")


@application.route("/reviewProduct", methods=['GET', 'POST'])
def reviewProduct():
    url = request.values.get('url')
    if url:
        print(url)
        reviewProductController.reviewProduct(url)
    return render_template("reviewProduct.html")


#Admin Functions
@application.route("/adminDashboard")
def adminDashboard():
    return viewUsers();


@application.route("/viewUsers")
def viewUsers():
    adminController.viewUsers()
    return render_template("viewUsers.html")


@application.route("/deleteUser", methods=['POST'])
def deleteUser():
    if request.method == 'POST':
        adminController.deleteUser(request.form['email'])
    return redirect(url_for("viewUsers"))


@application.route("/editEmail", methods=['GET', 'POST'])
def editEmail():
    if request.method == 'GET':
        adminController.editUserEmail(request.args.get('email'))
    elif request.method == 'POST':
        adminController.updateEmail(request)
    return render_template("editEmail.html")


@application.route("/userSearchHistory", methods=['POST'])
def userSearchHistory():
    if request.method == 'POST':
        adminController.searchHistory(request.form['email'])
    return render_template("userSearchHistory.html")


@application.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response


if __name__ == '__main__':
    dbController.openDbConnection(db)
    application.run()
