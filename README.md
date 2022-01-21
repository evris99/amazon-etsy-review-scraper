# Amazon and Etsy review scraper

A simple desktop GUI program to download reviews from Amazon and Etsy and export them as an Excel file

## Usage

To download Etsy reviews you need an API key from [here](https://www.etsy.com/developers/documentation/getting_started/api_basics). This is not needed for Amazon reviews. 

To start downloading product reviews paste your API key in the top input box and write the URLs to the products on the lower input box. Then click the button.

## Installation

### Windows

You can find the executable [here](https://github.com/evris99/amazon-etsy-review-scraper/releases/download/v1.0.0/review_scraper.exe).

### Linux / Mac

For Mac and Linux, you need to install from source.

To run you need to have python installed. Execute to install the dependencies:
```
pip install -r requirements.txt
```

Then to start the program execute:
```
python review_scraper.py
```