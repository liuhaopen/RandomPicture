import sublime, sublime_plugin
import re
import random
import threading
from . import ShowImageInSublime
import re, os, shutil

from . import RandNetPicHelper
from . import RandNetPicGamerSky
from . import RandNetPicZbjuran
class RandomPicLoader():
    def __init__(self):
        self.loader = []
        # self.loader.append(RandNetPicBaiduTieba.RandNetPicBaiduTieba())
        self.loader.append(RandNetPicGamerSky.RandNetPicGamerSky())
        self.loader.append(RandNetPicZbjuran.RandNetPicZbjuran())
    #随机下载一张图片
    def load_random_pic(self):
        is_loaded = False
        try_load_count = 0
        while not is_loaded:
            index = 0
            # print("self.loader :", self.loader)
            loader_num = len(self.loader)
            if loader_num <= 0 :
                print("has no vaild pic loader!")
                break
            elif loader_num > 1:
                index = random.randint(0, loader_num-1)
            
            print("loader_num : ", loader_num, " index :", index)
            is_loaded = self.loader[index].load_random_pic()
            print("is_loaded : ", is_loaded)
            if is_loaded == None:
                #该loader的图已经看完了
                del self.loader[index]
            try_load_count+=1
            if try_load_count > 5:
                break

g_random_pic_loader = None

#随机显示一张图片
def show_rand_pic(self, arg):
    global g_random_pic_loader
    g_random_pic_loader = None#测试时打开，否则改了其它Loader也是没用的，需要重新创建实例
    if g_random_pic_loader == None :
        g_random_pic_loader = RandomPicLoader()
    #如果缓存里找图片，有的话就显示，显示完后放到已显示目录，如果没有图片或者数量少于5时就开始从下载队列里下载新的图片
    image_cache_path = sublime.packages_path()+"/RandomPicture/Res/CacheImg/"
    filenames = os.listdir(image_cache_path)
    file_nums = len(filenames) 
    if file_nums <= 1:
        g_random_pic_loader.load_random_pic()
    filenames = os.listdir(image_cache_path)
    file_nums = len(filenames) 
    if file_nums <= 0:
        print("load pic error")
        return
    rand_index = random.randint(0, file_nums-1)
    try_count = 0
    while filenames[rand_index] == "Readed" or RandNetPicHelper.is_downloading(filenames[rand_index]):
        rand_index = random.randint(0, file_nums-1)
        # print("rand_index :", filenames[rand_index])
        try_count = try_count + 1
        if try_count > 130 :
            return
    open_file_full_name = image_cache_path+filenames[rand_index]
    new_readed_file_name = image_cache_path+'Readed/'+filenames[rand_index]
    #先剪切到已阅目录
    try:
        shutil.move(open_file_full_name, new_readed_file_name)
    except:
        pass
    def on_click_image(file_full_name):
        #点击便收藏图片
        file_name = file_full_name.strip().split('/')[-1]
        good_file_path = sublime.packages_path()+'/RandomPicture/Res/Good/'+file_name
        shutil.copy(file_full_name, good_file_path)
        sublime.active_window().active_view().hide_popup()
        global g_is_break_animate
        g_is_break_animate = True
    ShowImageInSublime.show_image(sublime.active_window().active_view(), new_readed_file_name, -1, on_click_image)
    if file_nums <= 5:
        #本地图片不足，下载多几张再说，不用每次都等到没图片的时候再下载
        g_random_pic_loader.load_random_pic()
        g_random_pic_loader.load_random_pic()
        g_random_pic_loader.load_random_pic()
        g_random_pic_loader.load_random_pic()
     

g_test_flag = 0
class RandNetPicCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # ShowImageInSublime.show_image(sublime.active_window().active_view(), 'D:/22.gif', -1)
        # global g_test_flag
        # print("g_test_flag : ", g_test_flag)
        # # g_test_flag = 0
        # if g_test_flag == 0:
        #     ShowImageInSublime.show_image(sublime.active_window().active_view(), 'D:/22.gif', -1)
        #   # ShowImageInSublime.show_image(sublime.active_window().active_view(), 'D:/2.jpg', -1)
        #     g_test_flag += 1
        # elif g_test_flag == 1:
        #     ShowImageInSublime.show_image(sublime.active_window().active_view(), 'D:/test.gif', -1)
        #     g_test_flag += 1
        # else:
        #     ShowImageInSublime.show_image(sublime.active_window().active_view(), 'D:/test3.jpg', -1)
        #     g_test_flag = 0
           
        t =threading.Thread(target=show_rand_pic,args=(self,33,))
        t.start()
        
