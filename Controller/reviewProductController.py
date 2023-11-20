import requests
import re
import validators

from datetime import datetime
from transformers import pipeline
from flask import redirect, url_for, flash, session

from Controller import dbController


def extractAsin(url):
    idx = re.search("/dp/", url)
    if not idx:
        return -1
    url = url[idx.start():]
    url = re.sub("/dp/", "", url)
    asin = url[0:10]
    return asin


def validURLCheck(url):
    if "https://www" not in url:
        url = "https://" + url
    if validators.url(url) and "amazon.com" in url:
        return True
    else:
        return False


def scrapReviews(asin):
    reviews = []
    url = "https://real-time-amazon-data.p.rapidapi.com/product-reviews"

    headers = {
        "X-RapidAPI-Key": "4f379d1851msh6ea897038188405p1667ddjsnba6c97df884b",
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    flag = 0
    # CHANGE RANGE TO 6 to include 5th page
    for num in range(1, 2):
        querystring = {"asin": asin, "country": "US", "sort_by": "MOST_RECENT", "verified_purchases_only": "false",
                       "images_or_videos_only": "false", "page": num, "page_size": "10"}
        response = requests.get(url, headers=headers, params=querystring)
        res = response.json()
        if res['status'] == 'OK' and res['data'] != {}:
            for review in res['data']['reviews']:
                resultReview = review['review_title'] + ". " + review['review_comment']
                reviews.append(resultReview)
                flag = 1
        else:
            break

    if flag == 1:
        return reviews
    else:
        return []


def getProductDescription(asin):

    url = "https://real-time-amazon-data.p.rapidapi.com/product-details"

    querystring = {"asin": asin, "country": "US"}

    headers = {
        "X-RapidAPI-Key": "4f379d1851msh6ea897038188405p1667ddjsnba6c97df884b",
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    res = response.json()
    flag = 0

    if res['status'] == 'OK' and res['data'] != {} and res['data']['product_description']:
        return res['data']['product_description']
    else:
        return "Description not found"


def analyzeReviews(reviews):
    score = {'POS': 0, 'NEG': 0}
    classification = pipeline('sentiment-analysis')
    result = classification(reviews)
    for i in result:
        match i['label']:
            case 'POSITIVE':
                score['POS'] += 1
            case 'NEGATIVE':
                score['NEG'] += 1
    maxScore = max(list(score.values()))
    idx = list(score.values()).index(maxScore)
    highScorePosition = ""
    match idx:
        case 0:
            highScorePosition = 'POS'
        case 1:
            highScorePosition = 'NEG'
    highScore = maxScore / len(reviews)
    score['POS'] /= len(reviews)
    score['POS'] *= 100
    score['NEG'] /= len(reviews)
    score['NEG'] *= 100
    return [highScorePosition, highScore * 100, len(reviews), [score['POS'], score['NEG']]]

def scoreListCheck(scores):
    scoreList = list(dict.fromkeys(scores))
    if len(scoreList) == 1:
        return False
    else:
        return True

def insertIntoLogs(email, asin, date):
    query = "INSERT INTO productsearchlogs(email, ASIN, dateSearched) VALUES ('" + email + "', '" + asin + "', '" + date + "')"
    return dbController.addRecord(query)

def getScoreValue(highestScorePosition):
    match highestScorePosition:
        case 'POS':
            return 'Positive'
        case 'NEG':
            return 'Negative'

def reviewProduct(urlPage):
    # Validity check of the URL entered by the user
    if validURLCheck(urlPage):
        # Extract ASIN
        asin = extractAsin(urlPage)
        print(asin)

        # If ASIN not found
        if asin == -1:
            message = "Product not found with the URL pasted. Try again with the proper URL"
            flash(message, 'Error')
            print(message)

        else:
            # Check if ASIN in analyseproductscores
            query = "SELECT * FROM analyseproductscores WHERE ASIN = '" + asin + "'"
            result = list(dbController.getRecords(query))
            if len(result) == 1:
                date1 = result[0][7].strftime('%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                date2 = now.strftime('%Y-%m-%d %H:%M:%S')
                d1 = datetime.strptime(date1, "%Y-%m-%d %H:%M:%S")
                d2 = datetime.strptime(date2, "%Y-%m-%d %H:%M:%S")
                delta = d2 - d1

                if delta.days < 15:
                    scoreValue = result[0][3]
                    highScore = result[0][4]
                    numOfReviews = result[0][5]
                    scores = [result[0][1], result[0][2]]
                    if scoreListCheck(scores):
                        print(scores)
                        result = insertIntoLogs(session['email'], asin, date2)
                        if not result:
                            print("Error adding into productsearchlogs")
                        message = "The product was found to be {}% {}.".format(highScore, scoreValue)
                        scoreMessage = map(str, scores)
                        scoreMessage = ','.join(scoreMessage)
                        flash(message, 'Success')
                        flash(scoreMessage, 'Info')
                    else:
                        print(scores)
                        result = insertIntoLogs(session['email'],asin,date2)
                        if not result:
                            print("Error adding into productsearchlogs")
                        message = "The analysis was found to be non-conclusive. Let your instincts take the wheel on this one"
                        flash(message, 'Error')
                        print(message)
                else:
                    # Scrap Reviews using API
                    try:
                        reviews = scrapReviews(asin)
                        if len(reviews) >= 10:
                            # Analyze Reviews using ML model
                            [highestScorePosition, highScore, numOfReviews, scores] = analyzeReviews(reviews)
                        else:
                            message = "The number of reviews are not sufficient for analysis"
                            flash(message, 'Error')
                            print(message)
                    except:
                        message = "The analysis was could not be processed. Uncaught Exception. Try analyzing another product from amazon.com."
                        flash(message, 'Error')
                        print(message)
                    else:
                        scoreValue = getScoreValue(highestScorePosition)
                        if scoreListCheck(scores):
                            print(scores)
                            result = insertIntoLogs(session['email'], asin, date2)
                            if result:
                                query = "UPDATE analyseproductscores SET Pos = " +str(scores[0])+ ", Neg = " +str(scores[1])+ ", HighestCategory = '" +scoreValue+ "' ,HighestCategoryPercentage = " +str(highScore)+ ", NumberOfReviewsAnalysed = " +str(numOfReviews)+ ", DateAnalysed = '" +date2+ "' WHERE ASIN = '" + asin + "'"
                                result2 = dbController.editRecord(query)
                                if not result2:
                                    print("Error updating into analyseproductscores")
                            else:
                                print("Error adding into productsearchlogs")
                            message = "The product was found to be {}% {}.".format(highScore, scoreValue)
                            scoreMessage = map(str, scores)
                            scoreMessage = ','.join(scoreMessage)
                            flash(message, 'Success')
                            flash(scoreMessage, 'Info')
                        else:
                            print(scores)
                            result = insertIntoLogs(session['email'], asin, date2)
                            if not result:
                                print("Error adding into productsearchlogs")
                            else:
                                query = "UPDATE analyseproductscores SET Pos = " + str(scores[0]) + ", Neg = " + str(
                                    scores[1]) + ", HighestCategory = 'NEUTRAL' ,HighestCategoryPercentage = " + str(
                                    highScore) + ", NumberOfReviewsAnalysed = " + str(
                                    numOfReviews) + ", DateAnalysed = '" + date2 + "' WHERE ASIN = '" + asin + "'"
                                result2 = dbController.editRecord(query)
                                if not result2:
                                    print("Error updating into analyseproductscores")
                            message = "The analysis was found to be non-conclusive. Let your instincts take the wheel on this one"
                            flash(message, 'Error')
                            print(message)
            else:
                try:
                    reviews = scrapReviews(asin)
                    description = getProductDescription(asin)
                    if len(reviews) >= 10:
                        # Analyze Reviews using ML model
                        [highestScorePosition, highScore, numOfReviews, scores] = analyzeReviews(reviews)
                    else:
                        message = "The number of reviews are not sufficient for analysis"
                        flash(message, 'Error')
                        print(message)
                except:
                    message = "The analysis was could not be processed. Uncaught Exception. Try analyzing another URL."
                    flash(message, 'Error')
                    print(message)
                else:
                    now = datetime.now()
                    date = now.strftime('%Y-%m-%d %H:%M:%S')
                    scoreValue = getScoreValue(highestScorePosition)
                    if scoreListCheck(scores):
                        print(scores)
                        result = insertIntoLogs(session['email'], asin, date)
                        if result:
                            query = "INSERT INTO analyseproductscores(ASIN, Pos, Neg, HighestCategory, HighestCategoryPercentage, NumberOfReviewsAnalysed, ProductDescription, DateAnalysed) VALUES ('"+asin+"'," +str(scores[0])+ "," +str(scores[1])+ ",'" + scoreValue + "', " + str(highScore) + ", " + str(numOfReviews) + ", '" + description + "', '" + date + "')"
                            result2 = dbController.addRecord(query)
                            if not result2:
                                print("Error adding into analyseproductscores")
                        else:
                            print("Error adding into productsearchlogs")

                        message = "The product was found to be {}% {}.".format(highScore, scoreValue)
                        scoreMessage = map(str, scores)
                        scoreMessage = ','.join(scoreMessage)
                        flash(message, 'Success')
                        flash(scoreMessage, 'Info')
                    else:
                        print(scores)
                        result = insertIntoLogs(session['email'], asin, date)
                        if not result:
                            print("Error adding into productsearchlogs")
                        else:
                            query = "INSERT INTO analyseproductscores(ASIN, Pos, Neg, HighestCategory, HighestCategoryPercentage, NumberOfReviewsAnalysed, DateAnalysed) VALUES ('"+asin+"'," +str(scores[0])+ "," +str(scores[1])+ ",'NEUTRAL', " + str(highScore) + ", " + str(numOfReviews) + ", '" + date + "')"
                            result2 = dbController.addRecord(query)
                            if not result2:
                                print("Error updating into analyseproductscores")
                        message = "The analysis was found to be non-conclusive. Let your instincts take the wheel on this one"
                        flash(message, 'Error')
                        print(message)

    else:
        if "www.amazon" in urlPage:
            message = "This is not a product from the US store. Please paste a URL from the US store"
        else:
            message = "This is not a valid amazon.com URL. Please paste a valid URL from amazon.com"
        flash(message, 'Error')
        print(message)
    return redirect(url_for("reviewProduct"))
