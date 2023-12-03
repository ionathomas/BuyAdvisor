from flask import redirect, url_for, flash, render_template, session

from Controller import dbController
from Model.User import User
from password_hashing import encrypt


# Function to register a user to the Service
def register(firstName, lastName, email, password):
    newUser = User(firstName, lastName, email, password.decode())
    # Query to insert the new user details into the table
    query = "INSERT INTO User(firstName, lastName, email, password) values ('"
    query += newUser.getFirstName() + "', '" + newUser.getLastName() + "', '" + newUser.getEmail() + "', '" + password.decode() + "')"
    result = dbController.addRecord(query)
    # Notify the user if they were registered successfully
    if result:
        message = "Successfully registered. Please log in to use our services."
        flash(message, 'Success')
        return redirect(url_for("register"))

    # Check if the user email already registered to our services
    else:
        query = "SELECT * FROM User WHERE email = '" + newUser.getEmail() + "'"
        result = list(dbController.getRecords(query))
        if len(result) != 0:
            message = "This email login already exists. Please register using a different email address"

        # Notify the user if there was an error while registering
        else:
            message = "Error while registering the account. Please try again"
        flash(message, 'Error')
        return redirect(url_for("register"))


# Function to edit the user information, Can edit all fields except email
def editProfile(request):
    # Query to the DB to display the existing information of the user
    query = "SELECT * FROM User WHERE email = '" + session['email'] + "'"
    result = list(dbController.getRecords(query))
    editUser = User(result[0][2], result[0][3], result[0][0], result[0][1])

    # Update the user details
    if request.method == 'POST':
        editUser.setLastName(request.form['lastName'])
        editUser.setFirstName(request.form['firstName'])
        passwordEncrypt = encrypt(request.form['password']).decode()

        # Query to update the user information
        query = "UPDATE User SET FirstName='" + editUser.getFirstName() + "', LastName='" + editUser.getLastName() + "'"
        if request.form['password'] != '':
            editUser.setPassword(passwordEncrypt)
            query += ", Password = '" + passwordEncrypt + "' "
        query += "WHERE Email = '" + editUser.getEmail() + "'"
        session['name'] = editUser.getFirstName()+" "+editUser.getLastName()
        session['firstName'] = editUser.getFirstName()
        session['lastName'] = editUser.getLastName()
        result = dbController.editRecord(query)

        # Notify the user if they successfully edited the profile
        if result:
            message = "Profile successfully updated"
            flash(message, 'Success')

        # Notify the user if there was an issue while updating the profile information
        else:
            message = "Error while updating the profile. Please try again later."
            flash(message, 'Error')
    return redirect(url_for("editProfile"))


# Function to display the search history of the user
def searchHistory():
    # Query to retrieve the logs of the products they have searched
    query = "SELECT DISTINCT ASIN FROM productsearchlogs WHERE email = '" + session['email'] + "' order by dateSearched DESC;"
    result = list(dbController.getRecords(query))
    print(result)
    if len(result) > 0:
        for asin in result:
            # Query to retrieve the product information and send to the html page for the user to view
            query = "SELECT * FROM analyseproductscores WHERE ASIN = '" + asin[0] + "'"
            result2 = dbController.getRecords(query)
            if result2:
                scoreValue = result2[0][3]
                scorePercentage = result2[0][4]
                description = result2[0][6]
                message = '<tr><td>'+asin[0]+'</td>'
                message += '<td><a onclick="displayModal(\'' + description + '\')"><i class="fa fa-edit" style="font-size:36px"></i></a></td>'
                if 'NEUTRAL' in scoreValue:
                    message += '<td>The analysis was found to be non-conclusive. <br> Let your instincts take the wheel on this one! </td>'
                else:
                    message += '<td>The product was found to be '+str(scorePercentage)+'% '+scoreValue+'</td>'
                message += '<td><a onclick="displayModal(\'https://www.amazon.com/dp/'+asin[0]+'\')"><i class="fa fa-link" style="font-size:36px"></i></a></td>'
                message += '</tr>'
                flash(message, "Info")
    # Notify the user if they have not searched anything before
    else:
        # No Search Results
        print("No Recent Searches")
        message = "No Recent Searches"
        flash(message, "Error")
    return redirect(url_for("searchHistory"))
