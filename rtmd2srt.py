import sys
import os
import re
import mmap
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
    if dist >= 65500 :
        dist = 'Inf.'
    else: dist = str(dist)+'m'
    return dist

def getdb():
    k=0
    j=0
    k= 8*121 + delta1
    j= k + 2*8
    db = sub[k:j].read('uint:16')/100
    return str(db)

def getsdur2(framemax):
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
        sdur = 1001.0/120000.0
    #print 'Debug: Framemax =',framemax
    return sdur

def getpasm():
    k = 78*8+delta1
    j = k+16*8
    if sub[k:j] == '0x060E2B340401010B0510010101010000' : ae = 'Exp. mode: M '
    elif sub[k:j] == '0x060E2B340401010B0510010101020000' : ae = 'Exp. mode: AUTO'
    elif sub[k:j] == '0x060E2B340401010B0510010101030000' : ae = 'Exp. mode: GAIN'
    elif sub[k:j] == '0x060E2B340401010B0510010101040000' : ae = 'Exp. mode: A'
    elif sub[k:j] == '0x060E2B340401010B0510010101050000' : ae = 'Exp. mode: S'
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

delta1 = 0

if not os.path.exists(args.infile) :
    print ('Error! Given input file name not found! Please check path given in CMD or set in script code!')
    sys.exit()

F = args.infile

print 'Opened file ' + F
print 'Analyzing...'
s = ConstBitStream(filename=F)

### NRT_Acquire START ###
filesize = os.path.getsize(F)

sampl_check = s.find('0x001c0100', bytealigned=True)
if len(sampl_check) != 0:
    sampl_string = '0x001c0100'
    samples = s.findall(sampl_string, bytealigned=True)
else:
    print 'No proper rtmd tags detected. Probably you have non-XAVCS file or XAVCS file from earlier camera (ex. ILCE-5100). Exiting.'
    exit()



all_the_data = open(F,'r+')
offset = (filesize/mmap.ALLOCATIONGRANULARITY-1)* mmap.ALLOCATIONGRANULARITY
m = mmap.mmap(all_the_data.fileno(),0,access=mmap.ACCESS_READ, offset = offset)

pattern = 'Duration value="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
duration = rx.findall(m)[0]

pattern = 'Device manufacturer="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
vendor = rx.findall(m)[0]

pattern = 'modelName="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
modelname = rx.findall(m)[0]

framemax = -1
for i in samples :
    frame = s[i+17*8:i+18*8].read('uint:8')
    if frame > framemax :
        framemax = frame
    else :

        break
        
sdur = getsdur2(framemax)

print 'Model Name:', vendor, modelname
print 'Video duration (frames):',duration
#print ffps

all_the_data.close()
### NRT_Acquire END ###

print 'Processing...'

ssec = 0
k=0
offset = 0
with open(F[:-3]+'srt', 'w') as f:

    for c in range(int(duration)):
        s = ConstBitStream(filename=F)
        #Debug# print s
        samples = (s.find(sampl_string, start = offset, bytealigned=True))
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
        if 'ILCE' in modelname or 'FDR-AX' in modelname: 
            dist=getdist()
        else: dist = 'N/A'
        c+=1
        
        #Debug# print c

        f.write (str(c) +'\n')
        f.write (str(sampletime(ssec,sdur)) + '\n')
        
        f.write ('Frame: ' + str(c) + '/' + duration + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
        f.write (ae +'  ISO: ' + str(iso) + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
        f.write ('Focus Distance: ' + dist + '\n')
        f.write ('\n')
        ssec=ssec+sdur
        offset = s.pos + 1024*8 - 8
        #Debug# print offset



    #Debug" print 'Last pos', i
    print 'Last frame processed:', c
    #Debug# print("type error: " + str(e))
print 'Success! SRT file created: ' + F[:-3]+'srt'


