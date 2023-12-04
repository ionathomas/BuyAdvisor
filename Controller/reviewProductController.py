import requests
import re
import validators

from datetime import datetime
from transformers import pipeline
from flask import redirect, url_for, flash, session
from bs4 import BeautifulSoup

from Controller import dbController


# Function to extract the ASIN number of an amazon product
def extractAsin(url):
    idx = re.search("/dp/", url)
    if not idx:
        return -1
    url = url[idx.start():]
    url = re.sub("/dp/", "", url)
    asin = url[0:10]
    return asin


# Function to check if the url entered by the user is valid or not
def validURLCheck(url):
    if "https://www" not in url:
        url = "https://" + url
    if validators.url(url) and "amazon.com" in url:
        return True
    else:
        return False


# Function to Scrap the reviews from amazon using RAPID API
def scrapReviews(asin):
    reviews = []
    url = "https://real-time-amazon-data.p.rapidapi.com/product-reviews"

    headers = {
        "X-RapidAPI-Key": "4f379d1851msh6ea897038188405p1667ddjsnba6c97df884b",
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    flag = 0
    for num in range(1, 6):
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


# Function to get the Product Title with the help of the asin extracted
def getProductTitle(asin):

    HEADERS = ({'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit / 537.36(KHTML, like Gecko)'
                             'Chrome / 44.0.2403.157 Safari / 537.36', 'Accept-Language': 'en-US, en;q=0.5'})
    webpage = requests.get("https://www.amazon.com/dp/"+asin, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "lxml")
    try:
        title = soup.find("span", attrs={"id": 'productTitle'})
        title_value = title.string
        title_string = title_value.strip().replace(',', '')
        title_string = title_string.replace('"', '')
        title_string = title_string.replace("'", "")
    except AttributeError:
        title_string = "N/A"
    return title_string


# Function to classify reviews
def classifyReviews(payload):
    API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
    headers = {"Authorization": "Bearer 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"}

    response = requests.post(API_URL, headers=headers, json=payload)
    reviewsClassified = response.json()
    result=[]
    for i in reviewsClassified:
        result.append(i[0]['label'])
    print(result)
    return result


# Function to analyze the reviews scrapped
def analyzeReviews(reviews):
    score = {'POS': 0, 'NEG': 0}
    cleanUpReviews = []
    for i in reviews:
        if len(i.split()) <= 450:
            cleanUpReviews.append(i)
    print(cleanUpReviews)
    result = classifyReviews({
        "inputs": cleanUpReviews
    })
    for i in result:
        match i:
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
    highScore = round((maxScore / len(reviews)) * 100, 2)
    score['POS'] /= len(reviews)
    score['POS'] *= 100
    score['POS'] = round(score['POS'],2)
    score['NEG'] = 100 - score['POS']
    return [highScorePosition, highScore, len(reviews), [score['POS'], score['NEG']]]


# Funtion to check if the percentage of positive and negative reviews are the same or not
def scoreListCheck(scores):
    scoreList = list(dict.fromkeys(scores))
    if len(scoreList) == 1:
        return False
    else:
        return True


# Function to insert the search logs into productsearchlogs table
def insertIntoLogs(email, asin, date):
    query = "INSERT INTO productsearchlogs(email, ASIN, dateSearched) VALUES ('" + email + "', '" + asin + "', '" + date + "')"
    return dbController.addRecord(query)


# Function to get the score value of the highest position
def getScoreValue(highestScorePosition):
    match highestScorePosition:
        case 'POS':
            return 'Positive'
        case 'NEG':
            return 'Negative'


# Main function that deals with the process of scraping reviews, analysing them and displaying the results.
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

                # If the product was found in the DB, checking if they were reviewed in less than 15 days
                # If less than 15 days, display as is
                # If 15 days or more, scrap and analyse reviews and display the results
                if delta.days < 15:
                    scoreValue = result[0][3]
                    highScore = result[0][4]
                    numOfReviews = result[0][5]
                    scores = [result[0][1], result[0][2]]
                    if scoreListCheck(scores):
                        print(scores)

                        # Adding logs and notifying the user the result of the analysis
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

                        # Adding logs and notifying the user the result of the analysis
                        result = insertIntoLogs(session['email'],asin,date2)
                        if not result:
                            print("Error adding into productsearchlogs")
                        message = "The analysis was found to be non-conclusive. Let your instincts take the wheel on this one"
                        flash(message, 'Error')
                        print(message)
                        return redirect(url_for("reviewProduct"))
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
                            return redirect(url_for("reviewProduct"))
                    except:
                        message = "The analysis was could not be processed. Uncaught Exception. Try analyzing another product from amazon.com."
                        flash(message, 'Error')
                        print("Unable to use RapidAPI")
                        print(message)
                    else:

                        # Since the product is already in the table, the scores are just updated using the UPDATE query
                        scoreValue = getScoreValue(highestScorePosition)

                        if scoreListCheck(scores):
                            print(scores)

                            # Adding logs and notifying the user the result of the analysis
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

                            # Adding logs and notifying the user the result of the analysis
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

            # If the product is not found in the analyseproductscores table
            # Scraping and analysing the reviews
            else:
                description = "NA"
                #getProductTitle(asin)
                try:
                    reviews = scrapReviews(asin)
                    if len(reviews) >= 10:
                        # Analyze Reviews using ML model
                        [highestScorePosition, highScore, numOfReviews, scores] = analyzeReviews(reviews)
                    else:
                        message = "The number of reviews are not sufficient for analysis"
                        flash(message, 'Error')
                        print(message)
                        return redirect(url_for("reviewProduct"))
                except:
                    message = "The analysis was could not be processed. Uncaught Exception. Try analyzing another URL."
                    flash(message, 'Error')
                    print(message)
                    print("Unable to fetch RapidAPI")
                    return redirect(url_for("reviewProduct"))
                else:

                    now = datetime.now()
                    date = now.strftime('%Y-%m-%d %H:%M:%S')
                    scoreValue = getScoreValue(highestScorePosition)
                    if scoreListCheck(scores):
                        print(scores)

                        # Adding logs and notifying the user the result of the analysis
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
                        # Adding logs and notifying the user the result of the analysis
                        result = insertIntoLogs(session['email'], asin, date)
                        if not result:
                            print("Error adding into productsearchlogs")
                        else:
                            query = "INSERT INTO analyseproductscores(ASIN, Pos, Neg, HighestCategory, HighestCategoryPercentage, NumberOfReviewsAnalysed, ProductDescription, DateAnalysed) VALUES ('"+asin+"'," +str(scores[0])+ "," +str(scores[1])+ ",'NEUTRAL', " + str(highScore) + ", " + str(numOfReviews) + ", '" + description + "', '"+ date + "')"
                            result2 = dbController.addRecord(query)
                            if not result2:
                                print("Error updating into analyseproductscores")
                        message = "The analysis was found to be non-conclusive. Let your instincts take the wheel on this one"
                        flash(message, 'Error')
                        print(message)

    # Notifying the user if the URL enterred was not from amazon.com or if it was not a valid url
    else:
        if "www.amazon" in urlPage:
            message = "This is not a product from the US store. Please paste a URL from the US store"
        else:
            message = "This is not a valid amazon.com URL. Please paste a valid URL from amazon.com"
        flash(message, 'Error')
        print(message)
    return redirect(url_for("reviewProduct"))
