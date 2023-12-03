from flask import Flask, render_template, session, redirect, url_for, flash

from password_hashing import encrypt, decrypt
from Controller import dbController
from Model.User import User


# Function to log in the user
def login(request):
    if request.method == 'POST':
        # Admin Login Check
        if request.form['email'] == 'admin@buyadvisor.com' and request.form['password'] == 'test':
            session['email'] = 'test@admin.com'
            return redirect(url_for("adminDashboard"))
        else:
            # Query to see in the user is found in the User table
            passwordEncrypt = encrypt(request.form['password']).decode()
            newUser = User('', '', request.form['email'], passwordEncrypt)
            query = "SELECT * FROM User WHERE email = '" + newUser.getEmail() + "'"
            result = list(dbController.getRecords(query))
            # Check if the password matches what is found in the DB
            if len(result) != 0:
                result = result[0]
                pass1 = decrypt(passwordEncrypt)
                pass2 = decrypt(result[1])
                if pass1 == pass2:
                    session['name'] = result[2] + " " + result[3]
                    session['email'] = request.form['email']
                    session['firstName'] = result[2]
                    session['lastName'] = result[3]
                    return redirect(url_for("dashboard"))

                # Notify the user if they were entered the wrong password
                else:
                    message = "Invalid Password. Please Try Again"
                    flash(message, 'Error')
                    return redirect(request.url)

            # Notify the user if the email entered is not found in the User table
            else:
                message = "We cannot find an account with that email address. Please register into our services"
                flash(message, 'Error')
                return redirect(url_for("signIn"))
    else:
        return render_template("login.html")


# Function to direct the user to the registration page
def register():
    return render_template("register.html")


# Function to have the user log out and end the session
def logout():
    if session['email'] == 'admin@buyadvisor.com':
        session.pop('email', None)
    else:
        session.pop('name', None)
        session.pop('email', None)
        session.pop('firstName', None)
        session.pop('lastName', None)
    return redirect("/")
