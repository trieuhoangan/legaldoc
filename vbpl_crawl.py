import requests
import scrapy
from scrapy.selector import Selector

import pymysql
import pymysql.cursors
import re
import json
import random
import time
import traceback
import sys
def striphtml(data):
    # data = data.replace("\n"," ")
    data = data.replace("\r"," ")
    data = data.replace("\t"," ")
    data = data.replace("\\"," ")
    data = data.replace("'"," ")
    data = data.replace('"'," ")
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def normalize_text(text):
    
    for i in range(10):
        text = text.replace("  "," ")
    
    for i in range(10):
        text = text.replace(" \n","\n")
    
    for i in range(10):
        text = text.replace("\n ","\n")
    
    for i in range(10):
        text = text.replace("\n \n","\n")
    
    for i in range(10):
        text = text.replace("\n\n","\n")
    return text

def get_response(url):
    session = requests.Session()
    data = session.get(url)
    content = data.content.decode('utf-8')
    response = Selector(text=content)
    return response

def parse(response):
    toanvan_str = response.xpath('//div[@id="toanvancontent"]').get()
    toanvan_str = striphtml(toanvan_str)

    return toanvan_str

def main():

    urls=[
        'http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32801&Keyword=Hi%E1%BA%BFn%20ph%C3%A1p%202013',
        "http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=95942&Keyword=B%E1%BB%99%20lu%E1%BA%ADt%20d%C3%A2n%20s%E1%BB%B1%202015",
        "http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=25700&Keyword=Lu%E1%BA%ADt%20th%C6%B0%C6%A1ng%20m%E1%BA%A1i",
        "http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=132957&Keyword=lu%E1%BA%ADt%20an%20ninh%20m%E1%BA%A1ng",
        "http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=96035&Keyword=lu%E1%BA%ADt%20t%E1%BB%91%20t%E1%BB%A5ng%20h%C3%A0nh%20ch%C3%ADnh",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=26355",
        "https://vbpl.vn/bogiaoducdaotao/Pages/vbpq-toanvan.aspx?ItemID=136042&Keyword=",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=152501",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=146648",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=142850",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=137311",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=137312",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=158993",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=129350",
        "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=101873",
        "http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=36870&Keyword=Lu%E1%BA%ADt%20H%C3%B4n%20nh%C3%A2n%20v%C3%A0%20gia%20%C4%91%C3%ACnh",
        "http://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=146609&Keyword=lu%E1%BA%ADt%20m%C3%B4i%20tr%C6%B0%E1%BB%9Dng"
    ]
    # urls=[cur_url]

    count=0
    for url in urls:
        response = get_response(url)
        text = parse(response)
        text = normalize_text(text)
        print(text[0])
        filename="statue_laws/law{}.txt".format(count)
        count+=1
        with open(filename,'w',encoding="utf-8") as f:
            f.write(text)
        time.sleep(5)
    print("end")
if __name__ == "__main__":
    # session = requests.Session()
    
    # data = session.get(url)
    # content = data.content.decode('utf-8')
    # response = Selector(text=content)
    # print(response.xpath('html'))
    main()