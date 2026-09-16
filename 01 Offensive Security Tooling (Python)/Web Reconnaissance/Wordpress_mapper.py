# Wordpress web content scanner that traverses a local directory structure, strips out static media files, 
# and uses multiple concurrent threads to test if those same file paths exist and are accessible on a remote target web server.

import contextlib
import os
import queue
import requests
import sys
import threading
import time

FILTERED = [".jpg", ".gif", ".png", ".css"] # a list of file extensions to ignore
TARGET = "http://boodelyboo.com/wordpress" 
THREADS = 10

# initialize thread-safe first in, first out queues to store discovered URLs and paths
answers = queue.Queue()
web_paths = queue.Queue()

# gather local files
def gather_paths():
    for root, _, files in os.walk('.'): # talk recursively through all directories/files, starting at the current directory
        for fname in files: # loop through all files found
            if os.path.splitext(fname)[1] in FILTERED: # ignore files that have extension in the FILTERED list
                continue
            path = os.path.join(root, fname) # build the full path to the file
            if path.startswith('.'): # formatting, remove dots from the beginning of paths
                path = path[1:]
            print(path)
            web_paths.put(path) # push the path into the web_paths queue to be used later

# directory context manager
@contextlib.contextmanager # decorator that will allow the creation of enter and exit methods in a context manager
def chdir(path):
    # On enter, change directory to specified path.
    # On exit, change directory back to original
    this_dir = os.getcwd() # saves the cwd  
    os.chdir(path) # change into the target directory
    try:
        yield # pause the function midway
    finally:
        os.chdir(this_dir) # no matter what happens, change the working directory back to where it started

# test the server, each thread will run this function
def test_remote():
    while not web_paths.empty(): # continue looping while there are paths in the queue
        path = web_paths.get() # pull a path from the queue
        url = f'{TARGET}{path}' # combine the target url with the path
        time.sleep(2) # target may have a throttling/lockout timer, or a WAF
        r = requests.get(url) # send GET request to target url
        if r.status_code == 200: # 200 OK status code means file exists and is accessible
            answers.put(url) # saves valid url into 'answers' queue
            sys.stdout.write('+') # print '+' to indicate successful find
        else:
            sys.stdout.write('x') # indicates the url did not exist or was not accessible
        sys.stdout.flush() # force the output to render immediately without waiting for a newline

def run():
    mythreads = list()
    for i in range(THREADS):
        print(f'Spawning thread {i}')
        t = threading.Thread(target=test_remote)
        mythreads.append(t)
        t.start()

    for thread in mythreads:
        thread.join()

if __name__ == '__main__':
    with chdir("/home/john/Downloads/wordpress"):
        gather_paths()
    input('Press return to continue.')

    run()
    with open('myanswers.txt', 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')
    print('done')
