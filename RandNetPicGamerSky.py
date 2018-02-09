import sublime, sublime_plugin
import re
import random
import threading
from . import ShowImageInSublime
import re, os, shutil
import urllib
from urllib.request import urlopen
from . import RandNetPicHelper

#抓取游民星空的娱乐频道里的图
class RandNetPicGamerSky():
    def __init__(self):
        self.html_url_cache = []
        self.pic_url_cache = []
        self.gamer_sky_ent_url = r'http://www.gamersky.com/ent/'

    #随机下载一张图片
    def load_random_pic(self):
        return self.load_random_pic_url(0)

    #随机下载一张图片
    def load_random_pic_url(self, count=0):
        if count >= 10:
            return False
        pic_url_num = len(self.pic_url_cache)
        if pic_url_num <= 0:
            page_url_num = len(self.html_url_cache)
            if page_url_num <= 0:
                #网页URL缓存不足时就要加了，为了性能，这里只加1条，然后另外线程再去抓取网页吧
                self.get_gamer_sky_page_urls()
            page_url_num = len(self.html_url_cache)
            if page_url_num <= 0:
                # sublime.message_dialog("有没有搞错，图都给你看光了!")
                print("GamerSky:有没有搞错，图都给你看光了!")
                return False
            rand_index = random.randint(0, page_url_num-1)
            new_pic_urls = self.get_gamer_sky_pic_urls(self.html_url_cache[rand_index])
            if new_pic_urls != None:
                self.pic_url_cache += new_pic_urls
            RandNetPicHelper.add_readed_url(self.html_url_cache[rand_index])
            del self.html_url_cache[rand_index]
        pic_url_num = len(self.pic_url_cache)
        if pic_url_num <= 0:
            #还是解析不到就再次尝试，最多10次
            return self.load_random_pic_url(count+1)

        rand_index = random.randint(0, pic_url_num-1)
        pic_url = self.pic_url_cache[rand_index]
        load_succeed = RandNetPicHelper.download_pic_from_url(pic_url)
        # file_name = pic_url.strip().split('/')[-1]
        # image_cache_path = sublime.packages_path()+"/RandomPicture/Res/CacheImg/"
        # now=datetime.datetime.now()
        # t_str = now.strftime('%Y-%m-%d-%H-%M-%S-')
        # file_name = t_str + file_name
        # urllib.request.urlretrieve(pic_url,image_cache_path+file_name)
        if load_succeed :
            del self.pic_url_cache[rand_index]
        return True

    #解析游民星空娱乐频道里的页面url
    def get_gamer_sky_page_urls(self, timeout=10, more=False):
        # print("len(self.html_url_cache)", len(self.html_url_cache))
        if len(self.html_url_cache) > 0:
            self.html_url_cache = RandNetPicHelper.get_unreaded_page_urls(self.html_url_cache)
            rand_index = random.randint(0, len(self.html_url_cache)-1)
            return self.html_url_cache[rand_index]
        try:
            html = urlopen(self.gamer_sky_ent_url, timeout=timeout).read()
        except "":
            return None
        patt_str = r'<div class="tit"><a class="dh".*?href="(\S*shtml)"'
        self.html_url_cache = re.findall(patt_str, str(html))
        for i, url in enumerate(self.html_url_cache):
            if url[0] == '/':
                self.html_url_cache[i] = "http://www.gamersky.com"+url
        self.html_url_cache = RandNetPicHelper.get_unreaded_page_urls(self.html_url_cache)
        return self.html_url_cache

    #解析获取游民星空page_url页面里的图片url
    def get_gamer_sky_pic_urls(self, page_url, timeout=10, more=False):
        try:
            html = urlopen(page_url, timeout=timeout).read()
        except:
            return None

        #先找出图片url区域的字符串
        patt_str = r'<div class="Mid2L_con">[\s\S]*?<div class="page_css">'
        html_str = str(html)
        res = re.search(patt_str, html_str)
        if res == None:
            return None
        contain_pic_url = res.group()
        patt_str = r'<img .*?src="(\S*)"'
        contain_pic_url_str = str(contain_pic_url)
        res = re.findall(patt_str, contain_pic_url_str)
        #解析本url的其它页
        patt_str = r' id="pe100_page_contentpage"[\s\S]*?</span>'
        res2 = re.search(patt_str, html_str)
        patt_str = r'href="(\S*)"'
        other_page_url_re = re.findall(patt_str, str(res2.group()))
        for k, v in enumerate(other_page_url_re):
            had_in_cache = False
            for kk, vv in enumerate(self.html_url_cache):
                if v == vv:
                    had_in_cache = True
                    break
            if not had_in_cache:
                self.html_url_cache.append(v)
        self.html_url_cache = RandNetPicHelper.get_unreaded_page_urls(self.html_url_cache)
        return res