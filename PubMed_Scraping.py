#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 22:35:49 2017

@author: Hongwei Liu
"""

from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import re
import random
from pymongo import MongoClient
import pandas as pd
import multiprocessing as mp

UserAgent = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]


def singlePageExtract(url):
    # Get author's organization and paper keywords
    org = ''
    
    print(url)
    # Set waiting time to avoid high traffic
    browser.implicitly_wait(random.randint(2, 3))
    
    # Get target page information
    tempo_html = requests.get(url,  headers = requestHeader(url))
    tempo_soup = BeautifulSoup(tempo_html.text, 'lxml')
    
    # Find and collect authors' organization
    try:
        collect = tempo_soup.find('dl', {'class':'ui-ncbi-toggler-slave'}).find_all('dd')
        for single in collect:
            org += ';' + single.get_text()
    except:
        org = 'ORGANIZATION_NA'
    
    # Collect article' keywords
    try:
        keywords = tempo_soup.find('div', {'class':'keywords'}).find('p').get_text().split(';')
    except:
        keywords = 'KEYWORDS_NA'
    
    return org, keywords

def requestHeader(url):
    # Build request headers
    headers = {
            'User-Agent':random.choice(UserAgent),
            'Referer': url,
            'Connection':'keep-alive',
            'Host':'www.ncbi.nlm.nih.gov'
            }
    return headers

    
def getMaxPageNum(searchWord):
    # Build search link
    url = 'https://www.ncbi.nlm.nih.gov/pubmed/?term=' + searchWord
    
    browser.get(url)
    browser.implicitly_wait(1)
    
    # Get maximum page number from returned research result
    soup = BeautifulSoup(browser.page_source, "lxml")
    max_num = int(soup.find('input', {'id':'pageno2'}).get('last'))
    return max_num
    

def multiCore(url_list):
    # Multiprocessing
    p = mp.Pool()

    for url in url_list:
        p.apply_async(extractWrite, args=(url,))

    # Close pool
    p.close()
    p.join()


def extractWrite(url):
    # Extract information and write into MongoDB
    org, keywords = singlePageExtract(url)
    # Extract title, author, date and other information
    title = row.find('a').get_text()
    author = row.find('p', {'class':'desc'}).get_text()
    journal = row.find('span', {'class':'jrnl'}).get('title')
    date_raw = row.find('p', {'class':'details'}).get_text()
    # Use regular expression to get time information
    date = re.findall(r'\d{4}[\s\w{3}\s\d+]*', date_raw)[0]

    # Build data to be loaded into MongoDB
    data = {
    'url': link,
    'title': title,
    'author': author,
    'journal': journal,
    'date': date,
    'org': org,
    'keywords': keywords
    }

    # Check if already existed
    if db.med_nlp.find({'url': link}).limit(1):
    	print(data, 'already exists.')
    else:
        # Insert data into MongoDB's Pubmed database's med_nlp collections
        db.med_nlp.insertOne(data)  


def informationExtraction():
    # Extract and build data 
    # Parse html information
    soup = BeautifulSoup(browser.page_source, "lxml")
    # Find sections with desired information
    all_div = soup.find_all('div', {'class':'rslt'})

    # Create/empty url_list to store all the new urls
    url_list = []
    
    # Iterate to extract information like author, title, journal, etc
    for row in all_div:
        # Build article's individual link
        link = default_link + row.find('a').get('href')
        url_list.append(link)
    
    # Operate multiprocessing
    multiCore(url_list)

    browser.implicitly_wait(1)

    # Click next buttion to navigate to the next page
    browser.find_element_by_xpath('//*[@title="Next page of results"]').click()


if __name__ == "__main__":
    # Website to scrape
    default_link = 'https://www.ncbi.nlm.nih.gov'

    # Start web browser
    browser = webdriver.Chrome('/home/katon/Desktop/chromedriver')

    # Start MongoDB
    MONGO_HOST= 'mongodb://localhost:27017/'
    client = MongoClient(MONGO_HOST)

    # Create or load Pubmed database
    db = client.Pubmed

    # Get input
    searchKeyWords = input("Please input your search key words/phrases!")

    # By default
    # searchKeyWords = 'natural language processing clinical'

    # Get max page number
    max_number = getMaxPageNum(searchKeyWords)

    count = 1

    while count < max_number:
        print(count)
        informationExtraction()
        count += 1

    print("finish")

## Access MongdoDB to analyze data   
#conn = MongoClient(host='localhost',port=27017)
#pub = conn['Pubmed']
#nlp = pub['med_nlp']
#
#data = pd.DataFrame(list(nlp.find()))
#print(data)