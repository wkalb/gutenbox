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
typed = ''
keypressed = False
scrolling = False

# Set GPIO pins
GPIO.setmode(GPIO.BCM)
for x in range(0, len(pins)):
    #print pins[x]
    GPIO.setup(pins[x], GPIO.IN)

# Activate ssh client
ssh = paramiko.SSHClient()

# Get script file path
#dn = os.path.dirname(os.path.realpath(__file__))

# Open login file
# The login file should have the format "server,username,password,printer queue"
# Example: music.example.com,myuser,mypass,Pmyprinter
try:
    f = open('/home/pi/gutenbox/login.txt','r') # Change this to the relevant directory
    login = f.read().split(',')
# Get server and login information
    server = login[0]#raw_input('Server: ')
    user = login[1]#raw_input('Username: ')
    passwd = login[2]#raw_input('Password: ')
    printer = login[3]
except:
    print 'Login file not found. Create a login.txt file in the musicbroswer.py directory'
    print 'in the format: server,username,password,printer'
#print server
#print user
#print passwd

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(server, username=user, password=passwd)

# Change the following line to the top directory of your music folders.
filepath = '/music/'

playpath = ''
message = '' # Printed at the bottom of the screen following a button press.
mode = 'files' # Either 'files' for viewing files or 'queue' for viewing queue.
volume = 0

# Initialize the list of files.
stdin, stdout, stderr = ssh.exec_command('cd ' + filepath + '; ls -F | sort -f')
fileList = stdout.read().splitlines()#sorted(glob.glob('*'),key=str.lower)

# Get size of terminal display.
rows, cols = os.popen('stty size', 'r').read().split()
rows = int(rows)
windowLength = rows-3 # Number of lines to display, taking into account 'message'
columns = int(cols)

# Place cursor at top of list to start
steps = 0
cursor = 0

# Remembered values for going up one directory. Increments as you open directorys.
depth = 0

# Remembers your previous cursor position for going up a directory
prevsteps = [0]
prevcursor = [0]

# Button press variables.
timeclosed = 0 # Time a button is held down. Useful for timing long vs short presses
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
    os.system('clear')
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

# Obsolete method for getting keyboard input. Used for debugging.
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
    
# Print the starting directory file list with cursor at top
fileprint(steps,windowLength,columns,cursor+steps*windowLength,filepath.rsplit('/', 2)[1])

# Initialize the input string.  For the each button, 0 is unpressed and 1 is pressed.
for x in range (0, len(pins)):
    input.extend([0])
    previnput.extend([0])

drawscreen = True

# Main loop.  Listens for button presses and takes actions
try:
 while 1:
     
    for x in range (0, len(pins)):
        input[x]=GPIO.input(pins[x])
        
        # When key toggles from open to closed
        if ((not previnput[x]) and input[x]):
            keypressed = True
            #drawscreen = True
            timeclosed = millis()
        # When key toggles from closed to open
        if (previnput and (not input)):
            keypressed = False
            #drawscreen = True
            #timeopen = millis()
        if (millis()-timeclosed > 20) and keypressed: # 20 milliseconds to account for spring debounce
            if input[volup] == 0 and input[voldown] == 0:
                typed = 'queue'
#                message = 'queue'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[back]:
                typed = 'back'
#                message = 'back'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[scrolldown]:
                typed = 'scrolldown'
#                message = 'scrolldown'
                scrolling = True
#                print(message)
                keypressed = False
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
            elif input[scrollup]:
                typed = 'scrollup'
                keypressed = False
                scrolling = True
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
#                message = 'scrollup'
#                print(message)
            elif input[enter]:
                typed = 'enter'
#                message = 'enter'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[kill]:
                typed = 'kill'
#                message = 'kill'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif input[play]:
                typed = 'play'
#                message = 'play'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                keypressed = False
            elif not input[volup]:
                typed = 'volup'
#                message = 'volup'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)  
                keypressed = False
            elif not input[voldown]:
                typed = 'voldown'
#                message = 'voldown'
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)  
                keypressed = False
        elif (millis()-timeclosed > 1500): # Long button press
            if input[kill]:
                typed = 'killall'
        elif (millis()-timeclosed > 500) and scrolling: # long button press                 
            if input[scrolldown]:
                typed = 'pagedown'
#                message = 'pagedown'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                scrolling = False
            elif input[scrollup]:
                typed = 'pageup'
#                message = 'pageup'
#                print(message)
#                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
                scrolling = False
    # Case wherein the items in the directory all fit on one screen
    if len(fileList)<windowLength:
        windowLength = len(fileList)
    
    for x in range (0, len(pins)):
        previnput[x]=input[x]
    # Get the typed character
    #typed = getch()


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
            windowLength = rows - 3
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,filepath.rsplit('/', 2)[1])
        elif cursor == windowLength-1 and cursor + steps*windowLength < len(fileList)-1:
            steps+=1
            cursor = 0
            windowLength = rows- 3
            message = filepath.rsplit('/', 2)[1]
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Scroll up
    elif typed == 'scrollup':
        if cursor > 0:
            cursor-=1
            windowLength = rows- 3
            message = filepath.rsplit('/', 2)[1]
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
        elif cursor == 0:
            if steps >0:
                steps-=1
                cursor = windowLength-1
                windowLength = rows- 3
                message = filepath.rsplit('/', 2)[1]
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Select
    elif typed == 'enter':
        if len(fileList) > 0:
            if fileList[cursor+steps*windowLength].endswith('/') and mode == 'files':
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
                fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
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
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Page down
    elif typed == 'pagedown':
        if (steps+1)*windowLength < len(fileList): 
            steps+=1
            cursor = 0
            windowLength = rows- 3
            message = filepath.rsplit('/', 2)[1]
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Page up
    elif typed == 'pageup':
        if (steps-1)*windowLength >= 0:
            steps-=1
            cursor = 0
            windowLength = rows- 3
            message = filepath.rsplit('/', 2)[1]
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Play song or directory
    elif typed == 'play':
        if fileList[cursor+steps*windowLength].endswith('/'):
            playpath = filepath + fileList[cursor+steps*windowLength]           
            stdin, stdout, stderr = ssh.exec_command('cd ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',playpath) +'; for i in *.mp3*; do lpr -Pbhmp3 "$i" ; done ; for j in *.m4a*; do lpr -Pbhmp3 "$j" ; done')
            message = 'Playing directory: ' + fileList[cursor+steps*windowLength]
        else:
            playpath = filepath + fileList[cursor+steps*windowLength]
            if '.mp3' in playpath or'.m4a' in playpath:
                stdin, stdout, stderr = ssh.exec_command('lpr -Pbhmp3 ' + re.sub(r'([^a-zA-Z0-9_.-])', r'\\\1',playpath))
                message = 'Adding to queue: ' + fileList[cursor+steps*windowLength]
        windowLength = rows- 3
        fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # End a song
    elif typed == 'killall':
        stdin, stdout, stderr = ssh.exec_command('lpq -Pbhmp3')
        for i in range(0, len(stdout.read().splitlines()[2:])):
            stdin, stdout, stderr = ssh.exec_command('lprm -Pbhmp3')
            time.sleep(0.1)
        message = 'Clearing queue'
        windowLength = rows- 3
        fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    elif typed == 'kill':
        if mode == 'files':
            stdin, stdout, stderr = ssh.exec_command('su gutenbox; lprm -Pbhmp3')
            message = 'Stopping current song'
            windowLength = rows- 3
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
        elif mode == 'queue':
            songtokill = fileList[cursor+steps*windowLength]
            songtokill = songtokill.split()[1]
            stdin, stdout, stderr = ssh.exec_command('lprm -Pbhmp3 ' + songtokill)
            #time.sleep(0.05)
            stdin, stdout, stderr = ssh.exec_command('lpq -Pbhmp3')
            fileList = stdout.read().splitlines()[2:]
            for i in range(0, len(fileList)):
                killline = fileList[i].split()
                killline = killline[0] + ' ' + killline[2] + ' ' + killline[3] + ' ' + killline[4] + ' ' + killline[5]
                fileList[i] = killline
            cursor = 0
            steps = 0
            message = 'Stopping selected song'
            windowLength = rows- 3
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
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
        windowLength = rows- 3
        fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Volume up
    elif typed == 'volup':
        stdin, stdout, stderr = ssh.exec_command('volume-get')
        #message = stdout.read().split(' ')[0]
        volume = int(stdout.read().split(' ')[0])
        if volume < 100: # Set the maximum volume
            volume = str(volume + 5)
            #message = 'Volume = ' + volume
            stdin, stdout, stderr = ssh.exec_command('volume-set set ' + volume)
            stdin, stdout, stderr = ssh.exec_command('volume-get')
            message = stdout.read().split(' ')[0]
            windowLength = rows- 3
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
    # Show queue
    elif typed == 'queue':
        if mode == 'files':
            stdin, stdout, stderr = ssh.exec_command('lpq -Pbhmp3')
            fileList = stdout.read().splitlines()[2:]
            for i in range(0, len(fileList)):
                queueline = fileList[i].split()
                queueline = queueline[0] + ' ' + queueline[2] + ' ' + queueline[3] + ' ' + queueline[4] + ' ' + queueline[5]
                fileList[i] = queueline
            prevcursor.extend([cursor])
            prevsteps.extend([steps])
            depth += 1
            cursor = 0
            steps = 0
            windowLength = rows-3
            message = 'Upcoming songs'
            mode = 'queue'
            windowLength = rows- 3
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
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
            windowLength = rows- 3
            fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
   # os.system('clear')
    windowLength = rows-3
    typed = ''
   # if drawscreen:
   #     fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
   #     drawscreen = False

except KeyboardInterrupt:
    ssh.close()
    stdin.flush()
    stdout.flush()
#except:
#    print 'Something went wrong. :('
#    ssh.close()
#    stdin.flush()
#    stdout.flush()
