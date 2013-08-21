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
# p = print song or directory
# e = end song
# - = volume down
# = = volume up

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

# Main loop.  Listens for keypresses and takes actions
# Eventually, keypresses will be replaced with GPIO
#try:
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
        stdout.flush()
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
    elif typed == 'h':
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
        if mode == 'files':
            stdin, stdout, stderr = ssh.exec_command('lprm -Pbhmp3')
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
    elif typed == '-':
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
    elif typed == '=':
        stdin, stdout, stderr = ssh.exec_command('volume-get')
        #message = stdout.read().split(' ')[0]
        volume = int(stdout.read().split(' ')[0])
        if volume < 180:
            volume = str(volume + 5)
            #message = 'Volume = ' + volume
            stdin, stdout, stderr = ssh.exec_command('volume-set set ' + volume)
            stdin, stdout, stderr = ssh.exec_command('volume-get')
            message = stdout.read().split(' ')[0]
    # Show queue
    elif typed == 'c':
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
    os.system('clear')
    windowLength = rows-3
    fileprint(steps,windowLength,columns,cursor+steps*windowLength,message)
#except:
#    print 'Something went wrong. :('
#    ssh.close()
#    stdin.flush()
#    stdout.flush()
