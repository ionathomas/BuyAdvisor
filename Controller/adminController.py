from flask import redirect, url_for, flash, render_template, session

from Controller import dbController
from Model.User import User

def viewUsers():
    query = "SELECT firstName, lastName, email FROM User"
    result = list(dbController.getRecords(query))
    print(result)
    if len(result) > 0:
        for user in result:
            message = '<tr><td>'+user[0]+' '+user[1]+'</td>'
            message += '<td>'+user[2]+'</td>'
            message += '<td><a onclick="editEmail(\''+user[2]+'\')"><i class="fa fa-edit" style="font-size:24px"></i></a></td>'
            message += '<td><a onclick="deleteUser(\''+user[2]+'\')"><i class="fa fa-trash" style="font-size:24px"></i></a></td>'
            message += '<td><a onclick="userSearchHistory(\''+user[2]+'\')"><i class="fa fa-search" style="font-size:24px"></i></a></td></tr>'
            print(message)
            flash(message, "Info")
    else:
        # No Registered Users
        print("No Registered Users")
        message = "No registered Users"
        flash(message, "Error")
    return redirect(url_for("viewUsers"))


def deleteUser(email):
    query = "DELETE FROM User WHERE email = '"+email+"'"
    result = dbController.deleteRecord(query)
    print(result)
    if result:
        message = "Record Successfully Deleted"
        flash(message, "Error")
    return redirect(url_for("viewUsers"))


def editUserEmail(email):
    print(email)
    query = "SELECT firstname, lastName FROM User WHERE email = '" + email + "'"
    result = list(dbController.getRecords(query))
    if result:
        [firstName, lastName] = list(result[0])
        message = firstName + "|" + lastName + "|" + email
        flash(message, "Error")
    return redirect(url_for("editEmail"))


def updateEmail(request):
    query = "UPDATE User SET email = '" + request.form['userEmailId'] + "' WHERE email = '" + request.form['originalEmail'] +"'"
    result = dbController.editRecord(query)
    if result:
        message = "Email successfully updated"
        flash(message, 'Success')
    else:
        message = "Error while updating email. Please try again later."
        flash(message, 'Error')
    return redirect(url_for("editEmail"))


def searchHistory(email):
    query = "SELECT DISTINCT ASIN FROM productsearchlogs WHERE email = '" + email + "' order by dateSearched DESC;"
    result = list(dbController.getRecords(query))
    print(result)
    if len(result) > 0:
        for asin in result:
            query = "SELECT * FROM analyseproductscores WHERE ASIN = '" + asin[0] + "'"
            result2 = dbController.getRecords(query)
            if result2:
                scoreValue = result2[0][3]
                scorePercentage = result2[0][4]
                description = result2[0][6]
                message = '<tr><td>' + asin[0] + '</td>'
                if 'NEUTRAL' in scoreValue:
                    message += '<td>The analysis was found to be non-conclusive. Let your instincts take the wheel on this one</td>'
                else:
                    message += '<td>The product was found to be ' + str(scorePercentage) + '% ' + scoreValue + '</td>'
                message += '<td><a onclick="displayModal(\'' + description + '\')"><i class="fa fa-edit" style="font-size:36px"></i></a></td>'
                message += '<td><a onclick="displayModal(\'https://www.amazon.com/dp/' + asin[
                    0] + '\')"><i class="fa fa-link" style="font-size:36px"></i></a></td>'
                message += '</tr>'
                print(message)
                flash(message, "Info")
    else:
        # No Search Results
        print("No Recent Searches")
        message = "No Recent Searches"
        flash(message, "Error")
    return redirect(url_for("userSearchHistory"))
