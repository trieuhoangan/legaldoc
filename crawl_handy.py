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
    data = data.replace("\n"," ")
    data = data.replace("\r"," ")
    data = data.replace("\\"," ")
    data = data.replace("'"," ")
    data = data.replace('"'," ")
    p = re.compile(r'<.*?>')
    return p.sub('', data)
def get_db_connection(host,user,pw,db):
    return pymysql.connect(host=host,
                                user=user,
                                password=pw,
                                database=db,
                                cursorclass=pymysql.cursors.DictCursor)
def extract_date_and_org(table):
    trs = table.css('tr')
    org = trs[0].css('td')[0].get()
    cou_name = trs[0].css('td')[1].get()
    doc_id = trs[1].css('td')[0].get()
    date = trs[1].css('td')[1].get()
    return org,cou_name,doc_id,date
def extract_signer(table):
    trs = table.css('tr')
    receiver = trs[0].css('td')[0].get()
    signer = trs[0].css('td')[1].get()
    return receiver, signer
def extract_table(table):
    trs = table.css('tr')
    content = []
    for tr in trs:
        tds = [striphtml(td) for td in tr.css('td').getall()]
        content.append(tds)
    return content
def merge_paragraphs(paragraphs):
    new_para = [striphtml(doc) for doc in paragraphs]
    text = " ".join(new_para)
    return text

def extract_data_from_single_page(response):
    div_content_doc = response.xpath('//div[@id="divContentDoc"]/div[@class="content1"]/div/div').get()
    tables = Selector(text=div_content_doc).xpath('//table')
    org,cou_name,doc_id,date = extract_date_and_org(tables[0])
    receiver, signer = extract_signer(tables[1])
    # appendix = []
    # if len(tables) > 2:
    #     for i in range(2,len(tables)):
    #         appendix.append(extract_table(tables[i]))
    p_tags = response.xpath('//div[@id="divContentDoc"]/div[@class="content1"]/div/div/p').getall()
    if len(p_tags)==0:
        p_tags = response.xpath('//div[@id="divContentDoc"]/div[@class="content1"]/div/div/div/p').getall()
    content = merge_paragraphs(p_tags)
    # str_app = json.dumps(appendix)
    doc_object = {
        "org":striphtml(org),        
        "cou":striphtml(cou_name),
        "doc_id":striphtml(doc_id),
        "date":striphtml(date),
        "content":content,
        "receiver":striphtml(receiver),
        "signer":striphtml(signer)
        # "appendix":str_app
    }
    return doc_object

def save_to_database(data,link):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        # try:
        org = data["org"].replace("\'"," ")
        doc_id = data["doc_id"].replace("\'"," ")
        date = data["date"].replace("\'"," ")
        content = data["content"].replace("\'"," ")
        receiver = data["receiver"].replace("\'"," ")
        signer = data["signer"].replace("\'"," ")
        # appendix = data["appendix"].replace("\'"," ")
        # print(org)
        sql = 'select * from doc2 where link="{}"'.format(link)
        cursor.execute(sql)
        results = cursor.fetchall()
        if len(results) == 0:
            print("saved doc")
            sql = 'insert into doc2(doc_id,org,date,receiver,signer,content,link,domain) value ("{}","{}","{}","{}","{}","{}","{}","thuvienphapluat")'.format(doc_id,org,date,receiver,signer,content,link)
            # print(sql)
            cursor.execute(sql)
        else:
            print("allready had it")
        # except:
        #     print("error")
        connection.commit()
    connection.close()  

def update_crawled_link(link):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        sql = "select * from link"
        cursor.execute(sql)
        results = cursor.fetchall()
        if len(results) >0:
            sql = 'update link set link.link="{}" where id=1 '.format(link)
        else:
            sql = 'insert into link(id,link) values(1,"{}")'.format(link)
        print(sql)
        cursor.execute(sql)  
        connection.commit()
    connection.close()  

def insert_crawled_link(link):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        # sql = "select * from link"
        # cursor.execute(sql)
        # results = cursor.fetchall()
        # if len(results) >0:
        #     sql = 'update link set link.link="{}" where id=1 '.format(link)
        # else:
        sql = 'insert into link(link) values("{}")'.format(link)
        # print(sql)
        cursor.execute(sql)  
        connection.commit()
    connection.close()  

def get_crawled_link():
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        sql = "select * from link"
        cursor.execute(sql)
        results = cursor.fetchall()
    connection.close() 
    if len(results)>0:
        return results[0]["link"]
    else:
        return None

def is_crawled(url):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        sql = 'select * from doc2 where link="{}"'.format(url)
        cursor.execute(sql)
        results = cursor.fetchall()
    connection.close() 
    if len(results) >0:
        return True
    else:
        return False

def check_if_crawled(link):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        sql = 'select * from link where link="{}"'.format(link)
        cursor.execute(sql)
        results = cursor.fetchall()
    connection.close() 
    if len(results)>0:
        return True
    else:
        return False

def clear_crawled_link():
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        sql = "delete from link where id=1"
        cursor.execute(sql)
        results = cursor.fetchall()
        connection.commit()
    connection.close() 

def get_single_doc_links(response):
        a =response.xpath('//div[@id="block-info-advan"]/div')[1]
        b0 = a.xpath('//div[@class="content-0"]/div[@class="left-col"]/div[@class="nq"]/p[@class="nqTitle"]/a/@href').getall()
        b1 = a.xpath('//div[@class="content-1"]/div[@class="left-col"]/div[@class="nq"]/p[@class="nqTitle"]/a/@href').getall()
        c =[]
        c.extend(b0)
        c.extend(b1)
        return c

def get_next_pages_links(response):
    domain = "https://thuvienphapluat.vn/page/"
    links = response.xpath('//div[@class="cmPager"]/a/@href').getall()
    page_links = []
    for link in links:
        link = domain+link 
        page_links.append(link)
    return page_links

def parse_pages_list(response,do_crawl_pages=True):
    print("got in here")
    doc_links = get_single_doc_links(response)
    for link in doc_links:
        if do_crawl_pages==True:
            try:
                print("start crawl ",link)
                crawled = is_crawled(link)
                if crawled==False:
                    doc_response = get_response(link)
                    parse_single_page(doc_response,link)
                    time.sleep(random.randint(10,13))    
                else:
                    continue    
            except:
                print("error happend")
                traceback.print_exception(*sys.exc_info())
                time.sleep(random.randint(10,13))
                continue
    
    page_links = get_next_pages_links(response)
    # for link in page_links:
    #     if link not in urls:
    #         urls.append(link)
    return page_links

def parse_single_page(response,link):
    doc = extract_data_from_single_page(response)
    save_to_database(doc,link)

def get_response(url):
    session = requests.Session()
    data = session.get(url)
    content = data.content.decode('utf-8')
    response = Selector(text=content)
    return response

def main():
    first_url = "https://thuvienphapluat.vn/page/tim-van-ban.aspx"
    cur_url = "https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword=&area=0&match=True&type=0&status=0&signer=0&sort=1&lan=1&scan=0&org=0&fields=&page="
    urls=[cur_url + str(i) for i in range(4000,4500)]
    # urls=[cur_url]
    crawled=[]
    
    # for url in urls:
    while True:
        url=urls[0]
        print(url)
        # if url not in crawled:
        #     urls.remove(url)
        #     crawled.append(url)
        if check_if_crawled(url)==True:
            urls.remove(url)
            # response = get_response(url)
            # extra_urls = parse_pages_list(response,do_crawl_pages=False)
            # urls+=extra_urls
            # urls = list(set(urls))
            # time.sleep(10)
            continue
        response = get_response(url)
        extra_urls = parse_pages_list(response)
        # print(extra_urls)
        time.sleep(random.randint(10,12))
        urls += extra_urls
        urls = list(set(urls))
        # print(urls)
        insert_crawled_link(url)
        # print(urls)
        urls.remove(url)
        
    print(urls)
    print("end")
if __name__ == "__main__":
    # session = requests.Session()
    
    # data = session.get(url)
    # content = data.content.decode('utf-8')
    # response = Selector(text=content)
    # print(response.xpath('html'))
    main()