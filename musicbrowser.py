import os
import tty
import termios
import sys
import paramiko
import re
import RPi.GPIO as GPIO
import time
import math
from datetime import datetime
from datetime import timedelta

# j = scroll down
# k = scroll up
# l = enter folder
# h = go back
# } = page down
# [ = page up
# p = print song or directory
# e = end song
# - = volume down
# = = volume up
# c = queue

# GPIO pins.  There are only eight pins, so volume controls
# work on two pins being activated at once.  Page up and 
# page down work by holding scrollup and scrolldown for a long
# button press.

# The pin numbers for the eight GPIO pins
pins = [4,17,27,22,18,23,24,25]
scrolldown = 0
scrollup = 1
enter = 2
back = 3
play = 4
kill = 5
voldown = 6
volup = 7
queue = [6,7]

keypressed = False
scrolling = False
GPIO.setmode(GPIO.BCM)
for x in range(0, len(pins)):
    print pins[x]
    GPIO.setup(pins[x], GPIO.IN)


ssh = paramiko.SSHClient()

# Get server and login information
server = raw_input('Server: ')
user = raw_input('Username: ')
passwd = raw_input('Password: ')

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(server, username=user, password=passwd)
filepath = '/music/'
playpath = ''
message = ''
mode = 'files' # Either 'files' for viewing files or 'queue' for viewing queue.
volume = 0
stdin, stdout, stderr = ssh.exec_command('cd ' + filepath + '; ls -F | sort -f')
#print stdout.read()

fileList = stdout.read().splitlines()#sorted(glob.glob('*'),key=str.lower)
#print fileList
rows, cols = os.popen('stty size', 'r').read().split()
rows = int(rows)
windowLength = rows-3
columns = int(cols)

steps = 0
cursor = 0

# Remembered values for going up one directory
depth = 0

prevsteps = [0]
prevcursor = [0]
#print rows
#print fileList


timeclosed = 0
input = []
previnput = []
currenttime = 0
starttime = datetime.now()
#charTyped = 0
#keyString = ''

# Time in milliseconds since an event. Used to determine long vs. short
# button presses.
def millis():
   dt = datetime.now() - starttime
   ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
   return ms

timeopen = millis()

# Prints out the contents of a directory that will fit in one terminal window
# s = number of steps of the size of the terminal window
# l = length of the window
# w = width of the window
# c = position of cursor
# m = message at bottom of screen
def fileprint(s,l,w,c,m):
    length = len(fileList)
    q = 0
    for x in range((s*l), ((s+1)*l)):
        if x==c and x<length:
            q = x
            if len(fileList[x]) > w-2:
                print '> ' + fileList[x][:w-5] + '...'
            else:
                print '> ' + fileList[x]
        elif x < length:
            if len(fileList[x]) > w-2:
                print '  ' + fileList[x][:w-5] + '...'
            else:
                print '  ' + fileList[x]
        else:
            print '  -'
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

# Initialize the input string.  For the eight keypresses, 0 is unpressed
# and 1 is pressed.
for x in range (0, len(pins)):
    input.extend([0])
    previnput.extend([0])


# Main loop.  Listens for keypresses and takes actions
# Eventually, keypresses will be replaced with GPIO
try:
 while 1:

    for x in range (0, len(pins)):
        input[x]=GPIO.input(pins[x])
        
        # When key toggles from open to closed
        if ((not previnput[x]) and input[x]):
            keypressed = True
            timeclosed = millis()
#            time.sleep(0.05)
            #os.system('clear')
#            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
        # When key toggles from closed to open
        if (previnput and (not input)):
            keypressed = False
#            time.sleep(0.05)
            #timeopen = millis()
        if (millis()-timeclosed > 20) and keypressed: # 20 milliseconds to account for debounce
            if input[volup] and input[voldown]:
                parsebutton('queue')
#                message = 'queue'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[back]:
                parsebutton('back')
#                message = 'back'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[scrolldown]:
                parsebutton('scrolldown')
#                message = 'scrolldown'
                scrolling = True
#                print(message)
                keypressed = False
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
            elif input[scrollup]:
                parsebutton('scrollup')
                keypressed = False
                scrolling = True
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
#                message = 'scrollup'
#                print(message)
            elif input[enter]:
                parsebutton('enter')
#                message = 'enter'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[kill]:
                parsebutton('kill')
#                message = 'kill'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[play]:
                parsebutton('play')
#                message = 'play'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[volup]:
                parsebutton('volup')
#                message = 'volup'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)  
                keypressed = False
            elif input[voldown]:
                parsebutton('voldown')
#                message = 'voldown'
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)  
                keypressed = False

        elif (millis()-timeclosed > 500) and scrolling: # long button press                 
            if input[scrolldown]:
                parsebutton('pagedown')
#                message = 'pagedown'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                scrolling = False
            elif input[scrollup]:
                parsebutton('pageup')
#                message = 'pageup'
#                print(message)
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                scrolling = False
    # Case wherein the items in the directory all fit on one screen
    if len(fileList)<windowLength:
        windowLength = len(fileList)
    
    for x in range (0, len(pins)):
        previnput[x]=input[x]
    # Get the typed character
    #typed = getch()
except KeyboardInterrupt:
    ssh.close()
    stdin.flush()
    stdout.flush()

def parsebutton(typed):    
    # Quit
#    if typed == 'q':
#        ssh.close()
#        stdin.flush()
#        stdout.flush()
#        break
    # Scroll down
    if typed == 'scrolldown':
        if cursor < windowLength-1 and cursor + steps*windowLength < len(fileList)-1:
            cursor+=1
        elif cursor == windowLength-1 and cursor + steps*windowLength < len(fileList)-1:
            steps+=1
            cursor = 0
    # Scroll up
    elif typed == 'scrollup':
        if cursor > 0:
            cursor-=1
        elif cursor == 0:
            if steps >0:
                steps-=1
                cursor = windowLength-1
    # Select
    elif typed == 'enter':
        if len(fileList) > 0:
            if fileList[cursor+steps*windowLength].endswith('/'):
                filepath += fileList[cursor+steps*windowLength]
                stdin, stdout, stderr = ssh.exec_command('cd ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',filepath) +'; ls -F | sort -f')
                fileList = stdout.read().splitlines()
                prevcursor.extend([cursor])
                prevsteps.extend([steps])
                depth += 1
                cursor = 0
                steps = 0
                windowLength = rows-3
                message = filepath.rsplit('/', 2)[1]
    # Up one directory
    elif typed == 'back':
        if filepath != '/music/':
            filepath = filepath.rsplit('/', 2)[0] + '/'
            stdin, stdout, stderr = ssh.exec_command('cd ' +re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1', filepath) + '; ls -F | sort -f')
            fileList = stdout.read().splitlines()
            cursor = prevcursor[depth]
            steps = prevsteps[depth]
            prevcursor = prevcursor[:depth]
            prevsteps = prevsteps[:depth]
            depth -= 1
            windowLength = rows-3
            message = filepath.rsplit('/', 2)[1]
    # Page down
    elif typed == 'pagedown':
        if (steps+1)*windowLength < len(fileList): 
            steps+=1
            cursor = 0
    # Page up
    elif typed == 'pageup':
        if (steps-1)*windowLength >= 0:
            steps-=1
            cursor = 0
    # Play song or directory
    elif typed == 'play':
        if fileList[cursor+steps*windowLength].endswith('/'):
            playpath = filepath + fileList[cursor+steps*windowLength]           
            stdin, stdout, stderr = ssh.exec_command('cd ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',playpath) +'; for i in *.mp3; do lpr -Pbhmp3 "$i" ; done ; for j in *.m4a; do lpr -Pbhmp3 "$j" ; done')
            message = 'Playing directory: ' + fileList[cursor+steps*windowLength]
        else:
            playpath = filepath + fileList[cursor+steps*windowLength]
            stdin, stdout, stderr = ssh.exec_command('lpr -Pbhmp3 ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',playpath))
            message = playpath #'Playing: ' + fileList[cursor+steps*windowLength]
    # End a song
    elif typed == 'kill':
        if mode == 'files':
            stdin, stdout, stderr = ssh.exec_command('su gutenbox; lprm -Pbhmp3')
            message = 'Stopping current song'
        elif mode == 'queue':
            songtokill = fileList[cursor+steps*windowLength]
            songtokill = songtokill.split()[2]
            stdin, stdout, stderr = ssh.exec_command('lprm -Pbhmp3 ' + songtokill)
            stdin, stdout, stderr = ssh.exec_command('lpq -Pbhmp3')
            fileList = stdout.read().splitlines()[2:]
            cursor = 0
            steps = 0
            message = 'Stopping selected song'
    # Volume down
    elif typed == 'voldown':
        stdin, stdout, stderr = ssh.exec_command('volume-get')
   #     message = stdout.read().split(' ')[0]                                                                                        
        volume = int(stdout.read().split(' ')[0])
        if volume > 5:
            volume = str(volume - 5)
           # message = 'Volume = ' + volume                                                                                          
        else:
            volume = str(0)
        stdin, stdout, stderr = ssh.exec_command('volume-set set ' + volume)
        stdin, stdout, stderr = ssh.exec_command('volume-get')
        message = stdout.read().split(' ')[0]
    # Volume up
    elif typed == 'volup':
        stdin, stdout, stderr = ssh.exec_command('volume-get')
        #message = stdout.read().split(' ')[0]
        volume = int(stdout.read().split(' ')[0])
        if volume < 100:
            volume = str(volume + 5)
            #message = 'Volume = ' + volume
            stdin, stdout, stderr = ssh.exec_command('volume-set set ' + volume)
            stdin, stdout, stderr = ssh.exec_command('volume-get')
            message = stdout.read().split(' ')[0]
    # Show queue
    elif typed == 'queue':
        if mode == 'files':
            stdin, stdout, stderr = ssh.exec_command('lpq -Pbhmp3')
            fileList = stdout.read().splitlines()[2:]
            prevcursor.extend([cursor])
            prevsteps.extend([steps])
            depth += 1
            cursor = 0
            steps = 0
            windowLength = rows-3
            message = 'Upcoming songs'
            mode = 'queue'
        else:
            stdin, stdout, stderr = ssh.exec_command('cd ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',filepath) +'; ls -F | sort -f')
            fileList = stdout.read().splitlines()
            cursor = prevcursor[depth]
            steps = prevsteps[depth]
            prevcursor = prevcursor[:depth]
            prevsteps = prevsteps[:depth]
            depth -= 1            
            mode = 'files'
            message = filepath.rsplit('/', 2)[1]
   # os.system('clear')
    windowLength = rows-3
#    typed = ''
#except:
#    print 'Something went wrong. :('
#    ssh.close()
#    stdin.flush()
#    stdout.flush()
