import json
import os
from urllib import *
from urllib.parse import urlparse, urlencode, parse_qs
from urllib.request import urlopen
import re
import time
from datetime import datetime
import requests
from tiktok import tt_api
import csv
from random import randint
import subprocess

def getYoutubeComments(url, videoType, key):
    def openYoutubeURL(url, parms):
        f = urlopen(url + '?' + urlencode(parms))
        data = f.read()
        f.close()
        matches = data.decode("utf-8")
        return matches

    def calcYoutubeComments(mat, count, authors):
        try:
            for item in mat["items"]:
                comment = item["snippet"]["topLevelComment"]
                if (haveDigit(comment["snippet"]["textDisplay"])):
                    if (comment["snippet"].get("authorChannelId")!=None):
                        if (not comment["snippet"].get("authorChannelId").get("value") in authors): 
                            authors.append(comment["snippet"].get("authorChannelId").get("value"))
                            count['comments']+=1
                            countDigits(comment["snippet"]["textDisplay"], count)
                    else:
                        count['comments']+=1
                        countDigits(comment["snippet"]["textDisplay"], count)        
                if 'replies' in item.keys():
                    for reply in item['replies']['comments']:
                        if (haveDigit(reply["snippet"]["textDisplay"])):
                            if (reply["snippet"].get("authorChannelId")!=None):
                                if (not reply["snippet"].get("authorChannelId").get("value") in authors):
                                    authors.append(reply["snippet"]["authorChannelId"]["value"])
                                    count['subcomments']+=1
                                    countDigits(reply["snippet"]["textDisplay"], count)
                            else:
                                count['subcomments']+=1
                                countDigits(reply["snippet"]["textDisplay"], count)        
        except Exception as e:
            print(e)                    
    
    def calcYoutubeChat(mat, count, authors):
        for item in mat["items"]:
            comment = item["snippet"]
            if (not comment['authorChannelId'] in authors and haveDigit(comment['displayMessage'])):
                authors.append(comment['authorChannelId'])
                count['comments']+=1
                countDigits(comment['displayMessage'], count)

    vid = str()
    try:
        video_id = urlparse(url)
        q = parse_qs(video_id.query)
        vid = q["v"][0]
    except:
        print("Invalid YouTube URL")
    apiRequest=''
    try:
        if (videoType=='static'):
            parms = {
                'part': 'snippet,replies',
                'maxResults': 100,
                'videoId': vid,
                'textFormat': 'plainText',
                'key': key
            }
            apiRequest='https://www.googleapis.com/youtube/v3/commentThreads'
            commentFunc=calcYoutubeComments
            matches = openYoutubeURL(apiRequest, parms)
        else:
            parms = {
                'part': 'liveStreamingDetails',
                'id': vid,
                'key': key
            }
            response=json.loads(openYoutubeURL('https://www.googleapis.com/youtube/v3/videos', parms))
            parms = {
                'liveChatId': response['items'][0]['liveStreamingDetails']['activeLiveChatId'],
                'part': 'snippet',
                'maxResults': 2000,
                'key': 'key'
            }
            apiRequest='https://www.googleapis.com/youtube/v3/liveChat/messages'
            commentFunc=calcYoutubeChat
            matches = openYoutubeURL('https://www.googleapis.com/youtube/v3/liveChat/messages', parms)    
        i = 2
        mat = json.loads(matches)
        nextPageToken = mat.get("nextPageToken")
        count={'comments': 0, 'subcomments':0, 'ones': 0, 'twos': 0, 'threes': 0, 'fours': 0}
        authors=[]
        commentFunc(mat, count, authors)
        while nextPageToken:
                parms.update({'pageToken': nextPageToken})
                #time.sleep(mat['pollingIntervalMillis']/1000)
                matches = openYoutubeURL(apiRequest, parms)
                mat = json.loads(matches)
                nextPageToken = mat.get("nextPageToken")
                commentFunc(mat, count, authors)
                i += 1        
        return count    
    except KeyboardInterrupt:
        print("User Aborted the Operation")       
    except Exception as e:
        print(str(e))
        #if (videoType!='live'):
        #    getYoutubeComments(url, 'live', key)



def getInstagramComments(url, API):
    def getInstagramMediaId(url):
        req = requests.get('https://api.instagram.com/oembed/?url={}'.format(url))
        media_id = req.json()['media_id']
        return media_id
    
    has_more_comments = True
    media_id=getInstagramMediaId(url)
    max_id = ''
    count={'comments': 0, 'ones': 0, 'twos': 0, 'threes': 0, 'fours': 0}
    authors=[]
    while has_more_comments:
        _ = API.getMediaComments(media_id, max_id=max_id)
        for c in reversed(API.LastJson['comments']):
            if (not c['user_id'] in authors and haveDigit(c['text'])):
                authors.append(c['user_id'])
                count['comments']+=1
                countDigits(c['text'], count)
        next_id = API.LastJson.get('next_max_id', '')
        if (next_id ==''):
            has_more_comments=False
        else:
            max_id=next_id
    return count

def getTikTokComments(url, login, password, captcha=''):
    id=''
    try:
        id=url[url.index('v/')+2:url.index('.html')]
    except:
        paramIndex=url.find('?')
        if (paramIndex!=-1):
            id=url[url.index('video/')+6:paramIndex]
        else:        
            id=url[url.index('video/')+6:len(url)]
    instance=tt_api.api()
    try:
        if (len(captcha)==0):
            login=instance.login(login, password)
            if (login.get('code')):
                return login.get('code')
        else:
            login=instance.login(login, password, captcha)
            if (login.get('code')):
                raise Exception('Invalid captcha')
            #with cookies
            login=instance.login(login, password)
        raw_comments=instance.comment_list(video_id=id, session=instance.active_user['cookies'])
        count={'comments': 0, 'ones': 0, 'twos': 0, 'threes': 0, 'fours': 0}
        authors=[]
        for rc in raw_comments:
            if (not rc['user'].get('uid') in authors and haveDigit(rc['text'])):
                if (rc['user'].get('uid')!=None):
                    authors.append(rc['user'].get('uid'))
                count['comments']+=1
                countDigits(rc['text'], count)
        return count  
    except Exception as e:
        print(str(e))

def getFacebookComments(url, login, password):
    try:
        os.remove('fb_comments.csv')
    except OSError:
        pass    
    command="scrapy crawl comments -a email="+login+" -a password="+password+" -a page=\""+url+" -o fb_comments.csv -a lang=en -a year=2010"
    #print(command)
    try:
        subprocess.check_output(command.split())
    except Exception as e:
        print(str(e))
        pass  
    count={'comments': 0, 'subcomments': 0, 'ones': 0, 'twos': 0, 'threes': 0, 'fours': 0}
    authors=[]
    with open ('fb_comments.csv', newline='', encoding="utf8") as csvfile:
        reader=csv.DictReader(csvfile)
        for row in reader:
            if (not row['source'] in authors and haveDigit(row['text'])):
                authors.append(row['source'])
                countDigits(row['text'], count)
                if (row['reply_to']=='ROOT' or row['reply_to']==''):
                    count['comments']+=1
                else:
                    count['subcomments']+=1
    #os.remove('fb_comments.csv')                
    return count                    

def haveDigit(text):
    if (re.search(r'(^|\W)(1|2|3|4)+(\W|$)', text)!=None):
        return True    
    return False

def countDigits(text, countBuffer):
    oneMatch=re.search(r'(^|\W)(1)+([^a-zA-Z]|$)', text)   
    twoMatch=re.search(r'(^|\W)(2)+([^a-zA-Z]|$)', text)   
    threeMatch=re.search(r'(^|\W)(3)+([^a-zA-Z]|$)', text)   
    fourMatch=re.search(r'(^|\W)(4)+([^a-zA-Z]|$)', text)        
    oneIndex=oneMatch.start() if oneMatch!=None else None
    twoIndex=twoMatch.start() if twoMatch!=None else None
    threeIndex=threeMatch.start() if threeMatch!=None else None
    fourIndex=fourMatch.start() if fourMatch!=None else None
    minIndex=min([i for i in [oneIndex, twoIndex, threeIndex, fourIndex] if  i != None])    
    if (minIndex==oneIndex):
        countBuffer['ones']+=1
    elif (minIndex==twoIndex):
        countBuffer['twos']+=1
    elif (minIndex==threeIndex):
        countBuffer['threes']+=1
    elif (minIndex==fourIndex):
        countBuffer['fours']+=1

#Debug
#if __name__ == "__main__":
   # print(str(getFacebookComments('https://www.facebook.com/ShadyRecords/posts/2036446163057371')))
   # print(str(getFacebookComments('https://mbasic.facebook.com/story.php?story_fbid=2036446163057371&id=194172327284773')))
   #print(str(getFacebookComments('https://m.facebook.com/882129285282298/photos/a.902270676601492/1164142253747665', 'zhane.ermackowa@yandex.ru', 'P@ssw0rd')))
   #print(str(getFacebookComments('https://mbasic.facebook.com/NepsFasciOn/photos/p.365300823563155/365300823563155', 'esbinali@yandex.com', '0ASsoowV')))
#   print(str(getTikTokComments('https://www.tiktok.com/share/video/6633394690240548101?refer=h5_reflow_video_m', 'comment.collector', 'P@ssw0rd')))