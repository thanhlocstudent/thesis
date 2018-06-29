from urllib.parse import urlparse
from threading import Thread
import http.client, sys
from queue import Queue
import os
import json
import hashlib
from hashlib import md5
import re
from datetime import datetime
import time
import urllib.request
import requests
import json
import http.client
import urllib.parse

concurrent = 300
existed_url=[]
final_url=[]
headers={
    'User-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
}

def doWork():
    while True:
        try:
            url = q.get()
            status= getStatus(url)
            if status!=None:
                doSomethingWithResult(status, url)
            q.task_done()
        except Exception as error:
            print("\033[1;31;40m\t\t+Error: ",error,"\033[0m")
            q.task_done

def getStatus(ourl):
    try:
        url = urlparse(ourl)
        conn = http.client.HTTPConnection(url.netloc,timeout=20)   
        conn.request("HEAD", url.path)
        res = conn.getresponse()
        print("\x1b[1;32m\t\t+Checking URL \x1b[0;0m:[",ourl,"-",res.status,"]")
        return res.status
    except Exception as e:
        print("\033[1;31;40m\t\t+Error: ",e,ourl,"\033[0m")
        return None

def doSomethingWithResult(status, url):
    global existed_url
    if status==200:
        existed_url.append(url)
def CheckListDuplicate(urls):
    url_nonduplicate=[]
    for url in urls:
        if url not in url_nonduplicate:
            url_nonduplicate.append(url)
    return url_nonduplicate
def SendAPI():
    global final_url
    while True:
        try:
            url=p.get()
            api_url = 'http://207.148.67.180/not_exist_page_calculation/?target_url='
            complete_url=api_url+url
            r = requests.get(complete_url)
            body = r.text
            _dict = json.loads(body)
            if not _dict['page_is_404']:
                final_url.append(url)
            p.task_done()
        except Exception as error:
            print("\033[1;31;40m\t\t+Error: ",error,"\033[0m")
            p.task_done()
def computeMD5hash(my_string): #luu md5 cua homepage va kiem tra xem no co tu dong redirect ve trong truong hop ko co khong
    my_string=str(my_string)
    m = hashlib.md5()
    m.update(my_string.encode('utf-8'))
    return m.hexdigest()

def checkHomepageContent(ourl):
    try:
        url = urlparse(ourl)
        conn = http.client.HTTPConnection(url.netloc)   
        conn.request("GET", url.path)
        res = conn.getresponse()
        data1 = res.read()
        return data1
    except Exception as error:
        print("\033[1;31;40m\t\t+Error: ",error,"\033[0m")
        pass
def _clean_page(page):
    try:
        page = re.sub(b'(\d?\d:?){2,3}', b'',page)
        page = re.sub(b'AM', b'',page, flags=re.IGNORECASE)
        page = re.sub(b'PM', b'',page, flags=re.IGNORECASE)
        page = re.sub(b'(\d){13}', b'', page) # timestamp

        # date with 4 digit year
        page = re.sub(b'(\d){8}', '',page)
        page = re.sub(b'\d{4}-\d{2}-\d{2}', b'',page)
        page = re.sub(b'\d{4}/\d{2}/\d{2}', b'',page)
        page = re.sub(b'\d{2}-\d{2}-\d{4}', b'',page)
        page = re.sub(b'\d{2}/\d{2}/\d{4}', b'',page)

        # date with 2 digit year
        page = re.sub( b'(\d){6}', '',page)
        page = re.sub( b'\d{2}-\d{2}-\d{2}', b'',page)
        page = re.sub( b'\d{2}/\d{2}/\d{2}', b'',page)
        
        # links and paths
        page = re.sub( b'/[^ ]+',  b'', page)
        page = re.sub( b'[a-zA-Z]:\\[^ ]+',  b'', page)
        return page
    except:
        pass

def removeUrl(mydict):
    seen = mydict               #tao mot dict copy tu dict thu duoc
    tmp=[]                      #tao bien tmp chua cac url co ma hash giong nhau
    delete_key=[]               #tao bien chua tat ca cac url can loai bo vi duplicate do co ma hash giong nhau
    for key in mydict.keys():
        value = mydict[key]
        #print(value)
        tmp.append(key)         #them key vao tmp de so sanh chieu dai trong truong hop co hash giong
        for k in seen.keys(): 
            if(value==seen[k]) and (key != k): # neu url co hash giong va khong phai key dang xet thi cho vao mang chua url hash giong nhau
                tmp.append(k)
        if(len(tmp)>1):         #neu dict >1 nghia la co url giong nhau
            min_length=min(tmp, key=len)    #tim key co chieu dai string ngan nhat  
            for key_del in tmp:             #duyet tat ca url trong dict chua url co hash giong nhau
                if key_del!=min_length:     #neu khac url co chieu dai nho nhat thi them vao dict chua url can loai bo
                    delete_key.append(key_del)
        tmp=[]                              #reset lai dict de thuc hien lan duyet sau
    for key in delete_key:
        mydict.pop(key,None)
    return mydict

def MD5detect(scheme,domain):
    dict_url={}
    error_page=scheme+'://'+domain+'/errorpage.txt'
    _page404=1
    try:
        _page404=computeMD5hash(_clean_page(checkHomepageContent(error_page))) #tinh hash cua homepage, truoc do loai bo cac tham so dong nhu ngay gio
    except:
        pass
    for url in existed_url:
        _hash = computeMD5hash(_clean_page(checkHomepageContent(url))) #tinh hash moi url tim duoc
        if _hash!=_page404:                               
            dict_url[url]=_hash     #tao 1 dict chua tat ca cac url tim duoc cung voi hash tuong ung.
    _dict=removeUrl(dict_url)
    for key in _dict.keys():
        final_url.append(key)

q = Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()

p = Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=SendAPI)
    t.daemon = True
    t.start()

def run(url):
    global existed_url,final_url
    existed_url=[]
    result={}
    final_url=[]
    print("\n\n\033[0;37;41m *Checking Sensitive File/Folder :\033[0m")
    try:
        urls=[]
        if 'http' not in url:
            url='http://'+url
        res = requests.get(url,headers=headers,allow_redirects=True,timeout=25)
    except Exception as error:
        print("\033[1;31;40m\t\t+Error: ",error)
        return result
    scheme = urlparse(res.url).scheme
    domain = urlparse(res.url).netloc
    with open('default_links.txt') as f:
        for lines in f:
            lines = lines.strip()
            target= scheme+'://'+domain+lines
            urls.append(target)
    try:
        print("\033[0;37;44m\t+Detect existed Link :\033[0m")
        for url in urls:
            while q.full():
                time.sleep(10)
                print("\033[1;31;40m\t\t+Queue is full, Wait to Execute!\033[0m")
            q.put(url.strip())
        q.join()
        existed_url=CheckListDuplicate(existed_url)
        print("\033[0;37;44m\t+Checking to decrease False positive :\033[0m")
        match=re.findall('\d+.\d+.\d+.\d+', domain)
        print(match)
        if(match):
            MD5detect(scheme,domain)
        else:
            for url in existed_url:
                p.put(url)
            p.join()
        if len(final_url)==0:
            print("\033[0;37;42m+No found any Sensitive URL\033[0m")
        for url in final_url:
            print("\033[0;37;42m+Sensitive URL detected:\033[0m",url)
            result[url]=url
        return result
    except Exception as error:
        print("\033[1;31;40m\t\t+Error: ",error,"\033[0m")
        return result
