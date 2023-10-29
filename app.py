from flask import Flask, render_template
import mainController as main

app = Flask(__name__)
controller_main = main.mainController()


@app.route('/')
def index():
    return render_template("homepage.html")

@app.route("/login")
def login():
    return controller_main.login()

@app.route("/register")
def register():
    return controller_main.register()


if __name__ == '__main__':
    app.run(static_url_path='',
            static_folder='BuyAdvisor/static',
            template_folder='BuyAdvisor/templates')
