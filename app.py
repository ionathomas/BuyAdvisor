import pymysql
from flask import Flask, render_template, request, redirect, url_for
from flask_session import Session
from Controller import mainController, userController, dbController, reviewProductController, adminController
from password_hashing import encrypt

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'buyadvisordb.ctyxfzfytuey.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'buyadvisor'
app.config['MYSQL_DB'] = 'buyadvisor'
app.config['PORT'] = 3306
app.config['autocommit'] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'wZOCYEMqiZDj69v06Pl1KFOYF1gPxENY'

# Configure session management
Session(app)

# Configure DB connection
db = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB'],
    port=app.config['PORT'],
    autocommit=app.config['autocommit']
)
dbController.openDbConnection(db)


@app.route("/")
def index():
    dbController.openDbConnection(db)
    return render_template("homepage.html")


@app.route("/signIn", methods=['GET', 'POST'])
def signIn():
    return mainController.login(request)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        passwordEncrypt = encrypt(request.form['password'])
        return userController.register(request.form['firstName'], request.form['lastName'], request.form['email'],
                                       passwordEncrypt)
    return mainController.register()


@app.route("/signOut")
def signOut():
    mainController.logout()
    return redirect("/")


#User Functions
@app.route("/dashboard")
def dashboard():
    return reviewProduct()


@app.route("/editProfile", methods=['GET', 'POST'])
def editProfile():
    userController.editProfile(request)
    return render_template("editProfile.html")


@app.route("/searchHistory", methods=['GET', 'POST'])
def searchHistory():
    userController.searchHistory()
    return render_template("searchHistory.html")


@app.route("/reviewProduct", methods=['GET', 'POST'])
def reviewProduct():
    url = request.values.get('url')
    if url:
        print(url)
        reviewProductController.reviewProduct(url)
    return render_template("reviewProduct.html")


#Admin Functions
@app.route("/adminDashboard")
def adminDashboard():
    return viewUsers();


@app.route("/viewUsers")
def viewUsers():
    adminController.viewUsers()
    return render_template("viewUsers.html")


@app.route("/deleteUser", methods=['POST'])
def deleteUser():
    if request.method == 'POST':
        adminController.deleteUser(request.form['email'])
    return redirect(url_for("viewUsers"))


@app.route("/editEmail", methods=['GET', 'POST'])
def editEmail():
    if request.method == 'GET':
        adminController.editUserEmail(request.args.get('email'))
    elif request.method == 'POST':
        adminController.updateEmail(request)
    return render_template("editEmail.html")


@app.route("/userSearchHistory", methods=['POST'])
def userSearchHistory():
    if request.method == 'POST':
        adminController.searchHistory(request.form['email'])
    return render_template("userSearchHistory.html")


@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response


if __name__ == '__main__':
    dbController.openDbConnection(db)
    app.run()
