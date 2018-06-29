
from threading import Thread
from queue import Queue
import os
import json
import hashlib
from hashlib import md5
import re
import os
import json
import requests
from collections import Counter, defaultdict
from urllib.request import urlopen
import urllib.request
import time
from urllib.parse import urlparse
import http.client, sys
import collections



#===================== Class de xu ly gui request va ghi nhan code 302 trong truong hop webpage redirect
class ErrorHandler(urllib.request.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, hdrs):
        return(fp)


class RedirectHandler(urllib.request.HTTPRedirectHandler):
    """
    This currently only checks if the redirection netloc is 
    the same as the the netloc for the request.

    NOTE: this is very strict, as it will not allow redirections
          from 'example.com' to 'www.example.com' 
    """

    def http_error_302(self, req, fp, code, msg, headers):
        return None
    http_error_301 = http_error_303 = http_error_307 = http_error_302



#==================== Gui request trong Queue
def request(allow_redirect=False):
    try:
        args = [ErrorHandler]
        args.append(urllib.request.ProxyHandler({}))
        if not allow_redirect:
            args.append(RedirectHandler)
        opener = urllib.request.build_opener(*args)
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36')]
        return opener
    except Exception as error:
        return error

def do_request(url,method):
    args = [ErrorHandler]
    args.append(urllib.request.ProxyHandler({}))
    args.append(RedirectHandler)
    opener = urllib.request.build_opener(*args)
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36')]
    request = urllib.request.Request(url, method=method)
    response = opener.open(request,timeout=20)
    return response
                
def getStatus(fp_list):
    global org_url
    _response=None
    try:
        path=fp_list[0]['url']
        if len(path)>0 and path[0]!='/':
            path='/'+path
        complete_url=org_url+path
        _response = do_request(complete_url, method='HEAD')
        print("\x1b[1;32m\t\t+Checking URL \x1b[0;0m:[",complete_url,"-",_response.status,"]")
        if _response.status==200:
            _response = do_request(complete_url, method='GET')
        return _response
    except Exception as e:
        print("\033[1;31;40m\t\t+Error: ",e,fp_list[0]['url'],"\033[0m")

def createRespone(field,fp_list,_res):
    global found_url
    requested= defaultdict(list)
    requested[fp_list[0]['url']]=_res
    found_url[field].append(requested)

def doWork():
    while True:
        try:
            field,fp_list = q.get()
            _res = getStatus(fp_list)
            createRespone(field,fp_list,_res)
            q.task_done()
        except Exception as error:
            print("\033[1;31;40m\t\t+Error : ",error,fp_list[0]['url'],"\033[0m")
            q.task_done()

#============= Xu ly cac function de dua ra cac match fingerprints
def checkHomepageContent(ourl):
    try:
        url = urlparse(ourl)
        conn = http.client.HTTPConnection(url.netloc)   
        conn.request("GET", url.path)
        res = conn.getresponse()
        return res
    except Exception as error:
        print("\033[1;31;40m\t\t+Error: ",error)
        return None

def computeMD5hash(res):                        #luu md5 cua homepage va kiem tra xem no co tu dong redirect ve trong truong hop ko co khong
    max_file_size=100*1024*1024
    hash = hashlib.md5()
    total_read = 0
    while True:
        data = res.read(4096)
        total_read += 4096
        if not data or total_read > max_file_size:
            break
        hash.update(data)
    return hash.hexdigest()

def checkMD5CMS(response_list, fingerprints_matcher):
    hash_content={}                         #tao bien luu tru tat ca cac hash cua url tim duoc
    CMS=[]
    cms_added={}
    for response in response_list:
        for url_request, res in response.items():
            if res!= None and res.status==200:
                response=checkHomepageContent(res.url)
                if response==None:
                    continue
                _hash = computeMD5hash(response)
                for fp in fingerprints_matcher[url_request]:
                    if fp['match']==_hash:
                        if fp['name'] not in cms_added.keys():
                            cms_added[fp['name']]=[]
                            cms_added[fp['name']].append(fp['output'])
                        else:
                            cms_added[fp['name']].append(fp['output'])
    for key,value in cms_added.items():
        if len(value)==1:
            CMS.append(key+value[0])
        elif len(value)>1:
            output=CheckListDuplicate(value)
            if len(output)!=1:
                for version in output:
                    CMS.append(key)
            else:
                CMS.append(key)
    return CMS

def CheckListDuplicate(array_check):
    output=[]
    counter=collections.Counter(array_check)
    max=0
    for key,value in counter.items():
        if value>max:
            max=value
    for key,value in counter.items():
        if value ==max:
            output.append(key)
    return output

#================================== Check fingerprints with string and regex.

def is_matchstring(fingerprint,body):
    if 'match' in fingerprint.keys() and fingerprint['match'] in body:
        return True
    else:
        return False
def is_matchregex(fingerprint,body):
    regex = fingerprint["match"]
    output = fingerprint["output"] if 'output' in fingerprint else None
    matches = re.findall(regex, body)
    if len(matches):
        if "%" in output:
            result = output % matches[0]
            return result
        else:
            return ''
    else:
        return None


def checkFP(type_detect,fingerprint,body):
    if type_detect == 'string':
        if(is_matchstring(fingerprint,body)):
            return fingerprint['name']
        else:
            return None
    elif type_detect == 'regex':
        result=is_matchregex(fingerprint,body)
        if result != None:
            return fingerprint['name']+' '+result
        else:
            return None


def check_headerCMS(response_list, fingerprints_matcher): 
    #xu ly database trong CMS
    #kiem tra xem co de cap den code cua respone khong
    cms=[]
    for response in response_list:
        for url_request, res in response.items():
            for fp in fingerprints_matcher[url_request]:
                if res!=None:
                    for header in res.headers:
                        if header.lower()== fp['header'].lower():
                            if 'type' not in fp.keys() and 'regex' in fp.keys():        #hai cau dieu kien nay xu ly cho viec database khong co type
                                fp['type']='regex'
                                fp['match']=fp['regex']
                            elif 'type' not in fp.keys() and 'string' in fp.keys():
                                fp['type']='string'
                                fp['match']=fp['string']
                            output=checkFP(fp['type'],fp,res.headers[header])
                            if output!=None:
                                cms.append(output)
    return cms

#===========================================


def _check_string(found_url,_fingerprints):
    cms=[]
    found_cms=[]
    types=['string','regex']
    for _type in types:
        for response in found_url[_type]:
            for url_request, res in response.items():
                if res != None:
                    body=res.read().decode('utf-8')
                    for fp in _fingerprints[_type][url_request]:
                        output = checkFP(_type,fp,body)
                        if output!=None:
                            found_cms.append(output)
    found_cms=collections.Counter(found_cms)
    for found in found_cms.keys():
        cms.append(found)
    return cms

#============================================
def define_version(array_check):
    output=[]
    deleted=[]
    counter=collections.Counter(array_check)
    for key in counter.keys():
        for check in counter.keys():
            if key!=check and key in check:
                deleted.append(key)
    for key in counter.keys():
        if key not in deleted:
            output.append(key)
    return output

def redirect(url):
    try:
        opener=request(allow_redirect=True)
        response = opener.open(url,timeout=20)
        new_url = urlparse(response.geturl())
        new_loc = new_url.scheme + '://' + new_url.netloc
        return new_loc                                          # create an response object and add it to the cache
    except:
        print("\033[1;31;40mCan't connect to this website!\033[0m",url)
        return None


def run(url):
    global org_url,found_url
    found_url={}
    found_url['md5']=[]
    found_url['header']=[]
    found_url['string']=[]
    found_url['regex']=[]
    detected_cms=[]
    final_cms=[]
    result={}
    print("\n\n\033[0;37;41m *Detect CMS and its Version:\033[0m")
    if '://' not in url:
        url='http://'+url
    url=redirect(url)
    if url != None:
        org_url=url
        for catory in catories:
            print("\033[0;37;44m\t+Checking with ",catory,"\033[0m")
            for url,fp_list in _fingerprints[catory].items():
                while q.full():
                    print("\033[1;31;40m\t\t+Queue is full, Wait to Execute!\033[0m")
                    time.sleep(1)
                q.put((catory,fp_list))
            q.join()
        detected_cms.extend(checkMD5CMS(found_url['md5'],_fingerprints['md5']))
        detected_cms.extend(check_headerCMS(found_url['header'],_fingerprints['header']))
        detected_cms.extend(_check_string(found_url,_fingerprints))
        final_cms=define_version(detected_cms)
        if len(final_cms)==0:
            print("\033[0;37;42m+CMS Not found\033[0m")
        for cms in final_cms:
            print("\033[0;37;42m+CMS detected:\033[0m",cms)
            result[cms]=cms
    return result


#====================================initate variable
os.environ['http_proxy']=''
concurrent = 300
existed_url=[]
existed_path=[]
org_url=''
catories=['md5','string','header','regex']
found_url={}
for catory in catories:
    found_url[catory]=[]
#================================
path=os.getcwd()
path=path+'/cms/'       #get content in all file in folder data
_fingerprints={}                                #tao mot dict chua tat ca cac fingerprints co duoc
for filename in os.listdir(path):
    path_file=path+filename     #md5.header,string,...
    fingerprints_temp=defaultdict(list)            #tao mot dict temp chua cac noi dung fingerprint cua moi truong md5, string, regex hoac header
    for name in os.listdir(path_file):  #lay tat ca cac file json nhu wordpress,apache,....
        path_json=path_file+'/'+name
        with open(path_json, 'r') as f:
            data_dict = json.load(f)
            name=name.split('.json')[0]
            for fingerprints in data_dict:                #tao dict luu lai tat ca cac gia tri cua fingerprint de khong can phai load lai
                fingerprints['name']=name
                fingerprints_temp[fingerprints['url']].append(fingerprints)   #luu lai duoi dang {url:{}} nhu vay se xac dinh duoc cac url giong nhau
        f.close()
    _fingerprints[filename]=fingerprints_temp             #luu database vao fingerprints goc sau khi xet xong moi truong md5,string,...
    fingerprints_temp={}
print("done to save database")
#================================== Queue

q = Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()
