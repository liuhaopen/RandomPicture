import sublime
import sublime_plugin
import base64
import os
import re
import urllib.parse
import urllib.request
from . import get_image_size
from PIL import Image, ImageSequence
import threading
from io import BytesIO
import time
IMAGE_FORMATS = 'jpg|jpeg|bmp|gif|svg|png|'

g_gif_thread = None
def on_hide_func():
    if g_gif_thread != None :
        g_gif_thread.stop()

def show_image(view, path, point, click_call_back=None):
    global g_gif_thread
    on_hide_func()
    url = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    imageURL = re.compile('.+(?:' + IMAGE_FORMATS + ')')
    if (url.match(path) and imageURL.match(path)):
        url_path = urllib.parse.quote(path).replace("%3A", ":", 1)
        f = urllib.request.urlopen(url_path)
        encoded = str(base64.b64encode(f.read()), "utf-8")
        view.show_popup('<img src="data:image/png;base64,' +
                            encoded +
                        '">',
                         flags=0,
                         location=point,max_width=1024,max_height=720)
        return
    pattern = re.compile('([-@\w]+\.(?:' + IMAGE_FORMATS + '))')
    if True or (path and path != "" and pattern.match(path)):
        base_folders = sublime.active_window().folders()

        file_name = path
        if (file_name and os.path.isfile(file_name)):
            file_type = file_name.strip().split('.')[-1]
            if file_type == "gif":
                if g_gif_thread == None :
                    g_gif_thread = GifShowThread()
                g_gif_thread.show_gif(view, path, point, click_call_back)
                return
            encoded = str(base64.b64encode(
                            open(file_name, "rb").read()
                        ), "utf-8")

            max_width = 1024
            max_height = 720
            max_ratio = max_height / max_width

            try:
                width, height = get_image_size.get_image_size(file_name)
            except get_image_size.UnknownImageFormat:
                width, height = -1, -1

            if height / width >= max_ratio and height > max_height:
                ratio = max_height / height
                width = width * ratio
                height = height * ratio
            elif height / width <= max_ratio and width > max_width:
                ratio = max_width / width
                width = width * ratio
                height = height * ratio

            view.show_popup('<a href="'+file_name+'"><img style="width:' + str(width) +
                                        'px;height:' + str(height) +
                                        'px;" src="data:image/png;base64,' +
                                encoded +
                            '"></a>',
                             flags=0,
                             location=point,max_width=1024,max_height=720,on_navigate=click_call_back)
            return
        return
    return

def prn_obj(obj): 
    result = '\n'
    print(result.join(['%s:%s' % item for item in obj.__dict__.items()]))

class GifShowThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.state = "None"
        self.is_running = threading.Event()

    def show_gif(self, view, path, point, click_call_back=None):
        self.view = view
        self.path = path
        self.point = point
        self.click_call_back = click_call_back
        self.loadImg()
        self.is_running.set()
        if self.state == "None" :
            self.state = "Running"
            self.start()
        elif self.state == "Stop" :
            self.state = "Running"
            
    def stop(self):
        self.state = "Stop"
        self.is_running.clear()

    def loadImg(self):
        self.im = Image.open(self.path)  
        #这里有空需要处理下线程同步问题，self.im有可能在另外的线程被改变，所以analyseImage函数可能会出错
        self.mode = self.analyseImage(self.im)['mode']  
        # self.im.seek(1)
        self.im = Image.open(self.path)  
        self.p = self.im.getpalette()  
        self.last_frame = self.im.convert('RGBA')  
        
    def run(self):
        try:  
            self.loadImg()
            while True :
                if self.state == "Running":  
                    if not self.im.getpalette():  
                        self.im.putpalette(self.p)  
                    duration = self.im.info['duration']
                    new_frame = Image.new('RGBA', self.im.size)  
                      
                    if self.mode == 'partial':  
                        new_frame.paste(self.last_frame)
                      
                    new_frame.paste(self.im, (0,0), self.im.convert('RGBA'))  
                    buffer = BytesIO()
                    new_frame.save(buffer, format="PNG", quality=100)
                    encoded = str(base64.b64encode(buffer.getvalue()), "utf-8")
                    self.is_running.wait()
                    if not self.view.is_popup_visible() :
                        self.view.show_popup('<a href="'+self.path+'"><img style="width:' + str(self.im.size[0]) +
                                                    'px;height:' + str(self.im.size[1]) +
                                                    'px;" src="data:image/png;base64,' +
                                            encoded +
                                        '"></a>',
                                         flags=0,
                                         location=self.point,max_width=1024,max_height=720,on_navigate=self.click_call_back,on_hide=on_hide_func)
                    else:
                        self.view.update_popup('<a href="'+self.path+'"><img style="width:' + str(self.im.size[0]) +
                                                    'px;height:' + str(self.im.size[1]) +
                                                    'px;" src="data:image/png;base64,' +
                                            encoded +
                                        '"></a>')
                    
                    time.sleep(duration/1000)
                    self.last_frame = new_frame  
                    try:
                        self.im.seek(self.im.tell() + 1)  
                    except EOFError:
                        if self.im.tell() > 0 :
                            self.im.seek(1)  
                else:
                    time.sleep(0.02)
        except :  
            global g_gif_thread
            g_gif_thread = None
    def analyseImage(self, im):  
        results = {  
            'size': im.size,  
            'mode': 'full',  
        }  
        try:  
            while True:  
                if im.tile:  
                    tile = im.tile[0]  
                    update_region = tile[1]  
                    update_region_dimensions = update_region[2:]  
                    if update_region_dimensions != im.size:  
                        results['mode'] = 'partial'  
                        break  
                try :
                    im.seek(im.tell() + 1)  
                except :
                    break    
        except EOFError:  
            pass  
        return results  