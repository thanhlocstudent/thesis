import requests
import urllib.request
import urllib.parse
import re
import argparse
import threading
import multiprocessing
import http.client
import urllib.parse
from urllib.parse import urlparse
from queue import Queue
from threading import Thread
from collections import defaultdict
import sys
import json
import time
import os


#================global variable
img_ext =['png','jpg','gif','ico','bmp','css','swf','mp3','mp4','pdf','xdoc','db']
crawled_url=[]
url_visited=[]
url_scanned=[]
url_nottext=[]
different_site=[]
location=''

class ErrorHandler(urllib.request.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, hdrs):
        return(fp)

class UnknownHostName(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return "Unknown host: %s" % (self.url,)

class RedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.request.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        infourl.headers['Location']=headers['location']
        return infourl
    http_error_301 = http_error_303 = http_error_307 = http_error_302

#=====================================
def _get_urls(response):
    regexes = ['src="(.+?)"', "src='(.+?)'",'href="(.*?)"',"href='(.*?)'",'src:url\((.*?)\)','url\((.*?)\)']
    urls = set()
    for regex in regexes:
        for match in re.findall(regex, response):
            if match not in urls:
                urls.add(match)
    return urls

def detect_links(url_path,_domainName,_scheme,path):
    global different_site
    crawl = set() #tao list chua url
    url_org=_scheme +"://"+_domainName                  #url orginal
    for url in url_path:
        if url[0:2]=='//':                              #Neu bat dau bang '//' nghia la no dang truy van den mot trang web khac
            url='http'+url
        if ('javascript:' in url) or ('&amp' in url) or (';amp' in url) or ('mailto' in url):          #neu no khong cung domain thi khong kiem tra
            pass
        elif url!='' and ("http" not in url) and ('#' not in url) :
            if path.count('/')<=1:
                addfolder=''
            else:
                addfolder=path[0:path.rfind('/')]
            if url[0] == '/':
                target=url_org+url
            else:
                target=url_org+addfolder+'/'+url
            target=encode(target)                         #encode url truoc khi add vao list crawl
            crawl.add(target)
            try:
                tmp=url.split('/')
                if len(tmp)>1:                 
                    for i in range(0,len(tmp)-1):       #duyet tu 1 den so luong folder cua url, tao vong loop de luu folder, folder con,... vidu luu 1: img, 2: img/abc
                        folder=''                         #tao bien luu folder
                        for x in range(0,i+1):
                            if tmp[x]!='':          
                                folder+='/'+tmp[x]
                            new_url = url_org + folder+'/'    #cai nay chu yeu duyet may cai thu muc xem co bi index of directory hay khong
                            crawl.add(new_url)
            except:
                pass
        elif url!='' and "http" in url:
            parser=urllib.request.urlparse(url)
            name= parser.netloc
            directory = parser.path
            tmp=directory.split('/')
            add_pre='www.'+name
            if (name==_domainName or add_pre==_domainName):
                url=encode(url)
                crawl.add(url)
                try:
                    directory = parser.path
                    tmp=directory.split('/')
                    if len(tmp)>2:                 
                        for i in range(1,len(tmp)-1):       #duyet tu 1 den so luong folder cua url, tao vong loop de luu folder, folder con,... vidu luu 1: img, 2: img/abc
                            folder=''                         #tao bien luu folder
                            for x in range(1,i+1):          
                                folder+='/'+tmp[x]
                                new_url = parser.scheme + '://' + parser.netloc + folder+'/' #tuong tu xet folder directory
                                crawl.add(new_url)
                except:
                    pass
            elif url not in different_site and re.findall('http.*:\/\/.+\..+\..*', url):
                different_site.append(re.findall("http.*:\/\/.+\..+\..*", url)[0])
    return crawl

def encode(target=''):
    url = target
    url = urllib.parse.urlsplit(url)
    url = list(url)                                     #convert dict to list to use in other function
    url[2] = urllib.parse.quote(url[2])                 #encode the path
    url = urllib.parse.urlunsplit(url)
    return url

#====================================================

def backup_find(url):
    #print("Before backup:" +url)
    none_name=False
    if url.split('/')[-1]:                              #Getting file name from url if it not exist,
        file_name=url.split('/')[-1]
    else:
        none_name=True                                   #detect if it has no filename
        file_name="index.php"
    if '?' in file_name:
        file_name=file_name.split('?')[0]
    elif '&' in file_name:
        file_name=file_name.split('&')[0]
    file_ext=file_name.split('.')[1]#Getting the extension from filename
    file_noext=file_name.split('.')[0]#name without extesion
    files = [file_name, "%s.tar"%(file_noext), "%s.rar"%(file_noext), "%s.zip"%(file_noext), "%s.txt"%(file_noext)]
    files += ["%s.old"%(file_name), "%s~"%(file_name),"%s.bak"%(file_name), "%s.tar.gz"%(file_noext)]
    files += ["%s-backup.%s"%(file_noext, file_ext), "%s-bkp.%s"%(file_noext, file_ext), "backup-%s.%s"%(file_noext, file_ext)]
    files += [".%s.%s.swp"%(file_noext, file_ext), "%s.%s"%(file_noext, file_ext)+"s", "_%s.%s"%(file_noext, file_ext)]
    files += ["%s2.%s"%(file_noext, file_ext), "%s.%s_"%(file_noext, file_ext), "%s.%s.gz"%(file_noext, file_ext)]
    files += ["%s_old.%s"%(file_noext, file_ext)] 
    for name in files:
        try:
            if(none_name==True):
                new_url=url+name
            else:
                name_org=url.split('/')[-1]#Getting the orginal name of file
                new_url = url.replace(name_org, name) #replace the filename in the original url
            request = requests.get(new_url, headers=headers, verify=True, timeout=3)
            if request:
                backup_link.add(new_url)
        except Exception:
            continue
def CheckListDuplicate(urls):
    url_nonduplicate=[]
    for url in urls:
        if url not in url_nonduplicate:
            url_nonduplicate.append(url)
    return url_nonduplicate

#=====================================================
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
        print("\033[1;31;40m\t\t\t+Error: ",error,"\033[0m")
        return error

def do_request(url,method):
    try:
        opener=request()
        _request = urllib.request.Request(url, method=method)
        response = opener.open(_request,timeout=10)
        return response
    except Exception as error:
        print("\033[1;31;40m\t\t\t+Error: ",error,url,"\033[0m")
#=====================================================

def redirect(url):
    try:
        opener=request(allow_redirect=True)
        response = opener.open(url,timeout=10)
        new_url = urlparse(response.geturl())
        new_loc = new_url.scheme + '://' + new_url.netloc+new_url.path
        return new_loc                                          # create an response object and add it to the cache
    except Exception as error:
        print("\033[1;31;40mCan't connect to this website!\033[0m",url)
        return None 
#=====================================================

def url_parser(url):
    parser = urllib.request.urlparse(url)
    scheme = parser.scheme
    full_domain = parser.netloc
    _path= parser.path
    return scheme, full_domain, _path
#======================================================

def doWork():
    global crawled_url
    global url_scanned
    global img_ext
    global url_nottext
    while True:
        url = q.get()
        try:
            if url not in crawled_url and url not in url_scanned:
                response= do_request(url,'HEAD')
                status_code = response.status
                url_scanned.append(url)
                if '../' in url and status_code==400:
                    q.put(url.replace('../',''))
                elif './' in url and status_code==400:
                    q.put(url.replace('./',''))
                if status_code==302 and response.headers['Location']!=location:
                    crawled_url.append(url)
                    url_nottext.append(url)
                    parser=urllib.request.urlparse(url)
                    domain = parser.netloc
                    scheme = parser.scheme
                    name=response.headers['Location']
                    if 'http' in name and urllib.request.urlparse(name).netloc == domain and name not in url_scanned and url not in crawled_url:
                        response= do_request(name,'HEAD')
                        status_code = response.status
                        url_scanned.append(url)
                    else:
                        if name.startswith('/'):
                            url=scheme+'://'+domain+name
                        else:
                            url=scheme+'://'+domain+'/'+name
                        if url not in crawled_url and url not in url_scanned:
                            response= do_request(url,'HEAD')
                            status_code = response.status
                            url_scanned.append(url)

                if status_code==200:                        #chi them vao crawl trong truong hop respone-200
                    if '../' in url:
                        delete=url.count('../')
                        parent_folder=url.split('/')
                        for i in range(3,len(parent_folder)):
                            if parent_folder[i]=='..':
                                for j in range(i-delete,i+delete):
                                    url=url.replace(parent_folder[j]+'/','')
                    elif './' in url:
                        url=url.replace('./','')
                    crawled_url.append(url)
                    if response.headers['Content-Type']:
                        if ('text' not in response.headers['Content-Type']) and ('javascript' not in response.headers['Content-Type']):
                            url_nottext.append(url)
                    else:
                        url_nottext.append(url)
            q.task_done()
        except Exception as error:
            print("\033[1;31;40m\t\t\t+Error: ",error,url,"\033[0m")
            q.task_done()

#======================================================

def visit():
    global array_queue
    global url_scanned
    global url_nottext
    global url_visited
    global crawled_url
    while True:
        try:
            target=p.get()
            print("\x1b[1;33m\t+HTML Source code from: \x1b[0;0m",target)
            response=do_request(target,'GET')
            body=response.read()
            try:
                _body=body.decode('utf-8')
            except:
                _body=''
            urls= _get_urls(_body)
            scheme,domain_name,path= url_parser(target)
            url_path=detect_links(urls,domain_name,scheme,path)
            first_detect=True        
            for link in url_path:
                if link not in url_scanned:
                    if first_detect:
                        first_detect=False
                        print("\x1b[1;32m\t\t+Links detected: \x1b[0;0m")
                    print("\t\t\t+",link)
                    while q.full():
                        print("\033[1;31;40m\t\t+Queue is full, Waiting...!\033[0m")
                        time.sleep(1)
                    q.put((link))
            while not q.empty():
                print("\033[1;31;40m\t\t+Queue is not empty, Waiting...!\033[0m")
                time.sleep(1)
            q.join()
            url_visited.append(target)                       #Neu Phat hien url moi trong target, kiem tra xem co trong list crawl khong, neu ko thi de quy
            url_path=list(url_path)                          #Them target vao url_visisted
            if len(url_path)>=1:                              #neu khong co url thi khong lam gi het
                for link_inside in url_path:
                    if link_inside in url_nottext:
                        url_visited.append(link_inside)
                    elif link_inside not in url_visited and link_inside in crawled_url:
                        array_queue.append(link_inside)
            p.task_done()
        except Exception as error:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("\033[1;31;40m\t\t+Error: ",error,target,exc_type, fname, exc_tb.tb_lineno,"\033[0m")
            p.task_done()

#=====================================================


#=====================================================
def create_treelist(urls):
    paths=[]
    list_tree = defaultdict(list)
    for url in urls:                        #khong su dung ca url ma chi su dung path de su ly don gian hon
        parser = urlparse(url)              
        paths.append(parser.path)           
    max_len=0                               #tinh so luong folder nhieu nhat ma ghi nhan duoc
    for path in paths:                      
        tmp=path.split('/')                 
        if len(tmp)>max_len:
            max_len=len(tmp)
        for i in range(1,len(tmp)-1):       #duyet tu 1 den so luong folder cua url, tao vong loop de luu folder, folder con,... vidu luu 1: img, 2: img/abc
            name=''                         #tao bien luu folder
            for x in range(0,i+1):          
                if x!=0:
                    name+='/'+tmp[x]
            if name not in list_tree[i] and '.html' not in name:    # neu folder da ton tai thi khong luu nua
                list_tree[i].append(name)
    return list_tree,max_len
def create_treeview(urls,tree_list):
    list_view = defaultdict(list)                           #thuc hien tuong tu, create_treelist de luu url cho tung ten folder, can parser.query de lay day du luong tham so
    paths=[]
    for url in urls:
        parser = urlparse(url)
        netloc=parser.netloc
        paths.append(url[(url.index((netloc))+len(netloc)):])
    for path in paths:
        tmp=path.split('/')
        if len(path)>250:
            continue
        if len(tmp)==2:                                     #neu chieu dai bang 2 tuc la khong co folder thi se duoc them vao truc tiep voi key la homepage
            list_view['homepage'].append(path)
        else:
            for detected_dir in tree_list[len(tmp)-2]:      #Xac dinh so luong folder cua url va duyet cac folder co so luong tuong ung trong tree ten folder 
                if detected_dir in path:                    #neu ten folder nam trong url thi dua no vao va dung lai
                    list_view[detected_dir].append(path.replace(detected_dir,''))
                    break
    return list_view

def arrange(tree_list,max_len,tree_view):
    global different_site
    final=defaultdict(list)
    tree=defaultdict(list)
    tmp={}
    '''
    tree_list la mang chua cac ten folder dau tien, folder thu hai: vi du 1: /img/ , 2: /img/abc/
    tree_view la dict cac url ung voi tung tung folder, vi du: '/img/' : /img/a.png
    max_len-2 la so luong folder nhieu nhat : vi cai dau tien la '' va cai cuoi cung la ten file hoac ''
    '''
    for i in range(max_len-2,0,-1):                     
        for key in tree_list[i]:                #Duyet tu so luong folder nhieu nhat den folder it nhat
            if (i-1)==0:                        #Neu no la parent folder thi chi can them nhung url co duoc vao do
                final[key].extend(tree_view[key])
            else:
                delete=False                            #tao bien delete de break
                final[key].extend(tree_view[key])       #Lay tat ca url trong folder hien tai
                for j in range(i-1,0,-1):               #Duyet tat ca cac folder cha cua no
                    for merge in tree_list[j]:          
                        if merge == key[0:len(merge)]:  #Neu no nam trong folder cha
                            tmp={}                      #tao mot bien dict luu lai ten folder va cac url tuong ung cua no
                            tmp[key]=final[key]
                            final[merge].append(tmp)    # them bien dict nay vao folder cha cua no
                            delete=True                 #tao bien break de no khong can duyet voi cac folder cha khac
                            break;
                    if delete==True:
                        break
    for key in tree_list[1]:                            #sau khi thuc hien, chi can lay folder goc, se co tat ca folder con
        tree[key]=final[key]
    tree['homepage']=tree_view['homepage']              #lay tat ca url khong nam trong bat ki folder nao
    tree['different_site']=different_site
    return tree

def Crawl_view(crawled_url):
    tree={}
    tree_array,max_len=create_treelist(crawled_url)
    tree_view=create_treeview(crawled_url,tree_array)
    tree=arrange(tree_array,max_len,tree_view)
    return tree

def sortAlphabet(sort):
    for key, values in sort.items():
        try:
            for value in values:
                if type(value) is dict:
                    sortAlphabet(value)
                else:
                    values.sort()
        except:
            pass
    return sort

def detect_404(target):
    global location
    target=target+'/this_is_404_page'
    response= do_request(target,'HEAD')
    status_code = response.status
    if status_code == 302:
        location = response.headers['Location']

def main(target):
    global location
    global array_queue,crawled_url,different_site,url_nottext,url_scanned,url_visited
    print("\n\n\033[0;37;41m *Web Application Crawler :\033[0m")
    tree={}
    location=''
    tree_final={}
    array_queue=[]
    crawled_url=[]
    url_visited=[]
    url_scanned=[]
    url_nottext=[]
    different_site=[]
    if '://' not in target:
        target='http://'+target
    target = redirect(target)
    detect_404(target)
    if target!=None:
        array_queue.append(target)
        while len(array_queue)>0:
            count = len(array_queue)
            _len = 200
            while not p.empty() and not q.empty():
                sleep(1)
            if count <200: _len = count
            for i in range(_len):
                p.put(array_queue[i])
            p.join()
            array_queue=array_queue[_len:]
            array_queue=CheckListDuplicate(array_queue)
            p.join()
        crawled_url=CheckListDuplicate(crawled_url)
        print("+Total link crawled : ", len(crawled_url))
        print("+Total file/image : ",len(url_nottext))
        tree=Crawl_view(crawled_url)
        tree_final=sortAlphabet(tree)
    return json.dumps(tree_final)

array_queue=[]
concurrent = 200
pointer=0
q = Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()

p = Queue(concurrent * 2)
for i in range(concurrent):
    thread = Thread(target=visit)
    thread.daemon = True
    thread.start()
