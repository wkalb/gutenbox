# Import the required module.                                                                
import RPi.GPIO as GPIO
import math
from datetime import datetime
from datetime import timedelta

startTime = datetime.now()

pinOut = 10
pinIn = 8

wpm = 13
debounceDelay = 20
dotTime = 1200/wpm
dashTime = 2.5 * dotTime
spaceTime = 5 * dotTime

morseTable = {'.----.': "'", 
        '-.--.-': '(', 
        '-.--.-': ')', 
        '--..--': ',', 
        '-....-': '-', 
        '.-.-.-': '.', 
        '-..-.': '/', 
        '-----': '0', 
        '.----': '1', 
        '..---': '2', 
        '...--': '3', 
        '....-': '4', 
        '.....': '5', 
        '-....': '6', 
        '--...': '7', 
        '---..': '8', 
        '----.': '9', 
        '---...': ':', 
        '-.-.-.': ';', 
        '..--..': '?', 
        '.-': 'A', 
        '-...': 'B', 
        '-.-.': 'C', 
        '-..': 'D', 
        '.': 'E', 
        '..-.': 'F', 
        '--.': 'G', 
        '....': 'H', 
        '..': 'I', 
        '.---': 'J', 
        '-.-': 'K', 
        '.-..': 'L', 
        '--': 'M', 
        '-.': 'N', 
        '---': 'O', 
        '.--.': 'P', 
        '--.-': 'Q', 
        '.-.': 'R', 
        '...': 'S', 
        '-': 'T', 
        '..-': 'U', 
        '...-': 'V', 
        '.--': 'W', 
        '-..-': 'X', 
        '-.--': 'Y', 
        '--..': 'Z', 
        '..--.-': '_'}


GPIO.setmode(GPIO.BOARD)

GPIO.setup(pinOut, GPIO.OUT)
GPIO.setup(pinIn, GPIO.IN)

def millis():
   dt = datetime.now() - startTime
   ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
   return ms

timeOpen = millis()
timeClosed = 0
input = 0
prevInput = 0
currentTime = 0
charTyped = 0
keyString = ''


GPIO.output(pinOut, GPIO.LOW)
while 1:
  input = GPIO.input(pinIn)
  
  # When key toggles from open to closed
  if ((not prevInput) and input):
     GPIO.output(pinOut, GPIO.HIGH)
    # if (math.fabs(timeClosed - timeOpen) > debounceDelay):
     charTyped = 1
     timeClosed = millis()
     #print 'key closed'
    # if (charTyped):
    #    if (millis() - timeOpen > spaceTime):
    #      #print ' '
    #       if keyString:
    #         print morseTable[keyString]
    #         keyString = ''
    #         charTyped = 0
        
  # When key toggles from closed to open
  if (prevInput and (not input)):
     GPIO.output(pinOut, GPIO.LOW)
     #if (math.fabs(timeClosed - timeOpen) > debounceDelay):
     charTyped = 1
     timeOpen = millis()
     #print 'key opened'
     if (charTyped):
        if (millis() - timeClosed > dashTime):
          #print '-'
          keyString += '-'
          charTyped = 0
        elif (millis() - timeClosed > debounceDelay):
          #print '.'
          keyString += '.'
          charTyped = 0
          
  # If enough time has passed, parse the keyString as a letter
  if (millis() - timeOpen > spaceTime):
    #print ' '
     if keyString in morseTable:
        print morseTable[keyString]
        keyString = ''
        charTyped = 0
     else:
        keyString = ''
        charTyped = 0
  prevInput = input
