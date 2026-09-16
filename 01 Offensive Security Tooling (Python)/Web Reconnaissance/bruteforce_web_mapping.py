# multi-threaded web directory and file brute-forcer that iterates through a text-based wordlist, appends specific target file extensions, 
# and fires automated HTTP GET requests with custom User-Agent headers to discover hidden endpoints on a web server

import queue
import requests
import threading
import sys

AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0" # spoofed user agent string to make us look like a normal browser
EXTENSIONS = ['.php', '.bak', '.orig', '.inc'] # list of extensions that we will automatically append to words that don't have extensions
TARGET = "http://testphp.vulnweb.com"
THREADS = 50
WORDLIST = "/home/john/Downloads/all.txt"

# parsing and extending wordlist words
def get_words(resume=None): # option to resume where a previous scan left off

    def extend_words(word):
        if "." in word: # if word already has an extension, leave it as is
            words.put(f'/{word}') # put in the words queue
        else: # if no extension, add all extensions from the EXTENSIONS list
            for extension in EXTENSIONS:
                words.put(f'/{word}{extension}') # put in the words queue

    with open(WORDLIST) as f: # opens wordlist and reads file into raw_words variable for extend_words() to use later
        raw_words = f.read()

    found_resume = False # flag for stopping and starting
    words = queue.Queue() # initializes a thread safe queue
    for word in raw_words.split():
        if resume is not None:
            if found_resume:
                extend_words(word)
            elif word == resume:
                found_resume = True
                print(f'Resuming wordlist from:{resume}')
        else:
            print(word)
            extend_words(word)
    return words # return the queue that is now full of words with extensions

# brute forcer that will be executed by threads
def dir_bruter(words):
    headers = {'User-Agent': AGENT} # instantiates our spoofed browser user-agent header
    while not words.empty(): # loops while there is something in the queue
        url = f'{TARGET}{words.get()}' # pulls the next url from the queue
        try:
            r = requests.get(url, headers=headers) # send a GET request to the url
        except requests.exceptions.ConnectionError: # catches any network errors (from using 50 threads, which can be a lot)
            sys.stderr.write('x');sys.stderr.flush() # print an 'x' to the terminal
            continue # move on to next item in the queue

        if r.status_code == 200:
            print(f'\nSuccess ({r.status_code}: {url})') # prints success banner with url
        elif r.status_code == 404:
            sys.stderr.write('.');sys.stderr.flush() # prints a dot to the terminal and moves on
        else:
            print(f'{r.status_code} => {url}') # prints the unique status code as well as the url for manual investigation

if __name__ == '__main__':
    words = get_words() # read the wordlist, add extensions, and populate the queue
    print('Press return to continue.')
    sys.stdin.readline() # blocking state, waiting for the enter key to actually perform the brute forcing
    for _ in range(THREADS): # create 50 threads (or whatever our THREADS variable is)
        t = threading.Thread(target=dir_bruter, args=(words,)) # the threads will execute the dir_bruter passing the queue as an argument
        t.start()
