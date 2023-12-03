from flask import redirect, url_for, flash, render_template, session

from Controller import dbController
from Model.User import User

# Function to view all the users registered to the service
def viewUsers():
    # Querying the DB to get the user information
    query = "SELECT firstName, lastName, email FROM User"
    result = list(dbController.getRecords(query))
    print(result)
    # Sending the result to HTML
    if len(result) > 0:
        for user in result:
            message = '<tr><td>'+user[0]+' '+user[1]+'</td>'
            message += '<td>'+user[2]+'</td>'
            message += '<td><a onclick="editEmail(\''+user[2]+'\')"><i class="fa fa-edit" style="font-size:24px"></i></a></td>'
            message += '<td><a onclick="deleteUser(\''+user[2]+'\')"><i class="fa fa-trash" style="font-size:24px"></i></a></td>'
            message += '<td><a onclick="userSearchHistory(\''+user[2]+'\')"><i class="fa fa-search" style="font-size:24px"></i></a></td></tr>'
            print(message)
            flash(message, "Info")
    # Sending the message that no users are registered if that is the case
    else:
        # No Registered Users
        print("No Registered Users")
        message = "No registered Users"
        flash(message, "Error")
    return redirect(url_for("viewUsers"))


# Function to delete a particular user
def deleteUser(email):
    # Querying the user from DB to delete that user
    query = "DELETE FROM User WHERE email = '"+email+"'"
    result = dbController.deleteRecord(query)
    print(result)
    # Informing the admin if it has been deleted successfully by sending the message
    if result:
        message = "Record Successfully Deleted"
        flash(message, "Error")
    return redirect(url_for("viewUsers"))


# Function to edit a user's email address by sending the required information to the editEmail page
def editUserEmail(email):
    print(email)
    # Querying the table to find the user based on the email
    query = "SELECT firstname, lastName FROM User WHERE email = '" + email + "'"
    result = list(dbController.getRecords(query))
    if result:
        [firstName, lastName] = list(result[0])
        message = firstName + "|" + lastName + "|" + email
        flash(message, "Error")
    return redirect(url_for("editEmail"))


# Function to update the email based on the input entered by the admin
def updateEmail(request):
    # Querys to update User table and productsearchlogs tables
    query = "UPDATE User SET email = '" + request.form['userEmailId'] + "' WHERE email = '" + request.form['originalEmail'] +"'"
    result = dbController.editRecord(query)
    query = "UPDATE productsearchlogs SET email = '" + request.form['userEmailId'] + "' WHERE email = '" + request.form[
        'originalEmail'] + "'"
    # Informing the admin if the email updated successfully in the view
    result2 = dbController.editRecord(query)
    if result and result2:
        message = "Email successfully updated"
        flash(message, 'Success')
    # Informing the admin that there was an issue if it did not update properly and suggesting admin to check the DB manually
    else:
        message = "Error while updating email. (Can be an incomplete update, Check DB). Please try again later."
        flash(message, 'Error')
    return redirect(url_for("editEmail"))


# Function where admin can view search history for a particular user
def searchHistory(email):
    # Querying the DB to get the search history
    query = "SELECT DISTINCT ASIN FROM productsearchlogs WHERE email = '" + email + "' order by dateSearched DESC;"
    result = list(dbController.getRecords(query))
    print(result)
    # Displaying the results my passing them into View after querying relevant details of the product from
    # analyseproductscores table
    if len(result) > 0:
        for asin in result:
            query = "SELECT * FROM analyseproductscores WHERE ASIN = '" + asin[0] + "'"
            result2 = dbController.getRecords(query)
            if result2:
                scoreValue = result2[0][3]
                scorePercentage = result2[0][4]
                description = result2[0][6]
                message = '<tr><td>' + asin[0] + '</td>'
                message += '<td><a onclick="displayModal(\'' + description + '\')"><i class="fa fa-edit" style="font-size:36px"></i></a></td>'
                if 'NEUTRAL' in scoreValue:
                    message += '<td>The analysis was found to be non-conclusive. <br> Let your instincts take the wheel on this one! </td>'
                else:
                    message += '<td>The product was found to be ' + str(scorePercentage) + '% ' + scoreValue + '</td>'
                message += '<td><a onclick="displayModal(\'https://www.amazon.com/dp/' + asin[
                    0] + '\')"><i class="fa fa-link" style="font-size:36px"></i></a></td>'
                message += '</tr>'
                flash(message, "Info")
    # Informing admin if the user did not analyse any product
    else:
        # No Search Results
        print("No Recent Searches")
        message = "No Recent Searches"
        flash(message, "Error")
    return redirect(url_for("userSearchHistory"))
