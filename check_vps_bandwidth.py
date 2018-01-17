#!/usr/bin/python
# -*- coding:utf-8 -*-
# Author: Ro$es

import urllib.request
import http.cookiejar
import configparser
from bs4 import BeautifulSoup
import json
import re
import sys
from email_constructor import Email


class Vps(object):
    def __init__(self, user, password):
        self.client_area_url = "https://billing.virmach.com/clientarea.php"
        self.login_url = "https://billing.virmach.com/dologin.php"
        self.logout_url = "https://billing.virmach.com/logout.php"
        self.user = user
        self.password = password

        # install opener with cookiejar
        self.cookie = http.cookiejar.CookieJar()
        self.cookie_processor = urllib.request.HTTPCookieProcessor(self.cookie)
        self.opener = urllib.request.build_opener(self.cookie_processor)
        self.opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0")]
        urllib.request.install_opener(self.opener)

    def login(self):
        request = urllib.request.Request(self.client_area_url)
        responce = urllib.request.urlopen(request)
        html = responce.read().decode("utf-8")

        soup = BeautifulSoup(html, "lxml")

        # get csrf token
        csrf_token = soup.find("input", attrs={"type": "hidden", "name": "token"})["value"]
        # print(csrf_token)

        headers = {
            'origin': "https://billing.virmach.com",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            'content-type': "application/x-www-form-urlencoded",
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            'referer': "https://billing.virmach.com/clientarea.php",
            'accept-language': "zh-CN,zh;q=0.8,en;q=0.6",
        }

        params = {
            'username': self.user,
            'password': self.password,
            'token': csrf_token
        }
        params = urllib.parse.urlencode(params).encode("utf-8")

        request = urllib.request.Request(self.login_url, data=params, headers=headers)
        responce = urllib.request.urlopen(request)

        if responce.getcode() != 200:
            print("Login failed.")
            sys.exit(1)

    def get_bandwidth(self, vpsid):
        url = "%s?action=productdetails&id=%s&json=true" % (self.client_area_url, vpsid)

        headers = {
            'accept': "*/*",
            'origin': "https://billing.virmach.com",
            'x-requested-with': "XMLHttpRequest",
            'content-type': "application/x-www-form-urlencoded",
            'accept-language': "zh-CN,zh;q=0.8,en;q=0.6",
            'cache-control': "no-cache",
        }

        params = {
            'mg-action': 'detailsVM'
        }
        params = urllib.parse.urlencode(params).encode("utf-8")

        request = urllib.request.Request(url, data=params, headers=headers)
        responce = urllib.request.urlopen(request)
        data = responce.read().decode("utf-8")
        data = json.loads(re.match('<JSONRESPONSE#(.*)#ENDJSONRESPONSE>', data).group(1))

        bandwidth = data['data']['bandwidth'].split(",")
        bandwidth_all = round(int(bandwidth[0]) / 1024**3, 2)
        bandwidth_used = round(int(bandwidth[1]) / 1024**3, 2)
        bandwidth_left = round(int(bandwidth[2]) / 1024**3, 2)
        bandwidth_used_percent = int(bandwidth[3])

        return (bandwidth_all, bandwidth_used, bandwidth_left, bandwidth_used_percent)

    def logout(self):
        request = urllib.request.Request(self.logout_url)
        responce = urllib.request.urlopen(request)

        # if responce.getcode() != 200:
        #     print("Logout failed.")
        print(responce.getcode())
        print(responce.info())


if __name__ == "__main__":
    login_data = configparser.ConfigParser()
    login_data.read("virmach_user.ini")

    user = login_data.get("UserInfo", "user")
    password = login_data.get("UserInfo", "password")
    vps_id = login_data.get("UserInfo", "vpsid")

    vps_api = Vps(user, password)
    vps_api.login()
    bandwidth = vps_api.get_bandwidth(vps_id)
    vps_api.logout()
    email_content = """
    VPS带宽使用情况：\n
    总带宽： %s GB\n
    已使用： %s GB(%s %)\n
    剩余带宽: %s GB\n
    """ % (bandwidth[0], bandwidth[1], bandwidth[3], bandwidth[2])
    from_name = "VPS流量监控"
    to_name = "Admin"
    subject = "VPS带宽使用情况"
    email = Email("virmach_user.ini", from_name, to_name, subject, email_content)
    email.send()
