from flask import redirect, url_for, flash, render_template, session

from Controller import dbController
from Model.User import User
from password_hashing import encrypt


def register(firstName, lastName, email, password):
    newUser = User(firstName, lastName, email, password.decode())
    query = "INSERT INTO User(firstName, lastName, email, password) values ('"
    query += newUser.getFirstName() + "', '" + newUser.getLastName() + "', '" + newUser.getEmail() + "', '" + password.decode() + "')"
    result = dbController.addRecord(query)
    if result:
        message = "Successfully registered. Please log in to use our services."
        flash(message, 'Success')
        return redirect(url_for("register"))
    else:
        query = "SELECT * FROM User WHERE email = '" + newUser.getEmail() + "'"
        result = list(dbController.getRecords(query))
        if len(result) != 0:
            message = "This email login already exists. Please register using a different email address"
        else:
            message = "Error while registering the account. Please try again"
        flash(message, 'Error')
        return redirect(url_for("register"))


def editProfile(request):
    query = "SELECT * FROM User WHERE email = '" + session['email'] + "'"
    result = list(dbController.getRecords(query))
    editUser = User(result[0][2], result[0][3], result[0][0], result[0][1])
    if request.method == 'POST':
        editUser.setLastName(request.form['lastName'])
        editUser.setFirstName(request.form['firstName'])
        passwordEncrypt = encrypt(request.form['password']).decode()
        query = "UPDATE User SET FirstName='" + editUser.getFirstName() + "', LastName='" + editUser.getLastName() + "'"
        if request.form['password'] != '':
            editUser.setPassword(passwordEncrypt)
            query += ", Password = '" + passwordEncrypt + "' "
        query += "WHERE Email = '" + editUser.getEmail() + "'"
        session['name'] = editUser.getFirstName()+" "+editUser.getLastName()
        session['firstName'] = editUser.getFirstName()
        session['lastName'] = editUser.getLastName()
        result = dbController.editRecord(query)
        if result:
            message = "Profile successfully updated"
            flash(message, 'Success')
        else:
            message = "Error while updating the profile. Please try again later."
            flash(message, 'Error')
    return redirect(url_for("editProfile"))

