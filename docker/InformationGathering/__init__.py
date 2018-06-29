from flask import Flask, render_template, request, json, make_response
import os
import shutil
import handling
from urllib.parse import urlparse

app = Flask(__name__)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r
@app.route("/")
def main():
    return render_template("index.html")

@app.route("/", methods=['POST'])
def scanDemo():
    _url = request.form['scanDomain']		#List features will be used.
    _All = ["domain", "crawl", "platform", "cms", "finding", "takeover"] #Get all list features from Post request
    _listFeatures = []
    for key in request.form.items():
        if key[0] != "scanDomain":
            _listFeatures.append(key[0])
    if 'myCheckFF' in _listFeatures:
        _listFeatures=_All
    print("__init:",_url )
    filename=_url
    if 'http' in _url:
        parser = urlparse(_url)
        filename=parser.netloc

    crawlResult,domainScan,platformResult,cmsResult,findingResult=handling.run(_url,_listFeatures)
    return render_template("result.html",ahihi=crawlResult,dns=domainScan['dns'],mx=domainScan['mx'],host=domainScan['host'],plat=platformResult,cms=cmsResult,finding=findingResult,dir=filename,feature=_listFeatures)

@app.route('/graphview/<filename>')
def view(filename):
    filename='./database/'+filename+'/flare.json'
    #directory='static/database/'+directory+'/flare.json'
    return render_template('graphview.html',target=filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True,port=5000)
