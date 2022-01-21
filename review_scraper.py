import sys
import re
from os import getcwd
from random import randint
from time import sleep
from urllib import parse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from PyQt5.QtGui import QTextOption, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# The headers for making a request to amazon
amazonHeaders = {
'authority': 'www.amazon.com',
'pragma': 'no-cache',
'cache-control': 'no-cache',
'dnt': '1',
'upgrade-insecure-requests': '1',
'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
'sec-fetch-site': 'none',
'sec-fetch-mode': 'navigate',
'sec-fetch-dest': 'document',
'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
}

# A list of common user agents used to avoid being blacklisted by amazon
commonUserAgents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# A global list that contains all the scraped reviews
reviewList = []

# Changes the user agent from the amazon headers
def changeUserAgent():
    amazonHeaders["user-agent"] = commonUserAgents[randint(0, len(commonUserAgents)-1)]

# Returns the soup object with the corresponding URL
def getSoup(url):
    r = requests.get(url, headers=amazonHeaders)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup

# Adds the reviews from the soup to the global reviewList
# and returns the number of reviews added
def getAmazonReviews(soup):
    newReviews = 0
    reviews = soup.find_all('div', {'data-hook': 'review'})
    try:
        for item in reviews:
            review = {
                'title': item.find('a', {'data-hook': 'review-title'}).text.strip(),
                'rating':  float(item.find('i', {'data-hook': 'review-star-rating'}).text.replace('out of 5 stars', '').strip()),
                'body': item.find('span', {'data-hook': 'review-body'}).text.strip(),
            }
            reviewList.append(review)
            newReviews = newReviews + 1
    except:
        pass

    return newReviews

# Returns the scraping URL from the user inputted URL
def getAmazonURL(url):
    urlAttr = parse.urlsplit(url)
    path = urlAttr.path.split("/")
    name = path[1]
    prodID = path[3]
    return f'https://{urlAttr.netloc}/{name}/product-reviews/{prodID}/reviewerType=all_reviews?pageNumber='


# Takes an etsy URL as an argument and returns the listing ID
def getListingID(link):
    url = parse.urlsplit(link)
    return int(url.path.split("/")[2])

# Takes a listing UD as an argument and returns the shop ID
def getShopID(listingID, etsyHeader):
    r = requests.get(f'https://openapi.etsy.com/v3/application/listings/{listingID}', headers=etsyHeader)
    data = r.json()
    return data["shop_id"]

# Takes a shop's reviews and a listing ID as arguments,
# adds the reviews of that listing to the global reviewList
# and returns the number of reviews added
def addToReviewList(reviews, listingID):
    count = 0
    for review in reviews:
        if review["listing_id"] == listingID and review["review"]:
            newReview = {
            'rating':  review["rating"],
            'body': review["review"]
            }

            reviewList.append(newReview)
            count = count + 1
    return count


# Takes a file path and a suffix and returns a file path
#  with the suffix if one is not present
def addFileExtension(filepath, ext):
    rePattern = f".*\\.{ext}$"
    if re.match(rePattern, filepath) == None:
        return filepath + "." + ext

    return filepath

class WorkerThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, links, etsyApiKey, parent=None):
        super().__init__(parent)
        self.links = links
        self.etsyApiKey = etsyApiKey

    def run(self):
        for link in self.links:
            host = parse.urlsplit(link).netloc
            if "amazon" in host:
                self.getAllAmazonReviews(link)
            elif "etsy" in host:
                self.getAllEtsyReviews(link)
            else:
                print(f'{link} is not a valid URL')

    # Gets all reviews from amazon from url input and adds them to the global reviewList
    def getAllAmazonReviews(self, urlInput):
        url = getAmazonURL(urlInput)
        print(f"Getting reviews from {url}")
        for x in range(1,999):
            # Every 100 page requests change user agent
            if (x-1) % 100 == 0:
                changeUserAgent()

            soup = getSoup(url + str(x))
            newReviews = getAmazonReviews(soup)
            self.progress.emit(len(reviewList))
            print(f'Got {str(len(reviewList))} reviews')
            if soup.find('li', {'class': 'a-disabled a-last'}) or newReviews == 0:
                break

    # Gets all reviews from etsy from url input and adds them to the global reviewList
    def getAllEtsyReviews(self, link):
        print(f"Getting reviews from {link}")
        etsyHeader = { "x-api-key": self.etsyApiKey }
        listingID = getListingID(link)
        shopID = getShopID(listingID, etsyHeader)
        limit = 100
        offset = 0
        reviewCount = 1
        while offset < reviewCount:
            r = requests.get(f'https://openapi.etsy.com/v3/application/shops/{shopID}/reviews?limit={limit}&offset={offset}', headers=etsyHeader)
            data = r.json()
            reviewCount = data["count"]
            newReviews = addToReviewList(data["results"], listingID)
            if newReviews > 0:
                self.progress.emit(len(reviewList))
                print(f'Got {str(len(reviewList))} reviews')
            offset = offset + limit

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initGUI()

    def initGUI(self):
        self.setWindowTitle("Review Collector")
        self.resize(960, 540)

        # Title Label
        self.lblTitle = QLabel("### Enter the Amazon/Etsy URLs you want to get reviews from")
        self.lblTitle.setTextFormat(Qt.TextFormat.MarkdownText)
        self.lblTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Field for Etsy API key
        self.lineApiKey = QLineEdit()

        # Text Editor
        self.txtEdit = QTextEdit()
        self.txtEdit.setAcceptRichText(False)
        self.txtEdit.setPlaceholderText("https://www.etsy.com/listing/000000000/example-product\nhttps://www.amazon.com/example-product/dp/A0A0A0A000/\n...")
        self.txtEdit.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        # Start Button
        self.btnStart = QPushButton("Start collecting")
        self.btnStart.clicked.connect(self.onStart)

        # Progress Label
        self.lblProgress = QLabel("0 reviews collected")
        self.lblProgress.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.lblTitle)
        layout.addWidget(self.lineApiKey)
        layout.addWidget(self.txtEdit)
        layout.addWidget(self.lblProgress)
        layout.addWidget(self.btnStart)
        self.setLayout(layout)

    # Runs when the button is clicked
    def onStart(self):
        self.btnStart.setEnabled(False)
        apiKey = self.lineApiKey.text()
        links = self.txtEdit.toPlainText().split()
        if links:
            self.worker = WorkerThread(links, apiKey)
            self.worker.start()
            self.worker.finished.connect(self.onCompletion)
            self.worker.progress.connect(self.onProgress)
        else:
            self.lblProgress.setText("No URLS given")
            self.btnStart.setEnabled(True)

    # Runs when the worker thread is completed
    def onCompletion(self):
        if reviewList:
            df = pd.DataFrame(reviewList)
            outFile, fileType = QFileDialog.getSaveFileName(directory=getcwd(), caption="Choose export file", filter="Microsoft Excel Files(*.xlsx)")
            if fileType == "Microsoft Excel Files(*.xlsx)":
                outFile = addFileExtension(outFile, "xlsx")
                df.to_excel(outFile, index=False)
                msg = f"Saved as {outFile}"
                self.lblProgress.setText(msg)
                print(msg)
            else:
                msg = "No file selected"
                self.lblProgress.setText(msg)
                print(msg)

            reviewList.clear()
        else:
            self.lblProgress.setText("No reviews found")

        self.btnStart.setEnabled(True)
    
    # Runs when the worker thread has an update
    def onProgress(self, reviewCount):
        self.lblProgress.setText(str(reviewCount) + " reviews collected")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())