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

# parsing and extending wordlists
def get_words(resume=None): # option to resume where a previous scan left off

    def extend_words(word):
        if "." in word: # if word already has an extension, leave it as is
            words.put(f'/{word}')
        else: # if no extension, add all extensions from the EXTENSIONS list
            for extension in EXTENSIONS:
                words.put(f'/{word}{extension}')

    with open(WORDLIST) as f:
        raw_words = f.read()

    found_resume = False
    words = queue.Queue()
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
    return words

def dir_bruter(words):
    headers = {'User-Agent': AGENT}
    while not words.empty():
        url = f'{TARGET}{words.get()}'
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            sys.stderr.write('x');sys.stderr.flush()
            continue

        if r.status_code == 200:
            print(f'\nSuccess ({r.status_code}: {url})')
        elif r.status_code == 404:
            sys.stderr.write('.');sys.stderr.flush()
        else:
            print(f'{r.status_code} => {url}')

if __name__ == '__main__':
    words = get_words()
    print('Press return to continue.')
    sys.stdin.readline()
    for _ in range(THREADS):
        t = threading.Thread(target=dir_bruter, args=(words,))
        t.start()
