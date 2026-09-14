/*** includes ***/



#define _DEFAULT_SOURCE //these macros make sure that the header files we use will work correctly
#define _BSD_SOURCE
#define _GNU_SOURCE

#include <ctype.h> //character classification and transformation
#include <errno.h> //error handling library
#include <fcntl.h>
#include <stdio.h> //standard library, user inputs and outputs to the screen or files
#include <stdarg.h>
#include <stdlib.h> //standard library, system utilities and memory management
#include <string.h> //library for string functions
#include <sys/ioctl.h> //input/output library that provides the ioctl() system call, which is an easy way to get the size of the terminal
#include <sys/types.h> //includes the POSIX system data types header file
#include <termios.h> //for terminal attribute management
#include <time.h>
#include <unistd.h> //Unix standard header, allows for direct communication with kernel



/*** defines ***/



#define KILO_VERSION "0.0.1"
#define KILO_TAB_STOP 8
#define KILO_QUIT_TIMES 3

#define CTRL_KEY(k) ((k) & 0x1f) //defines a macro CTRL_KEY(k or key). will change k into "key" and the hexadecimal for CTRL

enum editorKey { //defines human-readable names for non-character key presses. The numbers won't conflict with standard ASCII character codes. editorReadKey() will return these values when a listed special key below is pressed. editorProcessKeypress() and editorMoveCursor() use these values in switch statements to respond to user input
    BACKSPACE = 127,
    ARROW_LEFT = 1000,
    ARROW_RIGHT,
    ARROW_UP,
    ARROW_DOWN,
    DEL_KEY,
    HOME_KEY,
    END_KEY,
    PAGE_UP,
    PAGE_DOWN
};



/*** data ***/



typedef struct erow { //represents a single row of text. This is the core data structure for the contents of a file, edited line by line. Many functions will modify this struct to edit text
    int size;
    int rsize;
    char *chars;
    char *render;
} erow;

struct editorConfig{ //global editor state. Most functions will read from or write to this and is the ground truth from the program's state
    int cx, cy;
    int rx;
    int rowoff; //row offset variable to track what row of the file the user is scrolled to
    int coloff;
    int screenrows; //initializing global variables for the terminal size. we will call later getWindowSize() to fill them
    int screencols;
    int numrows; //initializing a place to store the number of rows from a file
    erow *row; //making a dynamically allocated array to load multiple lines from a file, so we're including a pointer to erow
    int dirty;
    char *filename;
    char statusmsg[80];
    time_t statusmsg_time;
    struct termios orig_termios; //saving a copy of the termios struct in its original state in a global variable. termios is a built in struct that holds terminal settings
};

struct editorConfig E; //the instantiated global editor state, named "E". The rest of the program will repeatedly read from and write to E



/*** prototypes ***/


//these prototypes are for the compiler. The compiler reads code top to bottom, by using prototypes I can write my functions slightly out of order, since I lot of my functions rely on a lot of other functions

void editorSetStatusMessage(const char *fmt, ...);
void editorRefreshScreen();
char *editorPrompt(char *prompt, void (*callback)(char *, int));



/*** terminal ***/



void die(const char *s) { //error handling, if a fatal error occurs it will clear the screen and print the error message at the top left
    
    //if an error occurs while rendering a screen, then we want to clear the screen and move the cursor to the top left. Then the error message will be at the top left
    
    write(STDOUT_FILENO, "\x1b[2J", 4); // Clear the screen. 4 = write 4 bytes to the terminal, \x1b[2J = VT100 escape sequence. J command is screen clearing. \x1b = escape character, [2J = clear the entire screen 
    write(STDOUT_FILENO, "\x1b[H", 3); /* Reposition cursor at top left corner. 3 = write 3 bytes to the terminal, \x1b[H = VT100 escape sequence. H command is cursor position. 
    \x1b = escape character, [H = move cursor to default position of 1, 1: or the top left corner */
    
    perror(s); //prints a descriptive error message, also gives context for what caused the error
    exit(1); //after printing error message, we exit returning a value of non-zero (indicating failure)
}

void disableRawMode() { //restores the state of the terminal before the program opened. Called when we exit the application. We stored the original terminal state in the E struct at &E.orig_termios
    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &E.orig_termios) == -1) 
        die("tcsetattr"); //STDIN_FILENO represents keyboard input, TCSAFLUSH applies changes cleanly by waiting until pending output is done. die() is error handling

}

void enableRawMode() { //raw mode will allow us to process key presses without the OS interpreting them first. Called at the start of main()
    if (tcgetattr(STDIN_FILENO, &E.orig_termios) == -1) die("tcgetattr"); //reads current terminal settings and saves them in global termios variable, die() is error handling
    atexit(disableRawMode); //restores the terminal settings when we exit, either by returning from main() or calling the exit() function
    
    struct termios raw = E.orig_termios; //saves current settings to the raw variable that we'll change, leaving the global variable alone
    raw.c_iflag &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON); //modifying settings, raw.c_iflag for input flags. ~(ICRNL | IXON) IXON turns off Ctrl-S, Ctrl-Q. ICRNL Ctrl-M to read correctly as 13 (carriage return)
    raw.c_oflag &= ~(OPOST); //turning off output processing. with output processing "\n" is translated to "\r\n" (carriage return followed by newline)
    raw.c_cflag |= (CS8); //sets the character size to 8 bits per byte, though this is almost certainly already set that way on all modern machines
    raw.c_lflag &= ~(ECHO | ICANON | IEXTEN | ISIG); /* modifying the settings we want to change, raw.c_lflag (local flags) is a bundle of bits inside the struct that contain terminal settings, 
    ~(ECHO | ICANON | IEXTEN | ISIG) flips the ECHO, canonical mode, bits off. IEXTEN disables Ctrl-V. ISIG disables Ctrl-C and Ctrl-Z */
    raw.c_cc[VMIN] = 0; //this sets the minimum number of bytes required to return read() to 0, meaning it will return after any input
    raw.c_cc[VTIME] = 1; //max amount of time read() will wait to return, measured in 1/10th seconds. No input = return 0

    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) die("tcsetattr"); //writes the new settings back to the terminal, die() is error handling

}

int editorReadKey() { //returns one key press from standard input. Switch statements handle escape sequences from non-character keys (like arrow keys). This will be called by editorProcessKeypress()
    int nread; //the success/failure of read() will be output as an integer, which will be stored here
    char c; //the keypress
    while ((nread = read(STDIN_FILENO, &c, 1)) != 1) { //STDIN_FILENO = keypress, &c = store at c pointer, 1 = only 1 keypress. Keep looping while successful
        if (nread == -1 && errno != EAGAIN) die("read"); //if nread() is unsuccessful and it isn't a harmless timeout (EAGAIN), kill with die() and give feedback about error (refer to die() function)
    }

    if (c == '\x1b') { //checking for an escape sequence
        char seq[3];

        if (read(STDIN_FILENO, &seq[0], 1) != 1) return '\x1b'; 
        if (read(STDIN_FILENO, &seq[1], 1) != 1) return '\x1b'; //if it's just the escape sequence (or the escape key), then return '\x1b'

        if (seq[0] == '[') { // the '[' indicates a VT100 control sequence, which will happen if an arrow key is pressed
	    if (seq[1] >= '0' && seq[1] <= '9') { //this checks if the next character is a number like '5' or '6'. Escape sequences for different keys will have different numbers/letters
		if (read(STDIN_FILENO, &seq[2], 1) != 1) return '\x1b';
		if (seq[2] == '~') {
		    switch (seq[1]) {
			case '1': return HOME_KEY; //HOME and END keys can be represented with different escape sequences depending on OS or terminal, we'll cover all the cases here and the next switch block
			case '3': return DEL_KEY;
			case '4': return END_KEY;
		        case '5': return PAGE_UP;
		        case '6': return PAGE_DOWN;
			case '7': return HOME_KEY;
			case '8': return END_KEY;
		    }
		}
	    } else {
                switch (seq[1]) {
	            case 'A': return ARROW_UP;
	            case 'B': return ARROW_DOWN;
	            case 'C': return ARROW_RIGHT;
	            case 'D': return ARROW_LEFT; //these check for the input being '\x1b[A' or '\x1b[B' or '\x1b[C' or '\x1b[D' (arrow keys)
		    case 'H': return HOME_KEY;
		    case 'F': return END_KEY;
	        }
	    }
        }

        return '\x1b'; //the fallback return
    } else {
    return c; //if the key pressed doesn't start with an escape character then it's just a normal key, return it as is
    }
}

int getCursorPosition(int *rows, int *cols) { //a backup plan to determine the terminal size. The primary method is ioctl(), which does it all by itself, but that doesn't work on all OS. This will be called in getWindowSize()
    char buf[32];
    unsigned int i = 0;

    if (write(STDOUT_FILENO, "\x1b[6n", 4) != 4) return -1; //the n command queries the terminal for information, the 6 argument asks for the cursor position

    while (i < sizeof(buf) - 1) { //this will read the cursor position into a buffer and stop at the end (it will end with an 'R')
    if (read(STDIN_FILENO, &buf[i], 1) != 1) break;
    if (buf[i] == 'R') break;
    i++;
    }
    buf[i] = '\0'; //printf expects strings to end with a '0' byte, so we make '\0' the last byte of the buffer

    printf("\r\n&buf[1]: '%s'\r\n", &buf[1]);
    
    if (buf[0] != '\x1b' || buf[1] != '[') return -1; //this makes sure it responded with an escape sequence
    if (sscanf(&buf[2], "%d;%d", rows, cols) != 2) return -1; //we pass a pointer to the third character of buf to sscanf skipping '/x1b' and '['. This will pass a string something like XX;XX. Then we tell it to look for 2 ints formatted with a semi colon in between and pass those to the variables "rows" and "cols"

    return 0;
}

int getWindowSize(int *rows, int *cols) { //find the number of rows and columns in the terminal. It's called by initEditor() to set the screen size in the E struct
    struct winsize ws; //storage for the window size

    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == -1 || ws.ws_col == 0) { //both -1 and 0 indicate failure
    if (write(STDOUT_FILENO, "\x1b[999C\x1b[999B", 12) != 12) return -1; //moving the cursor to the bottom right of the screen, "\x1b[999C\x1b[999B" uses a B and C command to move the cursor all the way to the right, then down to the bottom

    return getCursorPosition(rows, cols); //this is the beginning of finding the terminal window size for systems that can't use ioctl()

    } else { //if successful we will pass the values back from ioctl() by setting the int references that were passed to the function
        *cols = ws.ws_col;
        *rows = ws.ws_row;
        return 0;
    }
}



/*** row operations ***/



int editorRowCxToRx(erow *row, int cx) { //helps editorScroll() to correctly calculate the position of the cursor accounting for tabs. This converts an index for *char to an index for *render in the erow struct. The difference is that *render accounts for tabs being wider than one character
    int rx = 0;
    int j;
    for (j = 0; j < cx; j++) {
	if (row->chars[j] == '\t')
	    rx += (KILO_TAB_STOP - 1) - (rx % KILO_TAB_STOP);
	rx++;
    }
    return rx;
}

void editorUpdateRow(erow *row) { //updates the row->render string based on the content of row->chars. Converts tab characters to the appropriate number of spaces. Called whenever a row's content changes, like editorRowInsertChar() or editorInsertRow()
    int tabs = 0;
    int j;
    for (j = 0; j < row->size; j++) 
        if (row->chars[j] == '\t') tabs++;

    free(row->render);
    row->render = malloc(row->size + tabs*(KILO_TAB_STOP - 1) + 1);

    int idx = 0;
    for (j = 0; j < row->size; j++) {
	if (row->chars[j] == '\t') {
	    row->render[idx++] = ' ';
	    while (idx % KILO_TAB_STOP != 0) row->render[idx++] = ' ';
	} else {
	    row->render[idx++] = row->chars[j];
	}
    }
    row->render[idx] = '\0';
    row->rsize = idx;
}

int editorRowRxToCx(erow *row, int rx) { //converts a render index back to a character index, opposite of editorRowCxToRx(). Used by editorFindCallback() during search functions to place the cursor at the matching text
    int cur_rx = 0;
    int cx;
    for (cx = 0; cx < row->size; cx++) {
	if (row->chars[cx] == '\t')
	    cur_rx += (KILO_TAB_STOP - 1) - (cur_rx % KILO_TAB_STOP);
	cur_rx ++;

	if (cur_rx > rx) return cx;
    }
    return cx;
}

void editorInsertRow(int at, char *s, size_t len) { //stores a line of text from a file into the editor state. This function will call editorUpdateRow() to prepare rendering a new row. It will be called by editorOpen() to load files and editorInsertNewline() if the enter key is pressed
    if (at < 0 || at > E.numrows) return;

    E.row = realloc(E.row, sizeof(erow) * (E.numrows + 1));
     memmove(&E.row[at + 1], &E.row[at], sizeof(erow) * (E.numrows - at));

    E.row[at].size = len; //go to the newly made row and set its character count to "len"
    E.row[at].chars = malloc(len + 1); //allocate memory at E.row[at].chars to hold this line's characters, + 1 for the null-terminator
    memcpy(E.row[at].chars, s, len); //copy the string "s" to the newly allocated memory at E.row[at].chars
    E.row[at].chars[len] = '\0'; //add a null-terminator to the end of the string
    
    E.row[at].rsize = 0;
    E.row[at].render = NULL;
    editorUpdateRow(&E.row[at]);

    E.numrows++; //update the global row counter so the rest of the program knows we've added another line
    E.dirty++;
}

void editorFreeRow(erow *row) { //helper funciton for editorDelRow. Frees the memory allocated for an erow's chars and render pointers
    free(row->render);
    free(row->chars);
}

void editorDelRow(int at) { //deletes a row of text in the editor. Also used in editorDelChar() to merge lines when backspacing at the beginning of a line
    if (at < 0 || at >= E.numrows) return;
    editorFreeRow(&E.row[at]);
    memmove(&E.row[at], &E.row[at + 1], sizeof(erow) * (E.numrows - at - 1));
    E.numrows--;
    E.dirty++;
    
}

void editorRowInsertChar(erow *row, int at, int c) { //inserts a single character into an erow. It's called by editorInsertChar()
    if (at < 0 || at > row->size) at = row->size;
    row->chars = realloc(row->chars, row->size + 2);
    memmove(&row->chars[at + 1], &row->chars[at], row->size - at + 1);
    row->size++;
    row->chars[at] = c;
    editorUpdateRow(row);
    E.dirty++;
}

void editorRowAppendString(erow *row, char *s, size_t len) { //appends a string to the end of an erow
    row->chars = realloc(row->chars, row->size + len + 1);
    memcpy(&row->chars[row->size], s, len);
    row->size += len;
    row->chars[row->size] = '\0';
    editorUpdateRow(row);
    E.dirty++;
}

void editorRowDelChar(erow *row, int at) { //deletes a single character from an erow
    if (at < 0 || at >= row->size) return;
    memmove(&row->chars[at], &row->chars[at + 1], row->size - at);
    row->size--;
    editorUpdateRow(row);
    E.dirty++;
}



/*** editor operations ***/



void editorInsertChar(int c) { //uses editorRowInsertChar() to translate a key press into inserting a character at the cursor's position
    if (E.cy == E.numrows) {
	editorInsertRow(E.numrows, "", 0);
    }
    editorRowInsertChar(&E.row[E.cy], E.cx, c);
    E.cx++;
}

void editorInsertNewline() { //handles the enter key. Uses editorInsertRow() to create a new line and is prepared to move text to that new line if necessary
    if (E.cx == 0) {
	editorInsertRow(E.cy, "", 0);
    } else {
	erow *row = &E.row[E.cy];
	editorInsertRow(E.cy + 1, &row->chars[E.cx], row->size - E.cx);
	row = &E.row[E.cy];
	row->size = E.cx;
	row->chars[row->size] = '\0';
	editorUpdateRow(row);
    }
    E.cy++;
    E.cx = 0;
}

void editorDelChar() { //handles the backspace key. It either deletes a character with editorRowDelChar() or, if at the beginning of a line, merges lines with editorRowAppendString() and editorDelRow()
    if (E.cy == E.numrows) return;
    if (E.cx == 0 && E.cy == 0) return;

    erow *row = &E.row[E.cy];
    if (E.cx > 0) {
	editorRowDelChar(row, E.cx - 1);
	E.cx--;
    } else {
	E.cx = E.row[E.cy - 1].size;
	editorRowAppendString(&E.row[E.cy - 1], row->chars, row->size);
	editorDelRow(E.cy);
	E.cy--;
    }
}



/*** file input/output ***/



char *editorRowsToString(int *buflen) { //converts the array of erow structs into newline separated strings, ready to write to file. Will be called by editorSave()
    int totlen = 0;
    int j;
    for (j = 0; j < E.numrows; j++)
	totlen += E.row[j].size + 1;
    *buflen = totlen;

    char *buf = malloc(totlen);
    char *p = buf;
    for (j = 0; j < E.numrows; j++) {
	memcpy(p, E.row[j].chars, E.row[j].size);
	p += E.row[j].size;
	*p = '\n';
	p++;
    }

    return buf;
}

void editorOpen(char *filename) { //for loading a file from disk. It's called in main() if Kilo is opened with a filename as an argument
    free(E.filename);
    E.filename = strdup(filename);

    FILE *fp = fopen(filename, "r"); //opens the file in read-only mode
    if (!fp) die("fopen"); //if fp is NULL, run die() and print the error

    char *line = NULL; //this and the next 2 lines initialize variables for reading the file
    size_t linecap = 0;
    ssize_t linelen; 
    while ((linelen = getline(&line, &linecap, fp)) != -1) { //when getline() reaches the end of the file and runs out of lines to read, it will return -1, breaking the while loop
	while(linelen > 0 && (line[linelen - 1] == '\n' || 
			      line[linelen - 1] == '\r')) 
	    linelen--; //if the last character is a carriage return or newline, remove it by linelen--. we're already looking 1 line at a time manually with editorDrawRows
        editorInsertRow(E.numrows, line, linelen); //append the line of text to the editor state
    }
    free(line);
    fclose(fp);
    E.dirty = 0;
}

void editorSave() { //for saving your work. Saves the current buffer contents to a file on disk. If the file is unnamed then it will prompt the user for a name
    if (E.filename == NULL) {
	E.filename = editorPrompt("Save as: %s (ESC to cancel)", NULL);
	if (E.filename == NULL) {
	    editorSetStatusMessage("Save aborted");
	    return;
	}
    }

    int len;
    char *buf = editorRowsToString(&len);

    int fd = open(E.filename, O_RDWR | O_CREAT, 0644);
    if (fd != -1) {
	if (ftruncate(fd, len) != -1) {
	    if (write(fd, buf, len) == len) {
		close(fd);
		free(buf);
		E.dirty = 0;
		editorSetStatusMessage("%d bytes written to disk", len);
		return;
	    }
	}
	close(fd);
    }

    free(buf);
    editorSetStatusMessage("Can't save! I/O error: %s", strerror(errno));
}



/*** find***/



void editorFindCallback(char *query, int key) { //callback function that executes a line by line incremental search each time the user types a character in the search prompt
    static int last_match = -1;
    static int direction = 1;

    if (key == '\r' || key == '\x1b') {
	last_match = -1;
	direction = 1;
	return;
    } else if (key == ARROW_RIGHT || key == ARROW_DOWN) {
	direction = 1;
    } else if (key == ARROW_LEFT || key == ARROW_UP) {
	direction = -1;
    } else {
	last_match = -1;
	direction = 1;
    }

    if (last_match == -1) direction = 1;
    int current = last_match;
    int i;
    for (i = 0; i < E.numrows; i++) {
	current += direction;
	if (current == -1) current = E.numrows - 1;
	else if (current == E.numrows) current = 0;

	erow *row = &E.row[current];
	char *match = strstr(row->render, query);
	if (match) {
	    last_match = current;
	    E.cy = current;
	    E.cx = editorRowRxToCx(row, match - row->render);
	    E.rowoff = E.numrows;
	    break;
	}
    }
}

void editorFind() { //an incremental search function. It searches each erow, when a match is found the editor state is updated to bring the cursor to the matched text
    int saved_cx = E.cx;
    int saved_cy = E.cy;
    int saved_coloff = E.coloff;
    int saved_rowoff = E.rowoff;

    char *query = editorPrompt("Search: %s (Use ESC/Arrows/Enter)", editorFindCallback);

    if (query) {
	free(query);
    } else {
	E.cx = saved_cx;
	E.cy = saved_cy;
	E.coloff = saved_coloff;
	E.rowoff = saved_rowoff;
    }
}



/*** append buffer ***/



struct abuf { //a buffer for appending. I'll take everything I want to write() and put it all into this buffer so I can do one big write() to update the screen
    char *b;
    int len;
};


#define ABUF_INIT {NULL, 0} //this is the buffer where we'll store string characters


void abAppend(struct abuf *ab, const char *s, int len) { //appends strings to the abuf append buffer
    char *new = realloc(ab->b, ab->len + len); //resizes the memory block to include what it was + what we're adding
    if (new == NULL) return; //safety check, if there is no memory to store, then stop
    memcpy(&new[ab->len], s, len); //copy "len" bytes of the new string "s" and copy it to the end of our old string
    ab->b = new; //updates buffer pointer
    ab->len += len; //updates the character count
}

void abFree(struct abuf *ab) { //cleans up the memory that we allocated to the struct abuf
    free(ab->b);
}



/*** output ***/



void editorScroll() { //manages scrolling. If the cursor has moved outside the terminal window it scrolls the window up or down. It'll be called by editorRefreshScreen() to ensure the cursor is on the screen
    E.rx = 0;
    if (E.cy < E.numrows) {
	E.rx = editorRowCxToRx(&E.row[E.cy], E.cx);
    }

    if (E.cy < E.rowoff) {
	E.rowoff = E.cy;
    }
    if (E.cy >= E.rowoff + E.screenrows) {
	E.rowoff = E.cy - E.screenrows + 1;
    }
    if (E.cx < E.coloff) {
	E.coloff = E.rx;
    }
    if (E.cx >= E.coloff + E.screencols) {
	E.coloff = E.rx - E.screencols + 1;
    }
}

void editorDrawRows(struct abuf *ab) { //this function will render text in the editor. It loops through each row on the screen and appends file content from E.row or a ~ on empty lines. Will be called by editorRefreshScreen()
    int y;
    for (y = 0; y < E.screenrows; y++) { //E.screenrows will be filled in by getWindowSize(). loop through row 0 to the bottom of the screen
	    int filerow = y + E.rowoff;
	    if (filerow >= E.numrows) { //numrows is the number of rows in a file loaded from disk. This line checks whether there's something in the row 
            if (E.numrows == 0 && y == E.screenrows / 3) { //welcome message only displays if there's no file to load. if we're 1/3 of the way down the screen, write the welcome message
                char welcome[80]; //make space in memory for 80 bytes called welcome
                int welcomelen = snprintf(welcome, sizeof(welcome), //this variable assignment has a side effect, it writes our message to a buffer called "welcome" before saving the variable
                    "Kilo editor -- version %s", KILO_VERSION);
            if (welcomelen > E.screencols) welcomelen = E.screencols; //if the screen is too small, it cuts the end of the welcome message down to size
            int padding = (E.screencols - welcomelen) / 2; //centering the welcome message
            if (padding) {
                abAppend(ab, "~", 1);
                padding--;
            }
            while (padding--) abAppend(ab, " ", 1);
            abAppend(ab, welcome, welcomelen); //append the welcome message to our buffer
        } else {
            abAppend(ab, "~", 1); //one tilde will be drawn at the beginning of each row
        }
	} else { //if the row is NOT empty
	    int len = E.row[filerow].rsize - E.coloff; //store the length of the loaded text
	    if (len < 0) len = 0;
	    if (len > E.screencols) len = E.screencols; //if the line is wider than the terminal, chop off the overflow
	    abAppend(ab, &E.row[filerow].render[E.coloff], len); //append E.row.chars to the buffer
	}

        abAppend(ab, "\x1b[K", 3); //erases the entire line before redrawing it
	abAppend(ab, "\r\n", 2);
    }
}

void editorDrawStatusBar(struct abuf *ab) { //displays a status bar that will display information about the file. Will be called by editorRefreshScreen()
    abAppend(ab, "\x1b[7m", 4); //inverting the colors of the bar and the text to make it stand out
    char status [80], rstatus[80];
    int len = snprintf(status, sizeof(status), "%.20s - %d lines %s",
	E.filename ? E.filename : "[No Name]", E.numrows,
	E.dirty ? "(modified)" : "");
    int rlen = snprintf(rstatus, sizeof(rstatus), "%d/%d",
	E.cy + 1, E.numrows);
    if (len > E.screencols) len = E.screencols;
    abAppend(ab, status, len);
    while (len < E.screencols) {
	if (E.screencols - len == rlen) {
	    abAppend(ab, rstatus, rlen);
	    break;
	} else {
	   abAppend(ab, " ", 1);
	   len++;
	}
    }
    abAppend(ab, "\x1b[m", 3); //back to normal text formatting
    abAppend(ab, "\r\n", 2);
}

void editorDrawMessageBar(struct abuf *ab) { //displays temporary messages, for instance for the search function. Will be called by editorRefreshScreen()
    abAppend(ab, "\x1b[K", 3); //clears message bar
    int msglen = strlen(E.statusmsg);
    if (msglen > E.screencols) msglen = E.screencols;
    if (msglen && time(NULL) - E.statusmsg_time < 5) //display the message, but only if it's less than 5 seconds old
	abAppend(ab, E.statusmsg, msglen);
}

void editorRefreshScreen() { //render the editor's UI to the screen, this will be done after each keypress. I'll do this by storing commands in a buffer, then writing it all at once. Called in main()
    editorScroll();

    struct abuf ab = ABUF_INIT; //initialize a new buffer called "ab"

    abAppend(&ab, "\x1b[?25l", 6); //hide the cursor before refreshing the screen to avoid any flickering effects
    abAppend(&ab, "\x1b[H", 3); /* Reposition cursor at top left corner. 3 = write 3 bytes to the terminal, \x1b[H = VT100 escape sequence. H command is cursor position. 
    \x1b = escape character, [H = move cursor to default position of 1, 1: or the top left corner */

    editorDrawRows(&ab); //draw a column of tildes, one for each row
    editorDrawStatusBar(&ab);
    editorDrawMessageBar(&ab);

    char buf[32];
    snprintf(buf, sizeof(buf), "\x1b[%d;%dH", (E.cy - E.rowoff) + 1, (E.rx - E.coloff) + 1); //this moves the cursor to the position stored in our global config struct "E", we add 1 because the terminal is base 1
    abAppend(&ab, buf, strlen(buf)); //appending what we just stored to buf to our bulk write()

    abAppend(&ab, "\x1b[?25h", 6); //display the cursor again

    write(STDOUT_FILENO, ab.b, ab.len); //we write everything from the buffer to the screen
    abFree(&ab); //we free the memory used by the buffer
}

void editorSetStatusMessage(const char*fmt, ...) { //helper function for the various functions that show messages to the user. It formats the message and stores it in E.statusmsg
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(E.statusmsg, sizeof(E.statusmsg), fmt, ap);
    va_end(ap);
    E.statusmsg_time = time(NULL);
}



/*** input ***/



char *editorPrompt(char *prompt, void (*callback)(char *, int)) { //displays a prompt in the message bar and get input from the user (for saving or searching). Called by editorSave() and editorFind()
    size_t bufsize = 128;
    char *buf = malloc(bufsize);

    size_t buflen = 0;
    buf[0] = '\0';

    while(1) {
	editorSetStatusMessage(prompt, buf);
	editorRefreshScreen();

	int c = editorReadKey();
	if (c == DEL_KEY || c == CTRL_KEY('h') || c == BACKSPACE) {
	    if (buflen != 0) buf[--buflen] = '\0';
	} else if (c == '\x1b') {
	    editorSetStatusMessage("");
	    if (callback) callback (buf, c);
	    free(buf);
	    return NULL;
	} else if (c == '\r') {
	    if (buflen != 0) {
		editorSetStatusMessage("");
	        if (callback) callback (buf, c);
		return buf;
	    }
	} else if (!iscntrl(c) && c < 128) {
	    if (buflen == bufsize - 1) {
		bufsize *= 2;
		buf = realloc(buf, bufsize);
	    }
	    buf[buflen++] = c;
	    buf[buflen] = '\0';
	}

	if (callback) callback(buf, c);
    }
}

void editorMoveCursor(int key) { //moves the cursor with arrow key presses. It also prevents the cursor from going off screen or to invalid positions. Called by editorProcessKeypress()
    erow *row = (E.cy >= E.numrows) ? NULL : &E.row[E.cy];

    switch (key) {
	case ARROW_LEFT:
	    if (E.cx != 0) { //doing some bounds checking to make sure the cursor doesn't go off the screen
	        E.cx--;
	    } else if (E.cy > 0) {
		E.cy--;
		E.cx = E.row[E.cy].size;
	    }
	    break;
	case ARROW_RIGHT:
	    if (row && E.cx < row->size) {
	        E.cx++;
	    } else if (row && E.cx == row->size) {
		E.cy++;
		E.cx = 0;
	    }
	    break;
	case ARROW_UP:
	    if (E.cy != 0) {
	        E.cy--;
	    }
	    break;
	case ARROW_DOWN:
	    if (E.cy < E.numrows) {
	        E.cy++;
	    }
	    break;
    }

    row = (E.cy >= E.numrows) ? NULL : &E.row[E.cy];
    int rowlen = row ? row->size : 0;
    if (E.cx > rowlen) {
	E.cx = rowlen;
    }
}

void editorProcessKeypress() { //this function takes a keypress and decides what to do with it
    static int quit_times = KILO_QUIT_TIMES;

    int c = editorReadKey(); //call the keypress function and store the result in this local variable

    switch (c) { //look at the keypress inside c, we'll compare it to a special case
	case '\r':
	    editorInsertNewline();
	    break;

        case CTRL_KEY('q'): //was the keypress CTRL + q? if the user presses CTRL Q to quit, then we want to clear the screen and move the cursor to the top left
	    if (E.dirty && quit_times > 0) {
		editorSetStatusMessage("WARNING!!! File has unsaved changes. "
		    "Press Ctrl-Q %d more times to quit.", quit_times);
		quit_times--;
		return;
	    }
            write(STDOUT_FILENO, "\x1b[2J", 4); // Clear the screen. 4 = write 4 bytes to the terminal, \x1b[2J = VT100 escape sequence. J command is screen clearing. \x1b = escape character, [2J = clear the entire screen 
            write(STDOUT_FILENO, "\x1b[H", 3); /* Reposition cursor at top left corner. 3 = write 3 bytes to the terminal, \x1b[H = VT100 escape sequence. H command is cursor position. 
            \x1b = escape character, [H = move cursor to default position of 1, 1: or the top left corner */
            exit(0); //if so exit the program cleanly (returning 0 meaning success)
            break; //stop comparing to special cases

	case CTRL_KEY('s'):
	    editorSave();
	    break;

	case HOME_KEY: //move the cursor to the left side of the screen
	    E.cx = 0;
	    break;

	case END_KEY: //move the cursor to the right side of the screen
	    if (E.cy < E.numrows)
		E.cx = E.row[E.cy].size;
	    break;

	case CTRL_KEY('f'):
	    editorFind();
	    break;

	case BACKSPACE:
	case CTRL_KEY('h'):
	case DEL_KEY:
	    if (c == DEL_KEY) editorMoveCursor(ARROW_RIGHT);
	    editorDelChar();
	    break;

	case PAGE_UP: 
	case PAGE_DOWN: //run the following block of code if PAGE_UP or PAGE_DOWN is pressed
	    { //we have to use a bracket to declare a new variable in a switch block
		if (c == PAGE_UP) {
		    E.cy = E.rowoff;
		} else if (c == PAGE_DOWN) {
		    E.cy = E.rowoff + E.screenrows - 1;
		    if (E.cy > E.numrows) E.cy = E.numrows;
		}
		
		int times = E.screenrows;
		while (times--)
		    editorMoveCursor(c == PAGE_UP ? ARROW_UP : ARROW_DOWN);	    
	    }
	    break;

	case ARROW_UP: 
	case ARROW_DOWN:
	case ARROW_LEFT:
	case ARROW_RIGHT: //run the following code if an arrow key is pressed
	    editorMoveCursor(c);
	    break;

	case CTRL_KEY('l'):
	case '\x1b':
	    break;

	default:
	    editorInsertChar(c); //if a special key isn't pressed, then it's a character and should be rendered to the screen
	    break;
    }

    quit_times = KILO_QUIT_TIMES;
}



/*** init ***/



void initEditor() { //initialized the global editor state, which is contained in the struct "E". Called at the start of main()
    E.cx = 0;
    E.cy = 0;
    E.rx = 0;
    E.rowoff = 0; //by initializing row offset to 0, we'll be scrolled to the top of the file by default
    E.coloff = 0;
    E.numrows = 0;
    E.row = NULL;
    E.dirty = 0;
    E.filename = NULL;
    E.statusmsg[0] = '\0';
    E.statusmsg_time = 0;

    if (getWindowSize(&E.screenrows, &E.screencols) == -1) die("getWindowSize"); //fills in the screenrows and screencols in our global variable struct editorConfig
    E.screenrows -= 2;
}


int main(int argc, char *argv[]) { //our main function. We enable "raw mode" and initialize the editor. If a file name is given it opens it with editorOpen(). The while loop repeatedly calls editorRefreshScreen() and editorProcessKeypress() to run the editor.
    enableRawMode();
    initEditor();
    if (argc >= 2) {
	editorOpen(argv[1]);
    }

    editorSetStatusMessage("HELP: Ctrl-S = save | Ctrl-Q = quit | Ctrl-F = find");
    
    while (1) {
        editorRefreshScreen(); 
        editorProcessKeypress(); 
    } 

    return 0; 
}

