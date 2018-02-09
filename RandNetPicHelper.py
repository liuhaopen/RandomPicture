import sublime, sublime_plugin
import re
import random
import threading
import re, os, shutil
import urllib
from urllib.request import urlopen
import time
import datetime


#获取已读链接
def get_readed_url():
    readed_file_path = sublime.packages_path()+"/RandomPicture/Res/Cookies/Cookies-GamerSky.txt"
    file_object = None
    if not os.path.exists(readed_file_path):
        file_object = open(readed_file_path, "w+")
    else:
        file_object = open(readed_file_path)
    try:
        file_object.seek(0)
        list_of_all_the_lines = file_object.readlines()
        # print("list_of_all_the_lines : ", list_of_all_the_lines)
    finally:
         file_object.close( )
    return list_of_all_the_lines

#从存档里加入已读链接
def add_readed_url( url ):
    readed_file_path = sublime.packages_path()+"/RandomPicture/Res/Cookies/Cookies-GamerSky.txt"
    output = open(readed_file_path, 'a')
    # print(dir(output))
    try:
        output.write('\n'+url)
        print("list_of_all_the_lines : ")
    finally:
        output.close( )

#查询某url是否已存在
def is_readed_page_url(cache_id, check_url):
    pass

#从存档里读取已阅链接
def get_unreaded_page_urls(html_url_cache):
    readed_url = get_readed_url()
    result = html_url_cache
    for k, v in enumerate(readed_url):
        for kk, vv in enumerate(result):
            if v.replace("\n", "") == vv:
                del result[kk]
                break
    return result

g_downloaded_pic_urls = {}
g_downloading_pic_urls = {}
def download_pic_from_url(pic_url):
    global g_downloaded_pic_urls
    global g_downloading_pic_urls
    if g_downloaded_pic_urls.get(pic_url) != None :
        #已经下载过此文件了
        return False
    g_downloaded_pic_urls[pic_url] = True
    file_name = pic_url.strip().split('/')[-1]
    now=datetime.datetime.now()
    t_str = now.strftime('%Y-%m-%d-%H-%M-%S-')
    file_name = t_str + file_name
    g_downloading_pic_urls[file_name] = True
    def on_download_ok(a, b, c):
        '''回调函数
        @a: 已经下载的数据块
        @b: 数据块的大小
        @c: 远程文件的大小
        ''' 
        per = 100.0 * a * b / c 
        # print("per :", per, " file_name :", file_name)
        if per >= 100: 
            per = 100 
            global g_downloading_pic_urls
            # print("file_name :", file_name, " g_downloading_pic_urls:", g_downloading_pic_urls[file_name])
            g_downloading_pic_urls[file_name] = False
    image_cache_path = sublime.packages_path()+"/RandomPicture/Res/CacheImg/"
    urllib.request.urlretrieve(pic_url, image_cache_path+file_name, on_download_ok)
    return True

def is_downloading(file_name):
    global g_downloading_pic_urls
    if g_downloading_pic_urls.get(file_name) == None:
        return False
    # print("is_downloading file_name :", file_name, " g_downloading_pic_urls:", g_downloading_pic_urls[file_name])
    return g_downloading_pic_urls[file_name]