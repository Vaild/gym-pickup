import requests
import re

from logzero import logger

from common import RSA
import json
import os
import time
import warnings
warnings.filterwarnings("ignore")

class Login:
    def __init__(self, username, password):
        self.url = "https://pass.sdu.edu.cn/cas/login"
        self.username = username
        self.password = password
        self.ul = len(self.username)
        self.pl = len(self.password)
        self.session = requests.Session()

    def getFirtCookie(self):
        payload = {}
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Microsoft Edge";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(url=self.url, headers=headers, data=payload)

        cookies = list(response.cookies)
        self.cookie_adx = cookies[1].name + "=" + cookies[1].value
        self.jsessionid = cookies[2].name + "=" + cookies[2].value

        regex = re.search(r'LT-.*-cas', str(response.content.decode('utf-8')))
        self.lt = regex.group(0)

        excure = re.search(r'name="execution".*"', str(response.content.decode('utf-8')))
        excall = excure.group(0)
        self.execution = excall[-5:-1]

        envent = re.search(r'name="_eventId".*"', str(response.content.decode('utf-8')))
        enventall = envent.group(0)
        self._eventId = enventall[-7:-1]

    def getRSA(self):
        self.rsa = RSA.strEnc(self.username + self.password + self.lt, '1', '2', '3')

    def postUserLogin(self):
        payload = f'rsa={self.rsa}&ul={self.ul}&pl={self.pl}&lt={self.lt}&execution={self.execution}&_eventId={self._eventId}'

        data = {
            'ras': self.rsa,
            'ul': str(self.ul),
            'pl': str(self.pl),
            'lt': self.lt,
            'execution': self.execution,
            '_eventId': self._eventId
        }

        headers = {
            "Host": "pass.sdu.edu.cn",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'{self.jsessionid}; {self.cookie_adx}; Language=zh_CN',
            'Origin': 'https://pass.sdu.edu.cn',
            'Referer': 'https://pass.sdu.edu.cn/cas/login',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Microsoft Edge";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.post(self.url, data=payload, headers=headers, verify=False)

        self.location = response.history[0].headers._store.get('location')[1]

        headerstore = dict(response.history[0].headers._store)
        setCookies = headerstore.get('set-cookie')[1].split('/,')
        self.formCookies = []
        for cookieRaw in setCookies:
            cookie = cookieRaw.lstrip().split(';')[0]
            self.formCookies.append(cookie)

        serviceUrl = "https://pass.sdu.edu.cn/cas/login?service=http%3A%2F%2Ffreshmansno.wh.sdu.edu.cn%3A9007%2Fapply.html"

        simpleHeader = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Origin': 'https://pass.sdu.edu.cn',
            'Referer': 'https://service.sdu.edu.cn/tp_up/view?m=up',
            'Cookie': f'{self.formCookies[3]}; {self.jsessionid}; {self.formCookies[0]}; Language=zh_CN',
        }

        serviceResponse = self.session.get(url=serviceUrl, headers=simpleHeader, allow_redirects=True, verify=False)

        appCookie = dict(serviceResponse.history[1].cookies)
        finalCookie = "JSESSIONID=" + appCookie.get("JSESSIONID")
        return finalCookie

    def __saveCookie(self, cookiesTime: dict):
        with open("Cookie.json", mode='w') as file:
            data = dict()
            # 然后将新的数据添加进去
            data[self.username] = cookiesTime
            json.dump(data, file)

    def __getSDUCookieOnline(self):
        self.getFirtCookie()
        self.getRSA()
        finalSessionID = self.postUserLogin()
        cookieJson = {
            "cookie": finalSessionID,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        self.__saveCookie(cookieJson)
        return finalSessionID

    def getCookies(self):
        if (os.path.exists("Cookie.json")):
            with open("Cookie.json", mode='r') as file:
                data: dict = json.load(file)
                data = data.get(self.username)
                if data != None and (time.time() - time.mktime(time.strptime(data.get("time"), "%Y-%m-%d %H:%M:%S"))) < 900:
                    logger.info("获取登录信息成功")
                    # 这里要改一下
                    return data.get("cookie")
        return self.__getSDUCookieOnline()

if __name__ == '__main__':
    import sys
    loginTools = Login(sys.argv[1], sys.argv[2])
    cookie = loginTools.getCookies()
    print(cookie)