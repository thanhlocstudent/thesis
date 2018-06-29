from flask import Flask, render_template, request, json, make_response
import os
import shutil
import Crawl
import FindSubdomain
import stupid
import final_CMS
import json
import defaultLink
from urllib.parse import urlparse

crawlResult=None
platformResult=[]
findingResult=[]
cmsResult=[]
domainScan={}
domainScan['dns']=[]
domainScan['mx']=[]
domainScan['host']=[]



def run(_url,_listFeatures):
    global crawlResult,domainScan,cmsResult,platformResult,findingResult
    crawlResult=None
    platformResult=[]
    cmsResult=[]
    findingResult=[]
    domainScan={}
    domainScan['dns']=[]
    domainScan['mx']=[]
    domainScan['host']=[]
    current_directory = os.getcwd()
    filename=_url
    if 'http' in _url:
        parser = urlparse(_url)
        filename=parser.netloc
    directory=current_directory+'/static/database/'+filename
    if _url:
        if not os.path.exists(directory):
            os.makedirs(directory)  #Create scan directory
            nonexistfolder(_url,directory,_listFeatures)
            return crawlResult,domainScan,platformResult,cmsResult,findingResult
        else:
            existfolder(_url,directory,_listFeatures)
            return crawlResult,domainScan,platformResult,cmsResult,findingResult

def nonexistfolder(_url,directory,_listFeatures):
    global crawlResult,domainScan,cmsResult,platformResult,findingResult
    print("I'm doing")
    crawl = directory + '/crawl.json'
    domain = directory + '/domain.json'
    cms = directory+'/cms.json'
    platform = directory + '/platform.json'
    finding = directory + '/finding.json'
    for i in _listFeatures:
        if i == 'domain':
            domainScan =FindSubdomain.run(_url)
            with open(domain, 'w') as outfile:
                json.dump(domainScan, outfile)
        elif i == 'crawl':
            crawlResult = Crawl.main(_url)
            with open(crawl, 'w') as outfile:
                json.dump(crawlResult, outfile)
        elif i == 'platform':
            platformResult = stupid.run(_url)
            with open(platform, 'w') as outfile:
                json.dump(platformResult, outfile)
        elif i == 'cms':
            cmsResult = final_CMS.run(_url)
            with open(cms, 'w') as outfile:
                json.dump(cmsResult, outfile)
        elif i =='finding':
            findingResult = defaultLink.run(_url)
            with open(finding,'w') as outfile:
                json.dump(findingResult, outfile)

def existfolder(_url,directory,_listFeatures):
    global crawlResult,domainScan,cmsResult,platformResult,findingResult
    crawl = directory + '/crawl.json'
    domain = directory + '/domain.json'
    cms = directory+'/cms.json'
    platform = directory + '/platform.json'
    finding = directory + '/finding.json'
    for i in _listFeatures:
        if i == 'domain':
            print(domain)
            if os.path.exists(domain):
                with open(domain) as f:
                    domainScan = json.load(f)
            else:
                domainScan =FindSubdomain.run(_url)
                with open(domain, 'w') as outfile:
                    json.dump(domainScan, outfile)

        elif i == 'crawl':
            if os.path.exists(crawl):
                with open(crawl) as f:
                    crawlResult = json.load(f)
            else:
                crawlResult = Crawl.main(_url)
                with open(crawl, 'w') as outfile:
                    json.dump(crawlResult, outfile)

        elif i == 'platform':
            if os.path.exists(platform):
                with open(platform) as f:
                    platformResult = json.load(f)
            else:
                platformResult = stupid.run(_url)
                with open(platform, 'w') as outfile:
                    json.dump(platformResult, outfile)

        elif i == 'cms':
            if os.path.exists(cms):
                with open(cms) as f:
                    cmsResult = json.load(f)
            else:
                cmsResult = final_CMS.run(_url)
                with open(cms, 'w') as outfile:
                    json.dump(cmsResult, outfile)

        elif i=='finding':
            if os.path.exists(finding):
                with open(finding) as f:
                    findingResult = json.load(f)
            else:
                findingResult = defaultLink.run(_url)
                with open(finding, 'w') as outfile:
                    json.dump(findingResult, outfile)
