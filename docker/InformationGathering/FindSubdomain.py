import json
from collections import defaultdict
from dnsdumpster.DNSDumpsterAPI import DNSDumpsterAPI
from urllib.parse import urlparse
from queue import Queue
from threading import Thread
import http.client, sys
import time
import requests
import urllib.request
import urllib.parse
import socket
import re

def check_domain(url):
	try:
		try:
			req = urllib.request.Request(url)
			with urllib.request.urlopen(req, timeout=10) as f:
				data = f.read().decode('utf-8')
				title = re.findall(r'<title>\s*(.*)\s*</title>', data)[0]
				existed_subdomain.append(url)
		except Exception as error:
			return error
	except Exception as error:
		return error

def findomain(target,results):
	json_data=results
	visualize_graph={}
	visualize_graph['name']=target
	visualize_graph['children']=[]
	names=['dns','mx']
	pos=0
	for name in names:
		visualize_graph['children'].append({})
		visualize_graph['children'][pos]['name']=name
		children=[]
		temp_dns={}
		dns=json_data[name]
		for i in range(len(dns)):
			children.append({})
		for i in range(len(children)):
			children[i]['name']=dns[i]['domain']
			temp=[]
			for j in range(0,2):
				temp.append({})
			m=0
			for key,value in dns[i].items():
				if key not in ['domain','as','reverse_dns','header','country']:
					string = key+' : '+value
					temp[m]['name']= string
					temp[m]['size']=0
					m=m+1

			children[i]['children']=temp
		visualize_graph['children'][pos]['children']=children
		pos=pos+1
	visualize_graph['children'].append({})
	visualize_graph['children'][2]['name']='host'
	tmp=[]
	ips=[]
	hosts = json_data['host']
	for i in range(len(hosts)):
		ip = hosts[i]['ip']
		if ip not in ips:
			ips.append(ip)
	for i in range(len(ips)):
		ip = ips[i]
		tmp.append({})
		tmp[i]['name']='['+ ip+']'
		temp_ips=[]
		domain_host=[]
		pos = 0
		for j in range(len(hosts)):
			if hosts[j]['ip'] == ip:
				domain_host.append({})
				domain_host[pos]['name']=hosts[j]['domain']
				domain_host[pos]['size']=0
				pos=pos+1
		tmp[i]['children']=domain_host
	visualize_graph['children'][2]['children']=tmp
	directory='./static/database/'+target+'/flare.json'
	with open(directory, 'w') as outfile:
		json.dump(visualize_graph,outfile)
	return json_data


def doWork():
	while True:
		try:
			url = q.get()
			check_domain(url)
			q.task_done()
		except Exception as error:
			q.task_done()
			print(error)

def bruteforce(scheme,base_url):
	urls=[]
	with open('subdomains.txt') as f:
		for lines in f:
			lines = lines.strip()
			target= scheme+'://'+lines+'.'+base_url
			urls.append(target)
	for url in urls:
		while q.full():
			time.sleep(1)
		q.put(url.strip())
	q.join()


def run(target):
	global existed_subdomain
	existed_subdomain=[]
	print("\n\n\033[0;37;41m *Find Subdomain :\033[0m",target)
	json_data={'dns':[],'mx':[],'host':[]}
	scheme='http'
	if 'http' in target:
		parser = urlparse(target)
		target=parser.netloc
		scheme = parser.scheme
	filename=target
	target='.'.join(target.split('.')[1:])
	print(target)
	try:
		results = DNSDumpsterAPI().search(target)
		if not type(results)==list:
			json_data=results['dns_records']
		else:
			print("\033[1;31;40m\t+Notfound\033[0m")
		if len(json_data['host'])<2:
			bruteforce(scheme,target)
		for domain in existed_subdomain:
			netloc = urlparse(domain).netloc
			exist = False
			for domain in json_data['host']:
				if netloc == domain['domain']:
					exist=True
			if not exist:
				tmp={}
				tmp['domain']=netloc
				tmp['ip']=socket.gethostbyname(netloc)
				tmp['country']=''
				tmp['provider']=''
				tmp['reverse_dns']=''
				tmp['as']=''
				json_data['host'].append(tmp)
		json_data=findomain(filename,json_data)
		print(json_data)
		print("\033[0;37;42m+Find Subdomain completed\033[0m")
		return json_data
	except Exception as error:
		print("\033[1;31;40m\t\t+Error: ",error,"\033[0m")
		return json_data

location=''
existed_subdomain=[]
concurrent=200
q = Queue(concurrent * 2)
for i in range(concurrent):
	t = Thread(target=doWork)
	t.daemon = True
	t.start()