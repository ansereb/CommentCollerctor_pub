import flask
import comment_collector as cc
import io
import base64
import os
import json
from InstagramAPI import InstagramAPI
import configparser
import random, time

app = flask.Flask(__name__)
#Credentials from config
configPath= os.path.join(os.path.dirname(os.path.realpath('__file__')), 'credentials.cfg')
parser=configparser.ConfigParser()
youtubeKey=''
random.seed(time.time())
youtubeKeyIndex=random.randint(0, 4)
instagramEmail=''
instagramPassword=''
tiktokLogin=''
tiktokPassword=''
facebookLogin=''
facebookPassword=''

def getYoutubeCredentials():
    parser.read_file(open('credentials.cfg', 'r'))
    global youtubeKey
    global youtubeKeyIndex
    youtubeKeys=parser.get('Youtube', 'KEY').split()
    youtubeKey=youtubeKeys[youtubeKeyIndex]
    youtubeKeyIndex=(youtubeKeyIndex+1)%5

def getInstagramCredentials():
    parser.read_file(open('credentials.cfg', 'r'))
    global instagramEmail
    global instagramPassword    
    instagramEmail=parser.get('Instagram', 'EMAIL')
    instagramPassword=parser.get('Instagram', 'PASSWORD')

def getTikTokCredentials():
    parser.read_file(open('credentials.cfg', 'r'))
    global tiktokLogin
    global tiktokPassword
    tiktokLogin=parser.get('Tiktok', 'LOGIN')
    tiktokPassword=parser.get('Tiktok', 'PASSWORD')

def getFacebookCredentials():
    parser.read_file(open('credentials.cfg', 'r'))
    global facebookLogin
    global facebookPassword
    facebookLogin=parser.get('Facebook', 'LOGIN')
    facebookPassword=parser.get('Facebook', 'PASSWORD')    

#Login to Instagram on start of application because it takes long to login on every request:
getInstagramCredentials()
API = InstagramAPI(instagramEmail, instagramPassword)
API.login()
API.getProfileData()
my_id = API.LastJson['user']['pk']
API.getUsernameInfo(my_id)



def add_cors(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/')
def root():
    return add_cors(flask.send_from_directory('.', 'index.html'))

@app.route('/js/<path:path>')
def send_js(path):
    return add_cors(flask.send_from_directory('js', path))

@app.route('/css/<path:path>')
def send_css(path):
    return add_cors(flask.send_from_directory('css', path))

@app.route('/captcha/<path:path>')
def send_captcha(path):
    return add_cors(flask.send_from_directory('captcha', path))

@app.route('/img/<path:path>')
def send_img(path):
    return add_cors(flask.send_from_directory('img', path))    

@app.route('/youtube')
def youtube():
    getYoutubeCredentials()
    print(youtubeKey)
    args=flask.request.args
    url=args['url']
    if (len(url)==0):
        return flask.abort(400)  
    return add_cors(flask.Response(json.dumps(cc.getYoutubeComments(url, 'static', youtubeKey))))

@app.route('/instagram')
def instagram():
    args=flask.request.args
    url=args['url']
    if (len(url)==0):
        return flask.abort(400)
    return add_cors(flask.Response(json.dumps(cc.getInstagramComments(url, API))))     

@app.route('/tiktok')
def tiktok():
    getTikTokCredentials()
    args=flask.request.args
    url=args['url']
    cpch=args['captcha']
    response=''
    if (len(url)==0):
        return flask.abort(400)
    if (len(cpch)==0):
        rv=cc.getTikTokComments(url, tiktokLogin, tiktokPassword)
        if (type(rv)==dict):
            response=flask.Response(json.dumps(rv))
        else:
            f = open("captcha/cp.png", "wb+")
            f.write(base64.b64decode(rv))
            f.close()
            response=flask.Response(json.dumps({"captcha": "image"}))
            #response=flask.send_file(io.BytesIO(base64.b64decode(rv)), mimetype='image/gif')
    else:
        response=flask.Response(json.dumps(cc.getTikTokComments(url, tiktokLogin, tiktokPassword, captcha=cpch)))
        if (response.get_data()==b'null'):
            return flask.abort(400)
    return add_cors(response)

@app.route('/facebook')
def facebook():
    getFacebookCredentials()
    args=flask.request.args
    url=args['url']
    if (len(url)==0):
        return flask.abort(400)
    return add_cors(flask.Response(json.dumps(cc.getFacebookComments(url, facebookLogin, facebookPassword))))    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)

    
