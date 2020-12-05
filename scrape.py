import requests
from selenium import webdriver
import os
from datetime import date,timedelta
from dateutil.parser import parse
import pandas as pd
import numpy as np
from collections import Counter


current_directory = os.getcwd()
path_to_chromedriver = os.path.join(current_directory, "chromedriver")

url_test = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair%3A%22Daily%20Discussion%22&restrict_sr=1&sort=new'
html = requests.get(url_test)

url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair%3A%22Daily%20Discussion%22&restrict_sr=1&sort=new'
driver = webdriver.Chrome(executable_path= path_to_chromedriver)
driver.get(url)

yesterday = date.today() - timedelta(days=1)
links = driver.find_elements_by_xpath('//*[@class="_eYtD2XCVieq6emjKBH3m"]')
for a in links:
    if a.text.startswith("Daily Discussion Thread"):
        date = "".join(a.text.split(' ')[-3:])
        parsed = parse(date) 
        if parse(str(yesterday)) == parsed:
            link = a.find_element_by_xpath('../..').get_attribute('href')
 
    if a.text.startswith('Weekend'):
        weekend_date = a.text.split(' ')
        parsed_date = weekend_date[-3] + ' ' + weekend_date[-2].split('-')[1] + weekend_date[-1]
        parsed = parse(parsed_date) 
        saturday = weekend_date[-3] + ' ' + str(int(weekend_date[-2].split('-')[1].replace(',','')) - 1) + ' ' + weekend_date[-1] 
        
        if parse(str(yesterday)) == parsed: 
            link = a.find_element_by_xpath('../..').get_attribute('href')

        elif parse(str(yesterday)) == parse(str(saturday)):
            link = a.find_element_by_xpath('../..').get_attribute('href')
print(link)
stock_link = link.split('/')[-3]
html = requests.get(f'https://api.pushshift.io/reddit/submission/comment_ids/{stock_link}')
print(html)
raw_comment_list = html.json()
#print(raw_comment_list)
driver.close()


all_stocks = pd.read_csv('Nasdaq_all_stocks.csv')
stocks_list = all_stocks['Symbol'].tolist()
#print(stocks_list)

orig_list = np.array(raw_comment_list['data'])
#print(orig_list)

comment_list = ",".join(orig_list[0:1000])

def get_comments(comment_list):
    print('hie')
    html = requests.get(f'https://api.pushshift.io/reddit/comment/search?ids{comment_list}&fields=body&size=1000&subreddit=wallstreetbets')
    print(html)
    newcomments = html.json()
    return newcomments 

#goes over each comment checking its body and looks if the ticker of a stock is present in it. If it is then it adds one to that ticker
all_comments = []
stock_dict = {}
def get_stock_list(newcomments,stocks_list):
        for a in newcomments['data']:
            all_comments.append(a['body'])
            for ticker in stocks_list:
                if ticker in a['body']:
                    if ticker in stock_dict:
                        stock_dict[ticker]["comment"].append(a['body'])
                        stock_dict[ticker]["value"] += 1
                    else: 
                        stock_dict[ticker] = {}
                        stock_dict[ticker]["comment"] = []
                        stock_dict[ticker]["comment"].append(a['body'])
                        stock_dict[ticker]["value"] = 1


orig_list = np.array(raw_comment_list['data'])
remove_me = slice(0,1000)
cleaned = np.delete(orig_list, remove_me)
i = 0
while 0 < len(cleaned):
    print(len(cleaned))
    cleaned = np.delete(cleaned, remove_me)
    new_comments_list = ",".join(cleaned[0:1000])
    try:
        newcomments = get_comments(new_comments_list)
    except:
        print('there was an error')
    get_stock_list(newcomments,stocks_list)
stock = stock_dict

#print(stock)

index_list = []
value_list = []
comment_list = []
for key in stock:
    index_list.append(key)
    print(key)
    value_list.append(stock[key]["value"])
    comment_list.append(','.join(stock[key]["comment"]))

print(index_list)
print(value_list)

final_dataframe_unsorted = pd.DataFrame({'number':value_list, 'comment':comment_list}, index=index_list)
comments_dataframe = pd.DataFrame({'comments':all_comments})
final_dataframe = final_dataframe_unsorted.sort_values(by='number', ascending=False)
final_dataframe.to_csv('output.csv')
comments_dataframe.to_csv('all_comments.csv')

