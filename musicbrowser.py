import os
import tty
import termios
import sys
import paramiko
import re

# j = scroll down
# k = scroll up
# l = enter folder
# h = go back
# } = page down
# [ = page up

#os.chdir('/Users/willkalb/Dropbox')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('example.com', username='your_username', password='your_password')
filepath = '/music/'
playpath = ''
message = ''
stdin, stdout, stderr = ssh.exec_command('cd ' + filepath + '; ls -F | sort -f')
#print stdout.read()

fileList = stdout.read().splitlines()#sorted(glob.glob('*'),key=str.lower)
#print fileList
rows, cols = os.popen('stty size', 'r').read().split()
rows = int(rows)
windowLength = rows-3
columns = int(cols)
#steps = raw_input('Steps? ')
#steps = int(steps)
steps = 0
cursor = 0
#print rows
#print fileList


# Prints out the contents of a directory that will fit in one terminal window
# s = number of steps of the size of the terminal window
# l = length of the window
# w = width of the window
# c = position of cursor
# m = message at bottom of screen
def fileprint(s,l,w,c,m):
    length = len(fileList)
   # if length < l:
   #     l=length
    q = 0
    for x in range((s*l), ((s+1)*l)):
        if x==c and x<length:
            q = x
            if len(fileList[x]) > w:
                print '> ' + fileList[x][:w-5] + '...'
            else:
                print '> ' + fileList[x]
        elif x < length:
            if len(fileList[x]) > w:
                print fileList[x][:w-3] +'...'
            else:
                print fileList[x]
        else:
            print '-'
    print '----------------'
    if len(m) > w:
        print m[:w-3] +'...'
    else:
        print m #filepath.rsplit('/', 2)[1] #filepath # + ' ' + str(len(fileList[q])) + ' ' + str(columns)

def getch():
        """getch() -> key character

        Read a single keypress from stdin and return the resulting character. 
        Nothing is echoed to the console. This call will block if a keypress 
        is not already available, but will not wait for Enter to be pressed. 

        If the pressed key was a modifier key, nothing will be detected; if
        it were a special function key, it may return the first character of
        of an escape sequence, leaving additional characters in the buffer.
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
# Initialize the file list with cursor at top
os.system('clear')
fileprint(steps,windowLength,columns,cursor+steps*windowLength,filepath.rsplit('/', 2)[1])

# Main loop.  Listens for keypresses and takes actions
# Eventually, keypresses will be replaced with GPIO
while 1:

    # Case wherein the items in the directory all fit on one screen
    if len(fileList)<windowLength:
        windowLength = len(fileList)
    # Get the typed character
    typed = getch()
    
    # Quit
    if typed == 'q':
        ssh.close()
        stdin.flush()
        break
    # Scroll down
    elif typed == 'k':
        if cursor < windowLength-1 and cursor + steps*windowLength < len(fileList)-1:
            cursor+=1
        elif cursor == windowLength-1 and cursor + steps*windowLength < len(fileList)-1:
            steps+=1
            cursor = 0
    # Scroll up
    elif typed == 'j':
        if cursor > 0:
            cursor-=1
        elif cursor == 0:
            if steps >0:
                steps-=1
                cursor = windowLength-1
    # Select
    elif typed == 'l':
        if fileList[cursor+steps*windowLength].endswith('/'):
            filepath += fileList[cursor+steps*windowLength]
            stdin, stdout, stderr = ssh.exec_command('cd ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',filepath) +'; ls -F | sort -f')
            fileList = stdout.read().splitlines()
            cursor = 0
            steps = 0
            windowLength = rows-3
            message = filepath.rsplit('/', 2)[1]
    # Up one directory
    elif typed == 'h':
        if filepath != '/music/':
            filepath = filepath.rsplit('/', 2)[0] + '/'
        stdin, stdout, stderr = ssh.exec_command('cd ' +re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1', filepath) + '; ls -F | sort -f')
        fileList = stdout.read().splitlines()
        cursor = 0
        steps = 0
        windowLength = rows-3
        message = filepath.rsplit('/', 2)[1]
    # Page down
    elif typed == ']':
        if (steps+1)*windowLength < len(fileList): 
            steps+=1
            cursor = 0
    # Page up
    elif typed == '[':
        if (steps-1)*windowLength >= 0:
            steps-=1
            cursor = 0
    # Play song or directory
    elif typed == 'p':
        if fileList[cursor+steps*windowLength].endswith('/'):
            playpath = filepath + fileList[cursor+steps*windowLength]           
            stdin, stdout, stderr = ssh.exec_command('cd ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',playpath) +'; for i in *.mp3; do lpr -Pbhmp3 "$i" ; done ; for j in *.m4a; do lpr -Pbhmp3 "$j" ; done')
            message = 'Playing directory: ' + fileList[cursor+steps*windowLength]
        else:
            playpath = filepath + fileList[cursor+steps*windowLength]
            stdin, stdout, stderr = ssh.exec_command('lpr -Pbhmp3 ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',playpath))
            message = playpath #'Playing: ' + fileList[cursor+steps*windowLength]
    # End a song
    elif typed == 'e':
        stdin, stdout, stderr = ssh.exec_command('lprm -Pbhmp3')
        message = 'Stopping current song'
    os.system('clear')
    windowLength = rows-3
    fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
