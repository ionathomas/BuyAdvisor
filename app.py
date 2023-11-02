import pymysql
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from Controller import mainController, userController, dbController
from password_hashing import encrypt, decrypt

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'BuyAdvisor'
app.config['autocommit'] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'super secret key'

# Configure session management
Session(app)

# Configure DB connection
db = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB'],
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


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/signOut")
def signOut():
    mainController.logout()
    return redirect("/")


@app.route("/editProfile", methods=['GET', 'POST'])
def editProfile():
    userController.editProfile(request)
    return render_template("editProfile.html")


@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response


if __name__ == '__main__':
    dbController.openDbConnection(db)
    app.run(static_url_path='/',
            static_folder='BuyAdvisor/static',
            template_folder='BuyAdvisor/templates',
            debug=True)
