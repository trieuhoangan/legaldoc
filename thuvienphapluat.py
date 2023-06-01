import scrapy
import pymysql
import pymysql.cursors
from scrapy.selector import Selector
import re
import json
import random
import time
import sys
from scrapy.crawler import CrawlerProcess,CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
def striphtml(data):
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
    appendix = []
    if len(tables) > 2:
        for i in range(2,len(tables)):
            appendix.append(extract_table(tables[i]))
    p_tags = response.xpath('//div[@id="divContentDoc"]/div[@class="content1"]/div/div/p').getall()
    content = merge_paragraphs(p_tags)
    str_app = json.dumps(appendix)
    doc_object = {
        "org":striphtml(org),        
        "cou":striphtml(cou_name),
        "doc_id":striphtml(doc_id),
        "date":striphtml(date),
        "content":content,
        "receiver":striphtml(receiver),
        "signer":striphtml(signer),
        "appendix":str_app
    }
    return doc_object

def save_to_database(data):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        # try:
        org = data["org"]
        doc_id = data["doc_id"]
        date = data["date"]
        content = data["content"]
        receiver = data["receiver"]
        signer = data["signer"]
        appendix = data["appendix"]
        sql = 'select * from doc where doc_id="{}"'.format(doc_id)
        cursor.execute(sql)
        results = cursor.fetchall()
        if len(results) == 0:
            sql = 'insert into doc(doc_id,org,date,receiver,signer,content,appendix,domain) value ("{}","{}","{}","{}","{}","{}","{}","thuvienphapluat")'.format(doc_id,org,data,receiver,signer,content,appendix)
            cursor.execute(sql)
            
        # except:
        #     print("error")
        connection.commit()
    connection.close()  
class ThuvienphapluatSpider(scrapy.Spider):
    name = 'thuvienphapluat'
    allowed_domains = ['thuvienphapluat.vn']
    start_urls = ["https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword=&area=0&match=True&type=0&status=0&signer=0&sort=1&lan=1&scan=0&org=0&fields=&page=1"]
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_pages_list)
    def get_single_doc_links(self,response):
        a =response.xpath('//div[@id="block-info-advan"]/div')[1]
        b0 = a.xpath('//div[@class="content-0"]/div[@class="left-col"]/div[@class="nq"]/p[@class="nqTitle"]/a/@href').getall()
        b1 = a.xpath('//div[@class="content-0"]/div[@class="left-col"]/div[@class="nq"]/p[@class="nqTitle"]/a/@href').getall()
        c =[]
        c.extend(b0)
        c.extend(b1)
        return c
    def get_next_pages_links(self,response):
        domain = "https://thuvienphapluat.vn/page/"
        links = response.xpath('//div[@class="cmPager"]/a/@href').getall()
        page_links = []
        for link in links:
            link = domain+link 
            page_links.append(link)
        return page_links
    def parse_pages_list(self,response):
        doc_links = self.get_single_doc_links(response)
        for link in doc_links:
            yield scrapy.Request(url=link, callback=self.parse_single_page)
        page_links = self.get_next_pages_links(response)
        for link in page_links:
            yield scrapy.Request(url=link, callback=self.parse_pages_list)
        
    def parse_single_page(self,response):
        doc = extract_data_from_single_page(response)
        save_to_database(doc)

def sleep(_, duration=90):
    duration = random.randint(10,15)
    print(f'sleeping for: {duration}')
    time.sleep(duration)  # block here


def crawl(runner):
    d = runner.crawl(ThuvienphapluatSpider)
    d.addBoth(sleep)
    d.addBoth(lambda _: crawl(runner))
    return d


def loop_crawl():
    runner = CrawlerRunner(get_project_settings())
    crawl(runner)
    reactor.run()

if __name__=="__main__":
    loop_crawl()