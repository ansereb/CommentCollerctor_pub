import time
from time import sleep
import requests
import json
import os.path
from tiktok import tt_helper

class api():
    api_url = "https://api2.musical.ly/"
    global_veriable = {}
    active_user = {}
    helper = tt_helper.helper()
    def __init__(self):
        var = 1
    def login(self,username,password,capthcha=None):
        username = self.helper.xor(str=username)
        if os.path.exists(username+'.json'):
            with open(username+'.json', encoding='utf-8') as json_file:
                load = json.load(json_file)
                if(load.get('data')['user_id']):
                    self.active_user = load
                    return load
        password = self.helper.xor(password)
        url = self.api_url+"passport/user/login/?"+self.helper.query(self.helper.default_veriable(self.global_veriable))

        posts = {
            'mix_mode':1,
            'username':username,
            'password':password,
            'email': None,
            'mobile': None,
            'account': None,
            'captcha': capthcha
        }
        login = self.helper.request_post(url,posts)

        print(login.json())
        if(login.json().get('data').get('captcha')):
                return {'error':'captcha','code':login.json().get('data').get('captcha')}

        try:
            headers = {}
            for c in login.cookies:
                headers[c.name]= c.value

        except KeyError:
            headers = None
        success = {}
        if(login.status_code != 200):
            return login.status_code
        else:
            data = login.json()
            if (data.get('data') and (data.get('error_code') == None)):
                success['data'] = self.helper.user_data_export(data.get('data'))
                success['cookies'] = headers
                with open(username +'.json', 'w') as outfile:
                    json.dump(success, outfile)
                return success
            else:
                return login.json()

    def comment_list(self, video_id, session={}):
        comments=[]
        cursor=0
        total=1
        while cursor<total:
            url=self.api_url+"aweme/v1/comment/list/?aweme_id="+str(video_id)+"&cursor="+str(cursor)+"&comment_style=2&"+self.helper.query(self.helper.default_veriable(self.global_veriable))
            if(session.__len__()>0):
                response = self.helper.request_get(self,url,session=session)
            else:
                response = self.helper.request_get(self,url)
            data=response.json()    
            comments.extend(data['comments'])
            cursor=data['cursor']
            total=data['total']
        return comments