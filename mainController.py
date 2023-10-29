from flask import Flask, render_template

class mainController:
    def login(self):
        return render_template("login.html")

    def register(self):
        return render_template("register.html")