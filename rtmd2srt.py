# -*- coding: utf-8 -*-
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
parser.add_argument('infile',help='Put SOURCE XAVC S file path (ends with .MP4')
args = parser.parse_args()

'''
GENERAL RTMD tags FORMAT

TAG ID (2 bytes)
ver? (1 byte)
tag length (1 byte)
TAG value (length = tag length)
'''

def getfn():
#    k=0
#    j=0
#    k= 8*52
    k=sub.find('0x8000',bytealigned = True)
    if len(k) == 0 :
        fn = 'N/A'
#        print sub
        return fn
#    print k
#    j = k + 8*2
    sub.pos+=32
#    fn = sub[k:j].read('uint:16')
    fn = sub.read(16).uint
    fn= 2**((1-float(fn)/65536)*8)
    fn=round(fn,1)
    return str(fn)


def getdist():
#DIST TAG = 0x8001
    k=sub.find('0x8001',bytealigned = True)
    if len(k) == 0 :
        dist = 'N/A'
        return dist
    sub.pos+=32
    diste = sub.read('int:4')
    distm = sub.read('uint:12')
    dist = float(distm*(10**diste))
    if dist >= 65500 :
        dist = '∞'
    else: dist = str(dist)+'m'
    return dist
    

def getss():
#SHUTTER SPEED TAG = 0x8109, 2 parts by 4 bytes
#    k=0
#    j=0
#    k= 8*109 + delta1
    k = sub.find('0x8109',bytealigned = True)
    if len(k) == 0 :
        ss = 'N/A'
        return ss
#    j= k + 4*8
    sub.pos+=32
#    ss1 = sub[k:j].read('int:32')
#    ss2 = sub[k+4*8:j+4*8].read('int:32')
    ss1 = sub.read(32).uint
    ss2 = sub.read(32).uint
    ss = str(ss1) + '/' +str(ss2)
    return str(ss)

def getiso():
#ISO TAG = 0x810b, 
#    k=0
#    j=0
#    k= 8*127 + delta1
    k = sub.find('0x8115',bytealigned = True)
    if len(k) == 0:
        k = sub.find('0x810b',bytealigned = True)
    if len(k) == 0:
        iso = 'N/A'
        return iso
#    j= k + 2*8
    sub.pos+=32
#    iso = sub[k:j].read('uint:16')
    iso = sub.read(16).uint
    return str(iso)

def getdb():
#    k=0
#    j=0
#    k= 8*121 + delta1
    k = sub.find('0x810a',bytealigned = True)
    if len(k) == 0:
        db = 'N/A'
        return db
    sub.pos+=32
#    j= k + 2*8
#    db = sub[k:j].read('uint:16')/100
    db = sub.read(16).uint/100
    return str(db)

def getdz():
#    k=0
#    j=0
#    k= 8*121 + delta1
    k = sub.find('0x810c',bytealigned = True)
    if len(k) == 0:
        dz = 'N/A'
        return dz
    sub.pos+=32
#    j= k + 2*8
#    db = sub[k:j].read('uint:16')/100
    dz = float(sub.read(16).uint)/100
    return str(dz)

def getpasm():
    #k = 78*8+delta1
    k = sub.find('0x060E2B340401010B0510010101',bytealigned = True)
    if len(k) == 0:
        ae = 'N/A'
        return ae
    k = k[0]
    j = k+16*8
    if sub[k:j] ==   '0x060E2B340401010B0510010101010000' : ae = 'Exp. mode: M '
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

if s[:96] != '0x0000001C6674797058415643' :
    print 'No XAVC type tag detected. Please user original XAVC MP4 file. Exiting.'
    exit()

### NRT_Acquire START ###
filesize = os.path.getsize(F)

sampl_check = s.find('0x6D64617400000000', bytealigned=True)
if len(sampl_check) != 0:
    #sampl_string = '0x001c010000'
    s.bytepos+=16
    sampl_string = s.read(48)
    samples = s.findall(sampl_string, bytealigned=True)
    """
    elif len(sampl_check) == 0 :   
        sampl_check = s.find('0x0008010000', bytealigned=True)
        if len(sampl_check) != 0:
            #sampl_string = '0x0008010000'
            sampl_string = s.read(48)
            samples = s.findall(sampl_string, bytealigned=True)
    """
else:
    print 'No mdat tags detected. Probably you have corrupted XAVC file. Exiting.'
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

s = ConstBitStream(filename=F, offset = offset*8) #,length=(mmap.ALLOCATIONGRANULARITY),offset = offset
# Get mdhd
pos = s.find('0x6D646864',bytealigned=True)
s.read(32).hex
v = s.read(8).uint
s.read(24).hex
if v == 0:
    s.read(32).uint
else: s.read(64).uint
if v == 0:
    s.read(32).uint
else: s.read(64).uint
ts = s.read(32).uint #i.e. 30000 

if v == 0:
    tdur = s.read(32).uint
else: tdur = s.read(64).uint

#Get stts - 0x73747473
pos = s.find('0x73747473',bytealigned=True)
s.read(32).hex
v = s.read(8).uint
s.read(24).uint
s.read(32).uint
s.read(32).uint
sd = s.read(32).uint

sdur = float(sd)/float(ts) #each frame duration



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
        samples = (s.find(sampl_string[:-8], start = offset, bytealigned=True))
        #Debug# print 'Samples:', len(samples)
        #Debug# if samples [0]
        i = samples[0]
        #Debug# print i
        sub = s[i:(i+1024*8)]
#        if sub[54*8:55*8] != '0x06' and sub[134*8:135*8] !='0x06':
#           delta1 = 48
#        print sub
        fn = getfn()
        if 'ILCE' in modelname or 'FDR-AX7' in modelname: 
            dist=getdist()
        else: dist = 'N/A'
        ss=getss()
        iso=getiso()
        db = getdb()
        dz = getdz()
        ae=getpasm()

        c+=1
        #Debug# print c

        f.write (str(c) +'\n')
        f.write (str(sampletime(ssec,sdur)) + '\n')
        
        f.write ('Frame: ' + str(c) + '/' + duration + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
        f.write (ae +'  ISO: ' + str(iso) + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
        f.write ('D.zoom: '+dz+'x '+'Focus Distance: ' + dist + '\n')
        f.write ('\n')
        ssec=ssec+sdur
        offset = s.pos + 1024*8 - 8
        #Debug# print offset



    #Debug" print 'Last pos', i
    print 'Last frame processed:', c
    #Debug# print("type error: " + str(e))
print 'Success! SRT file created: ' + F[:-3]+'srt'


