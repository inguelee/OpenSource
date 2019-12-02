#import
import os
import math
import time
import busio
import board
import numpy as np
import pygame
from scipy.interpolate import griddata
from colour import Color
import adafruit_amg88xx
import RPi.GPIO as GPIO

#setting sensor
i2c_bus = busio.I2C(board.SCL, board.SDA)
MINTEMP = 0.
MAXTEMP = 40.
COLORDEPTH = 1024
os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()
sensor = adafruit_amg88xx.AMG88XX(i2c_bus)
points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]
height = 240
width = 240
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]
displayPixelWidth = width / 30
displayPixelHeight = height / 30

#setting moter
pin = 18 # PWM pin num 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)
p = GPIO.PWM(pin, 50)
p.start(0)

#setting weight
weight=[[10,8,6,5],
        [8,6,5,4],
        [6,5,4,3],
        [5,4,3,1]]

#function
def turn(x):
    for i in range(x):
        print(i)
        p.ChangeDutyCycle(2.5)
        time.sleep(0.13)
        p.ChangeDutyCycle(7)
        time.sleep(1)
        
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))
 
def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def mapping(pixels):
    result =[]
    for roomnum in range(2):
        for roomber in range(2):
            #empty room make
            room=[]
            for x in range(4):
                #empty list make
                num=[]
                for y in range(4):
                    #append number to list
                    num.append(pixels[y+roomber*32+roomnum*4+x*8])
                #append list to room
                room.append(num)
            #append room to result
            result.append(room)
    return result

def weighting(roomnumber):
    result = []
    if roomnumber == 0:
        for x in range(4):
            wlist=[]
            for y in range(4):
                wlist.append(weight[x][y])
            result.append(wlist)
            
    if roomnumber == 1:
        for x in range(4):
            wlist=[]
            for y in range(3,-1,-1):
                wlist.append(weight[x][y])
            result.append(wlist)
            
    if roomnumber == 2:
        for x in range(3,-1,-1):
            wlist=[]
            for y in range(4):
                wlist.append(weight[x][y])
            result.append(wlist)
            
    if roomnumber == 3:
        for x in range(3,-1,-1):
            wlist=[]
            for y in range(3,-1,-1):
                wlist.append(weight[x][y])
            result.append(wlist)
            
    return result

def sum(room, roomnumber):
    result = 0.0
    w = weighting(roomnumber)
    for x in range(4):
        for y in range(4):
            result += room[x][y]*w[x][y]
    return result


#lcd on
lcd = pygame.display.set_mode((width, height))
lcd.fill((255, 0, 0))
pygame.display.update()
pygame.mouse.set_visible(False)
lcd.fill((0, 0, 0))
pygame.display.update()

#program on

temp = 0
initial_temp = 0
hot_point = 0
turning_point = 0

try:
    while True:
        #read the pixels
        pixels = []
        for row in sensor.pixels:
            pixels = pixels + row
        pixels = [map_value(q, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for q in pixels]
     
        #perform interpolation
        bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
     
        #draw everything
        for ix, row in enumerate(bicubic):
            for jx, pixel in enumerate(row):
                pygame.draw.rect(lcd, colors[constrain(int(pixel), 0, COLORDEPTH- 1)],
                                 (displayPixelHeight * ix, displayPixelWidth * jx,
                                  displayPixelHeight, displayPixelWidth))
     
        pygame.display.update()

        rooms = mapping(pixels)
        if initial_temp == 1:
            initial_temp = 0
            temp = 0
        for index in range(4):
            roomvalue = sum(rooms[index],index)
            if roomvalue > temp:
                temp = roomvalue
                hot_point = index
                initial_temp += 1
                
             
        #if hot_point == 0:
            #r_point = 0
        #elif hot_point == 2:
         #   r_point = 1
        #elif hot_point == 3:
         #3   r_point = 2
        #elif hot_point == 1:
         #   r_point = 3
        
        print("hot_point:",hot_point)
        print("turning_point:",turning_point)
        
        if turning_point == 0:
            if hot_point == 1:
                turn(3)
            if hot_point == 2:
                turn(1)
            if hot_point == 3:
                turn(2)
            
        if turning_point == 1:
            if hot_point == 0:
                turn(1)
            if hot_point == 2:
                turn(2)
            if hot_point == 3:
                turn(3)
                
                
        if turning_point == 2:
            if hot_point == 0:
                turn(3)
            if hot_point == 1:
                turn(2)
            if hot_point == 3:
                turn(1)
        
                
        if turning_point == 3:
            if hot_point == 0:
                turn(2)
            if hot_point == 1:
                turn(1)
            if hot_point == 2: 
                turn(3)

        time.sleep(0.1)
        turning_point = hot_point
        p.stop()
        p.start(0)
        

        
except:
    pass

p.stop()
GIOP.cleanup()
