# This Python script is a Windows screen-capture utility that uses native Win32 graphics APIs (win32gui, win32ui, and win32api) to take a snapshot
# of the entire virtual desktop (supporting multi-monitor configurations), save it as a bitmap file, and optionally read its contents.

import base64
import win32api
import win32con
import win32gui
import win32ui

# get the dimensions of the screen
def get_dimensions():
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    return (width, height, left, top)

def screenshot(name='screenshot'): # default file name of 'screenshot'
    hdesktop = win32gui.GetDesktopWindow() # stores a handle to the desktop window
    width, height, left, top = get_dimensions() # calls the helper function and stores the window dimensions

    # dc = device context, which is an environment for drawing. Windows OS is always maintaining a live dc for the monitor image
    desktop_dc = win32gui.GetWindowDC(hdesktop) # grabs the live desktop dc from the hdesktop handle
    img_dc = win32ui.CreateDCFromHandle(desktop_dc) # desktop_dc is only a windows token, win32ui wraps the token into a python object
    mem_dc = img_dc.CreateCompatibleDC() # create a new duplicate dc to draw on that exists only in memory and won't be on the live screen

    screenshot = win32ui.CreateBitmap() # make an empty bitmap object
    screenshot.CreateCompatibleBitmap(img_dc, width, height) # match the bitmap dimensions to the screen
    mem_dc.SelectObject(screenshot) # matches the screenshot bitmap with the dc that we created earlier that resides in memory
    mem_dc.BitBlt((0,0), (width, height), # Bit Block Transfer (BitBlt) copies pixels directly from the live screen dc to our memory dc
                  img_dc, (left, top), win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, f'{name}.bmp') # saves the bitmap data to a .bmp file 

    mem_dc.DeleteDC() # clean up the dc and handle that we used
    win32gui.DeleteObject(screenshot.GetHandle())

def run():
    screenshot() # saves the screenshot as 'screenshot.bmp'
    with open('screenshot.bmp') as f:
        img = f.read() # reads the contents of the bitmap file and saves those bytes to the img variable
    return img # returns the contents of the bitmap file so we can do things with it

# this program is designed to be modular, so if we run the script in the terminal to test it, we only want to take a screenshot. 
# but if this is imported to another program, we don't want it to run automatically, but only when run() is called
if __name__ == '__main__':
    screenshot()
