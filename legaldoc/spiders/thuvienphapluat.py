import scrapy
import pymysql
import pymysql.cursors
from scrapy.selector import Selector
import time
import re
import json
import random

def normalize(data):
    data = data.replace("\n"," ")
    data = data.replace("\r"," ")
    data = data.replace('"',"'")
    return data

def save_link(link):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        a = ""
    
    connection.commit()
    connection.close()
    return None

def striphtml(data):
    
    regex = re.compile(r'<[^>]+>')
    a = regex.sub('', data).strip()
    # a = a.encode("ascii","ignore").decode().strip()
    a = normalize(a)
    return a
def delete_between_tag(data,tag):
    regex = re.compile("<{} (.*?)</{}>".format(tag,tag))
    return regex.sub("",data).strip()
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
        # print(tds)
        content.append(tds)
    return content

def merge_paragraphs(paragraphs):
    new_para = [striphtml(doc) for doc in paragraphs]
    text = " ".join(new_para)
    return text

def split_appendix_and_content(container_text):
    table_split = container_text.split("</table>")
    content_p = table_split[0]+"</table>"+table_split[1]+"</table>"
    p_tags = Selector(text=content_p).css("p").getall()
    # appendix = "</table>".join(table_split[2:])
    appendix = []
    for i in range(2,len(table_split)):
        a_p = table_split[i]+"</table>"
        only_p = striphtml(delete_between_tag(a_p,"table"))
        table_content = extract_table(Selector(text=a_p))
        appendix.append({"text":only_p,"table":table_content})
    p_tags = []
    content = merge_paragraphs(p_tags)
    return content,appendix

def extract_data_from_single_page(response):
    div_content_doc = response.xpath('//div[@id="divContentDoc"]/div[@class="content1"]/div/div').get()
    tables = Selector(text=div_content_doc).xpath('//table')
    org,cou_name,doc_id,date = extract_date_and_org(tables[0])
    receiver, signer = extract_signer(tables[1])
    # appendix = []
    if len(tables) > 2:
        content,appendix = split_appendix_and_content(div_content_doc)
    else:
        p_tags = response.xpath('//div[@id="divContentDoc"]/div[@class="content1"]/div/div/p').getall()
        content = merge_paragraphs(p_tags)
        appendix = []
    
    # str_app = json.dumps(appendix)
    str_app = str(appendix)
    doc_object = {
        "org":striphtml(org),        
        "cou":striphtml(cou_name),
        "doc_id":striphtml(doc_id),
        "date":striphtml(date),
        "content":content,
        "receiver":striphtml(receiver),
        "signer":striphtml(signer),
        "appendix":normalize(str_app)
    }
    return doc_object

def save_to_database(data):
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        # try:
        
        org = data["org"]
        # print(org)
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
            sql = "insert into doc(doc_id,org,date,receiver,signer,content,appendix,domain) value ('{}','{}','{}','{}','{}',\"{}\",\"{}\",'thuvienphapluat')".format(doc_id,org,date,receiver,signer,content,appendix)
            print(sql)
            cursor.execute(sql)
            
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

def clear_crawled_link():
    connection =  get_db_connection("localhost",'root','12345678','legal')
    with connection.cursor() as cursor:
        sql = "delete from link where id=1"
        cursor.execute(sql)
        results = cursor.fetchall()
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
        crawled_link = get_crawled_link()
        if crawled_link is None:
            doc_links = self.get_single_doc_links(response)
            for link in doc_links:
                time.sleep(random.randint(23,30))
                yield scrapy.Request(url=link, callback=self.parse_single_page)
            page_links = self.get_next_pages_links(response)
            for link in page_links:
                update_crawled_link(link)
                time.sleep(random.randint(23,30))
                yield scrapy.Request(url=link, callback=self.parse_pages_list)
        else:
            clear_crawled_link()
            yield scrapy.Request(url=crawled_link, callback=self.parse_pages_list)

    def parse_single_page(self,response):
        doc = extract_data_from_single_page(response)
        save_to_database(doc)