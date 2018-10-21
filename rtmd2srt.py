import sys
import os
import re
#import numpy as np
from bitstring import  ConstBitStream #BitArray, BitStream, pack, Bits,
from datetime import datetime, timedelta
#import gc

import argparse

parser = argparse.ArgumentParser(description='Extracts realtime meta-data from XAVC files and put to SRT (subtitle) file',)
parser.add_argument('infile',help='First file or filepath should be the source')
args = parser.parse_args()

def getfn():
    k=0
    j=0
    k= 8*52
    j = k + 8*2
    fn = sub[k:j].read('uint:16')
    fn= 2**((1-float(fn)/65536)*8)
    fn=round(fn,1)
    return str(fn)

def getss():
    k=0
    j=0
    k= 8*109 + delta1
    j= k + 4*8
    ss1 = sub[k:j].read('int:32')
    ss2 = sub[k+4*8:j+4*8].read('int:32')
    ss = str(ss1) + '/' +str(ss2)
    return str(ss)

def getiso():
    k=0
    j=0
    k= 8*127 + delta1
    j= k + 2*8
    iso = sub[k:j].read('uint:16')
    return str(iso)

def getdist():
    k=0
    j=0
    k= 8*52 + delta1
    j= k + 2*8
    diste = sub[k:j].read('int:4')
    distm = sub[k+4:j].read('uint:12')
    dist = float(distm*(10**diste))
    return str(dist)+'m'

def getdb():
    k=0
    j=0
    k= 8*121 + delta1
    j= k + 2*8
    db = sub[k:j].read('uint:16')/100
    return str(db)

def getsdur():
    if framemax == 59:
        sdur = 1001.0/60000.0
    elif framemax == 29:
        sdur = 1001.0/30000.0
    elif framemax == 49:
        sdur = 1.0/50.0
    elif framemax == 24:
        sdur = 1.0/25.0
    elif framemax == 23:
        sdur = 1001.0/24000.0
    elif framemax == 99:
        sdur = 1.0/100.0
    elif framemax == 119:
        sdur = 1.0/120.0
    print 'Max. frame = ' + str(framemax)
    return sdur

def getpasm():
    k = 78*8+delta1
    j = k+16*8
    if sub[k:j] == '0x060E2B340401010B0510010101010000' : ae = 'Manual exposure'
    elif sub[k:j] == '0x060E2B340401010B0510010101020000' : ae = 'Auto exposure'
    elif sub[k:j] == '0x060E2B340401010B0510010101030000' : ae = 'Gain priority'
    elif sub[k:j] == '0x060E2B340401010B0510010101040000' : ae = 'Aperture priority'
    elif sub[k:j] == '0x060E2B340401010B0510010101050000' : ae = 'Shutter priority'
    else : ae = 'N/A'
    return ae

def sampletime (ssec,sdur):
    sec = timedelta(seconds=float(ssec))
    delta = timedelta(seconds=float(sdur))
    d = datetime(1,1,1) + sec
    de = d+delta
    d=str(d).split(' ',1)[1]
    d=d.replace('.',',')
    de=str(de).split(' ',1)[1]
    de=de.replace('.',',')
    result =  d[:-3] + ' --> ' + de[:-3]
    return result

chunk = 16777216
progr = 0
delta1 = 0
framemax = -1

if not os.path.exists(args.infile) :
    print ('Error! Given input file name not found! Please check path given in CMD or set in script code!')
    sys.exit()


#F = "C:/Users/ruskugaa/Downloads/C0275.mp4"
#F = "D:/Temp/rtmd/C0002.MP4"
#F = "D:/Temp/rtmd/C0078.MP4"
F = args.infile

print 'Opened file ' + F
print 'Analyzing...'
s = ConstBitStream(filename=F)

samples = s.findall('0x001c0100', bytealigned=True) 
print 'Processing...'
#Debug# print len(tuple(samples))

#Find the frame rate by finding max frame counter at 0x11 of chunk. Use 
for i in samples :
    frame = s[i+17*8:i+18*8].read('uint:8')
    #print frame
    if frame > framemax :
        framemax = frame
    else :
        break

sdur = getsdur()

c=0
ssec = 0
k=0
offset = 0
with open(F[:-3]+'srt', 'w') as f:
    try:
        while True:
            s = ConstBitStream(filename=F)
            #Debug# print s
            samples = (s.find('0x001c0100', start = offset, bytealigned=True))
            #Debug# print 'Samples:', len(samples)
            #Debug# if samples [0]
            i = samples[0]
            #Debug# print i
            sub = s[i:(i+1024*8)]
            if sub[54*8:55*8] != '0x06' and sub[134*8:135*8] !='0x06':
                delta1 = 48

            fn = getfn()
            ss=getss()
            iso=getiso()
            db = getdb()
            ae=getpasm()
            if sub[54*8:55*8] != '0x06': 
                dist=getdist()
            else: dist = 'N/A'
            
            c=c+1
            #Debug# print c

            f.write (str(c) +'\n')
            f.write (str(sampletime(ssec,sdur)) + '\n')
            f.write (ae +'  ISO: ' + str(iso) + '   Gain: ' + str(db) +'db' + '   F' + str(fn) + '   Shutter: ' + str(ss) + '\n') # cut '  x8115: ' + x8115 +
            f.write ('Dist: ' + dist + '\n')
            f.write ('\n')
            ssec=ssec+sdur
            offset = s.pos + 1024*8 - 8
            #Debug# print offset

 
    except Exception as e :
        print 'Last pos', i
        print 'Last frame', c
        #Debug# print("type error: " + str(e))
print 'Success! SRT file created: ' + F[:-3]+'srt'
#Debug# gc.collect()
