import sublime, sublime_plugin
from urllib.request import urlopen
import re
import time
import urllib
import datetime
from . import RandNetPicHelper
import os

class RandNetPicZbjuran():
    def __init__(self, page_url_prefix=r"http://www.zbjuran.com/dongtai/"):
        self.page_main_url = 'http://www.zbjuran.com'
        self.page_url_prefix = page_url_prefix
        self.pic_url_cache = []
        self.image_cache_path = sublime.packages_path()+"/RandomPicture/Res/CacheImg/"
        self.cur_page_url = None
        self.cookies_file_path = sublime.packages_path()+"/RandomPicture/Res/Cookies/Cookies-Zbjuran.txt"
        # self.test_next_page_url()
    # 随机下载一张图片
    def load_random_pic(self, run_count=0):
        if run_count >= 30:
            #防止死循环
            return False
        #先从缓存里看看是否已有图片的URL了，有的话直接下载就行了
        if len(self.pic_url_cache) > 0 :
            pic_url = self.page_main_url+self.pic_url_cache[0]
            load_succeed = RandNetPicHelper.download_pic_from_url(pic_url)

            # file_name = pic_url.strip().split('/')[-1]
            # now=datetime.datetime.now()
            # t_str = now.strftime('%Y-%m-%d-%H-%M-%S-')
            # file_name = t_str + file_name
            # # print("pic_url : ", pic_url, "      ", self.pic_url_cache)
            # urllib.request.urlretrieve(pic_url,self.image_cache_path+file_name)
            if load_succeed and len(self.pic_url_cache) > 0:
                del self.pic_url_cache[0]
            # print("pic_url deleted : ", pic_url, "      ", self.pic_url_cache)
            return True

        #先获取本地的记录，看看已经解析到第几期了，没有记录的话就解析第一期的网页，每一期的网页里包含页数，然后每页都有图片可提取，提完后就看下一期的，重复以上操作
        if self.cur_page_url == None:
            self.cur_page_url = self.get_last_unread_url_from_cookies()
            if self.cur_page_url == None or self.cur_page_url == "":
                self.cur_page_url = "http://www.zbjuran.com/quweitupian/201412/29.html"
                # self.cur_page_url = "http://www.zbjuran.com/quweitupian/201801/87921.html"
        # self.cur_page_url = "http://www.zbjuran.com/quweitupian/201801/87920.html"#Test
        try:
            html = urlopen(self.cur_page_url, timeout=10).read()
        except:
            return False
        html_str = str(html)

        #从当前期里提取出该期的所有页的URL
        urls = self.get_urls_from_page(html_str)
        if urls == None :
            #如果当前期没有其它页的话就直接提取图片
            # print(" self.cur_page_url : ", self.cur_page_url)
            self.pic_url_cache = self.pic_url_cache + self.get_pic_urls_from_page(html_str)
        else:
            pos = self.cur_page_url.rfind("/")
            prefix_url = self.cur_page_url[:pos]
            for k, v in enumerate(urls):
                if v == "#" :
                    continue
                #提取出该页的所有主文图片
                pic_html_str = html_str
                tmp_url = prefix_url+"/"+v
                if tmp_url != self.cur_page_url :
                    try:
                        pic_html = urlopen(tmp_url, timeout=10).read()
                    except:
                        return False
                    pic_html_str = str(pic_html)
                self.pic_url_cache = self.pic_url_cache + self.get_pic_urls_from_page(pic_html_str)
                # print("get_pic_urls_from_page() self.pic_url_cache : ", self.pic_url_cache)

        #下一期URL
        # print("self.cur_page_url before get next page: ", self.cur_page_url)
        self.cur_page_url = self.get_next_page_url(html_str)
        # print("self.cur_page_url : ", self.cur_page_url)
        if self.cur_page_url == None:
            for x in range(1,50):
                print("RandNetPicZbjuran has no next page!!!!!!")
            return None
        #保存下一期URL到文件
        self.set_last_unread_url_from_cookies(self.cur_page_url)
        #如果上面已经提取到了图片URL了，self.load_random_pic就会直接下载
        return self.load_random_pic(run_count+1)
    
    def get_last_unread_url_from_cookies(self):
        file_object = None
        if not os.path.exists(self.cookies_file_path):
            file_object = open(self.cookies_file_path, "w+")
        else:
            file_object = open(self.cookies_file_path)
        try:
            list_of_all_the_lines = file_object.readlines()
            if list_of_all_the_lines == None or len(list_of_all_the_lines) <= 0:
                return
        finally:
             file_object.close( )
        return list_of_all_the_lines[0]   

    #从存档里加入已读链接
    def set_last_unread_url_from_cookies( self, url ):
        output = open(self.cookies_file_path, 'w')
        try:
            output.write(url)
        finally:
            output.close( )

    def test_next_page_url(self):
        # page_url = "http://www.zbjuran.com/quweitupian/201412/29.html"
        page_url = "http://www.zbjuran.com/quweitupian/201503/20524.html"
        count = 0
        while True:
            print("page_url : ", page_url)
            try:
                html = urlopen(page_url, timeout=10).read()
            except:
                return None
            #提取下一期
            html_str = str(html)
            urls = self.get_next_page_url(html_str)
            if urls == None :
                for x in range(1,50):
                    print("!!!!!!!!!!!!!!!end!!!!!!!!!!!!")
                break
            page_url = urls   
            # count = count + 1
            # if count > 600000 :
                # break
        
    #获取下一期的URL
    def get_next_page_url(self, html_str):
        patt_str = r'<span id="pre">[\s\S]*?<a href=\\\'([\s\S]*?)\\\'>'
        urls = re.findall(patt_str, html_str)
        if urls == None or len(urls)<=0 :
            return
        return self.page_main_url + urls[0]

    #从每期首页里解析出本期有哪几页，就算没有其它页，结果里也会包含自己
    def get_urls_from_page(self, html_str, timeout=10):
        patt_str = r'<div class="page">[\s\S]*?</div>'
        result = re.search(patt_str, html_str)
        if result == None :
            return None
        contain_page_url_str = result.group()    
        patt_str = r'<a href=\\\'([\s\S]*?)\\\'>'
        urls = re.findall(patt_str, contain_page_url_str)
        # print("get_urls_from_page() urls :", urls)
        return urls

   	#从某具体页中提取图片
    def get_pic_urls_from_page(self, html_str, timeout=10):
        #要先找到主文的区域，然后在区域里找图片
        patt_str = r'<div class="main">[\s\S]*?<div class="article">[\s\S]*?<img[\s\S]*?</div>'
        result = re.search(patt_str, html_str)
        if result == None :
            return None
        contain_pic_url_str = result.group()    
        # print("get_pic_urls_from_page() contain_pic_url_str : ", contain_pic_url_str)
        patt_str = r'<img[\s\S]*?src=([\s\S]*?) [\s\S]*?>'
        urls = re.findall(patt_str, contain_pic_url_str)
        # print("get_pic_urls_from_page() urls : ", urls)
        for k, v in enumerate(urls):
            urls[k] = v.replace('\'', '')
            urls[k] = v.replace('\"', '')
            # print("get_pic_urls_from_page() pic url : ", v, urls[k])
        return urls