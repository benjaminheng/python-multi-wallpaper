#!/usr/bin/env python
# Module     : SysTrayIcon.py
# Synopsis   : Windows System tray icon.
# Programmer : Simon Brunning - simon@brunningonline.net
# Date       : 11 April 2005
# Notes      : Based on (i.e. ripped off from) Mark Hammond's
#              win32gui_taskbar.py and win32gui_menu.py demos from PyWin32
'''TODO

For now, the demo at the bottom shows how to use it...'''
         
import subprocess
import os
import sys
import win32api
import win32con
import win32gui_struct
import threading
import time
import random
import pythoncom
from PIL import Image
from win32com.shell import shell, shellcon
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui

class SysTrayIcon(object):
    '''TODO'''
    QUIT = 'Quit'
    SPECIAL_ACTIONS = [QUIT]
    
    FIRST_ID = 1023
    
    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 default_menu_index=None,
                 window_class_name=None,):
        
        self.icon = icon
        self.hover_text = hover_text
        self.on_quit = on_quit
        
        menu_options = menu_options + (('Quit', None, self.QUIT),)
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        del self._next_action_id
        
        
        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "SysTrayIconPy"
        
        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER+20 : self.notify,}
        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                          self.window_class_name,
                                          style,
                                          0,
                                          0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT,
                                          0,
                                          0,
                                          hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()
        
        win32gui.PumpMessages()

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action = menu_option
            if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                result.append(menu_option + (self._next_action_id,))
            elif non_string_iterable(option_action):
                result.append((option_text,
                               option_icon,
                               self._add_ids_to_menu_options(option_action),
                               self._next_action_id))
            else:
                print 'Unknown item', option_text, option_icon, option_action
            self._next_action_id += 1
        return result
        
    def refresh_icon(self):
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print "Can't find icon file - using default."
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER+20,
                          hicon,
                          self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit: self.on_quit(self)
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_LBUTTONDBLCLK:
            self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        elif lparam==win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam==win32con.WM_LBUTTONUP:
            pass
        return True
        
    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        self.create_menu(menu, self.menu_options)
        #win32gui.SetMenuDefaultItem(menu, 1000, 0)
        
        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
    
    def create_menu(self, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = self.prep_menu_icon(option_icon)
            
            if option_id in self.menu_actions_by_id:                
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        # Fill the background.
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        # unclear if brush needs to be feed.  Best clue I can find is:
        # "GetSysColorBrush returns a cached brush instead of allocating a new
        # one." - implies no DeleteObject
        # draw the icon
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)
        
        return hbm

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)
        
    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]      
        if menu_action == self.QUIT:
            win32gui.DestroyWindow(self.hwnd)
        else:
            menu_action(self)
            
def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return not isinstance(obj, basestring)

# 
class Wallpaper:
    def __init__(self, wallpapers, monitors=2, resolutions=[[1920, 1080], [1920, 1080]]):
        self.iad = pythoncom.CoCreateInstance(shell.CLSID_ActiveDesktop, None,
          pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IActiveDesktop)
        self.monitors = monitors
        self.resolutions = resolutions

        # must initialize wallpapers
        self.wallpapers = wallpapers

        # tmp wallpaper to apply
        self.tmpWallpaper = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tmp-wallpaper.png')


        if monitors != len(resolutions):
            raise Exception('Variable \'resolutions\' must have an equal number of elements as defined by variable \'monitors\'')

    # monitor=0 to simply set the image without concatenating it. it will span all displays this way.
    def set_wallpaper(self, path, monitor=2, applyChange=True):
        # sets the updates the wallpaper in the list at the appropriate index
        self.wallpapers[monitor-1] = path
        if applyChange:
            self.apply_wallpaper()
    
    # combine self.wallpapers before applying
    def apply_wallpaper(self):
        self.combine_wallpapers()
        self.iad.SetWallpaper(self.tmpWallpaper, 0)
        pythoncom.CoInitialize()
        self.iad.ApplyChanges(shellcon.AD_APPLY_ALL)
    
    # useless
    def get_wallpaper(self):
        self.iad.GetWallpaper()


    def combine_wallpapers(self):
        width = sum([i[0] for i in self.resolutions])
        height = max([i[1] for i in self.resolutions])
        new_im = Image.new('RGB', (width, height))
        pasteIndex = 0
        for i, j in enumerate(self.wallpapers):
            # first scales the image to width=yourMonitor'sWidth and keep aspect ratio
            im = Image.open(self.wallpapers[i])
            # if img width > monitor resolution, scale to monitor's width, keep aspect ratio
            if im.size[0] > self.resolutions[i][0]:
                newWidth = self.resolutions[i][0]
                wpercent = (newWidth/float(im.size[0]))
                newHeight = int((float(im.size[1])*float(wpercent)))
                im = im.resize((newWidth, newHeight), Image.ANTIALIAS)

            # by this point the img width should always = monitor width
            # the height might still be more, so we want to center the image on the monitor
            if im.size[0] >= self.resolutions[i][0] and im.size[1] > self.resolutions[i][1]:
                left = (im.size[0] - self.resolutions[i][0])/2
                top = (im.size[1] - self.resolutions[i][1])/2
                right = (im.size[0] + self.resolutions[i][0])/2
                bottom = (im.size[1] + self.resolutions[i][1])/2

                im.crop((left, top, right, bottom))


            # if first wallpaper, paste at x=0&y=0, then add the width of the monitor so that
            # the next paste is at the appropriate index.
            new_im.paste(im, (pasteIndex,0))
            pasteIndex = pasteIndex + self.resolutions[i][0]
        # save to file first
        new_im.save(self.tmpWallpaper)


class WallpaperThread(threading.Thread):
    def __init__(self, staticwall, path, interval):
        threading.Thread.__init__(self)
        self.path = path
        self.interval = interval
        self.staticwall = staticwall
        self.wall = Wallpaper([staticwall, staticwall])
        self.event = threading.Event()

    def run(self):
        files = [os.path.join(self.path, f) for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]
        random.shuffle(files)
        while True:
            for i in files:
                try:
                    # to update more then 1 monitor's wallpaper,
                    # call .set_wallpaper with applyChange=False keyword for all your monitors
                    # when done, call .apply_wallpaper()
                    self.wall.set_wallpaper(i, 2)
                except IOError: continue
                #time.sleep(interval)
                self.event.wait(interval)




# Minimal self test. You'll need a bunch of ICO files in the current working
# directory in order for this to work...
if __name__ == '__main__':
    import itertools, glob
    
    icons = itertools.cycle(glob.glob('*.ico'))
    hover_text = "Wallpaper Changer"

    def quit(sysTrayIcon): 
        print 'Exiting.'

    # delete wallpaper on monitor 2
    def delete_wallpaper_2(sysTrayIcon): 
        os.remove(t.wall.wallpapers[1])
        send_update_wallpapers_cmd()

    def update_wallpapers(sysTrayIcon): 
        send_update_wallpapers_cmd()

    def send_update_wallpapers_cmd():
        t.event.set()
        t.event.clear()
    
    ######
    # USER-DEFINED VARIABLES 
    interval = 60*60 # seconds
    wallPath = 'F:\\Pictures\\wallpapers\\interfacelift'
    # staticWallpaper is what you initialize your wallpapers to.
    staticWallpaper = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'monitor0wallpaper.png')
    # END USER-DEFINED VARIABLES
    ######

    t = WallpaperThread(staticWallpaper, wallPath, interval)
    t.daemon = True
    t.start()
       
    menu_options = (('Update Wallpapers', icons.next(), update_wallpapers),('Delete Wallpaper #2', icons.next(), delete_wallpaper_2),)
    
    SysTrayIcon(icons.next(), hover_text, menu_options, on_quit=quit, default_menu_index=1)
