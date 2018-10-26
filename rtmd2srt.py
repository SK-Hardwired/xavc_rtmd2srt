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

RDD 18 tags from Mediainfo MXF parser (https://github.com/MediaArea/MediaInfoLib/blob/master/Source/MediaInfo/Multiple/File_Mxf.cpp):
0x3210: return "CaptureGammaEquation";
    060E2B34040101010401010101020000 = rec.709
    060E2B34040101010401010101030000 = SMPTE ST 240
    06.0E.2B.34.04.01.01.vv.0E.xx.xx.xx.xx.xx.xx.xx = custom
0x8000: return "IrisFNumber";
0x8001: return "FocusPositionFromImagePlane";
0x8002: return "FocusPositionFromFrontLensVertex";
0x8003: return "MacroSetting";
0x8004: return "LensZoom35mmStillCameraEquivalent";
0x8005: return "LensZoomActualFocalLength";
0x8006: return "OpticalExtenderMagnification";
0x8007: return "LensAttributes";
0x8008: return "IrisTNumber";
0x8009: return "IrisRingPosition";
0x800A: return "FocusRingPosition";
0x800B: return "ZoomRingPosition";
0x8100: return "AutoExposureMode";
0x8101: return "AutoFocusSensingAreaSetting";
0x8102: return "ColorCorrectionFilterWheelSetting";
0x8103: return "NeutralDensityFilterWheelSetting";
0x8104: return "ImageSensorDimensionEffectiveWidth";
0x8105: return "ImageSensorDimensionEffectiveHeight";
0x8106: return "CaptureFrameRate";
0x8107: return "ImageSensorReadoutMode";
0x8108: return "ShutterSpeed_Angle";
0x8109: return "ShutterSpeed_Time";
0x810A: return "CameraMasterGainAdjustment";
0x810B: return "ISOSensitivity";
0x810C: return "ElectricalExtenderMagnification";
0x810D: return "AutoWhiteBalanceMode";
0x810E: return "WhiteBalance";
0x810F: return "CameraMasterBlackLevel";
0x8110: return "CameraKneePoint";
0x8111: return "CameraKneeSlope";
0x8112: return "CameraLuminanceDynamicRange";
0x8113: return "CameraSettingFileURI";
0x8114: return "CameraAttributes";
0x8115: return "ExposureIndexofPhotoMeter";
0x8116: return "GammaForCDL";
0x8117: return "ASC_CDL_V12";
0x8118: return "ColorMatrix";
0xE000: UDAM ID (10 bytes)

unkn tags
E3 01 - ISO?

E3 04 - 8 bytes - date and time in YY-YY-MM-DD-HH-MM-SS format


'''

def getfn():
    k=sub.find('0x8000',bytealigned = True)
    if len(k) == 0 :
        fn = 'N/A'
        return fn
    sub.pos+=32
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
    k = sub.find('0x8109',bytealigned = True)
    if len(k) == 0 :
        ss = 'N/A'
        return ss
    sub.pos+=32
    ss1 = sub.read(32).uint
    ss2 = sub.read(32).uint
    ss = str(ss1) + '/' +str(ss2)
    return str(ss)

def getiso():
#ISO TAG = 0x810b,
    k = sub.find('0x8115',bytealigned = True)
    if len(k) == 0:
        k = sub.find('0x810b',bytealigned = True)
    if len(k) == 0:
        iso = 'N/A'
        return iso
    sub.pos+=32
    iso = sub.read(16).uint
    return str(iso)

def getdb():
    k = sub.find('0x810a',bytealigned = True)
    if len(k) == 0:
        db = 'N/A'
        return db
    sub.pos+=32
    db = sub.read(16).uint/100
    return str(db)

def getdz():
    k = sub.find('0x810c',bytealigned = True)
    if len(k) == 0:
        dz = 'N/A'
        return dz
    sub.pos+=32

    dz = float(sub.read(16).uint)/100
    return str(dz)

def getwbmode():
    k = sub.find('0x810d',bytealigned = True)
    if len(k) == 0:
        wb = 'N/A'
        return wb
    sub.pos+=32
    wb = sub.read(8).int
    if wb == 0:
        wb = 'Manual'
    elif wb == 1:
        wb = 'Auto'
    elif wb == 2:
        wb = 'Hold'
    elif wb == 3:
        wb = 'One Push'
    return str(wb)

def getaf():
    k = sub.find('0x8101',bytealigned = True)
    if len(k) == 0:
        wb = 'N/A'
        return af
    sub.pos+=32
    af = sub.read(8).int
    if af == 0:
        af = 'Manual'
    elif af == 1:
        af = 'Auto center'
    elif af == 2:
        af = 'Auto Whole'
    elif af == 3:
        af = 'Auto Multi'
    elif af == 4:
        af = 'Auto Spot'
    return str(af)

def gettime():
    k = sub.find('0xe304',bytealigned = True)
    if len(k) == 0:
        time = 'N/A'
        return time
    sub.pos+=40
    time = str(sub.read(16).hex)+'/'+str(sub.read(8).hex)+'/'+str(sub.read(8).hex)+' '+str(sub.read(8).hex)+':'+str(sub.read(8).hex)+':'+str(sub.read(8).hex)
    return str(time)


def getpasm():
    k = sub.find('0x8100',bytealigned = True)
    if len(k) == 0:
        ae = 'N/A'
        return ae
    sub.pos+=32
    ae = sub.read(16*8).hex
    if ae ==   '060e2b340401010b0510010101010000' : ae = 'Exp. mode: M '
    elif ae == '060e2b340401010b0510010101020000' : ae = 'Exp. mode: AUTO'
    elif ae == '060e2b340401010b0510010101030000' : ae = 'Exp. mode: GAIN'
    elif ae == '060e2b340401010b0510010101040000' : ae = 'Exp. mode: A'
    elif ae == '060e2b340401010b0510010101050000' : ae = 'Exp. mode: S'
    else : ae = 'N/A'
    return ae

def getge():
    k = sub.find('0x3210',bytealigned = True)
    if len(k) == 0:
        ge = 'N/A'
        return ge
    sub.pos+=32
    ge = sub.read(16*8).hex
    if ge ==   '060E2B34040101010401010101020000' : ge = 'Gamma: rec.709'
    elif ge == '060E2B34040101010401010101030000' : ge = 'Gamma: SMPTE ST 240M'
#    elif ge == '060e2b340401010b0510010101030000' : ge = 'Exp. mode: GAIN'
#    elif ge == '060e2b340401010b0510010101040000' : ge = 'Exp. mode: A'
#    elif ge == '060e2b340401010b0510010101050000' : ge = 'Exp. mode: S'
    else :
        ge = 'Gamma: Unkn'
    return ge

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

if not os.path.exists(args.infile) :
    print ('Error! Given input file name not found! Please check path given in CMD or set in script code!')
    sys.exit()

F = args.infile

print 'Opened file ' + F
print 'Analyzing...'
s = ConstBitStream(filename=F)

if s[:96] != '0x0000001C6674797058415643' :
    print 'No XAVC type tag detected. Please user original XAVC MP4 file. Exiting.'
    sys.exit()

### NRT_Acquire START ###
filesize = os.path.getsize(F)

sampl_check = s.find('0x6D64617400000000', bytealigned=True)
if len(sampl_check) != 0:
    s.bytepos+=12
    sampl_string = s.read(4*8)

else:
    print 'No mdat tags detected. Probably you have corrupted XAVC file. Exiting.'
    sys.exit()

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
pos = s.rfind('0x6D646864',bytealigned=True)
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
pos = s.rfind('0x73747473',bytealigned=True)
s.read(32).hex
v = s.read(8).uint
s.read(24).uint
s.read(32).uint
s.read(32).uint
sd = s.read(32).uint
sdur = float(sd)/float(ts) #each frame duration


print 'Model Name:', vendor, modelname
print 'Video duration (frames):',duration
print 'Framerate:', float(ts)/float(sd)

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
        offset = samples[0] + 1024*8
        i = samples[0]
        sub = s[i:(i+1024*8)]
        if '0x810a' not in sub and '0x9109' not in sub:
            continue
        fn = getfn()
        dist=getdist()
        ss=  getss()
        iso= getiso()
        db = getdb()
        #dz = getdz()
        ae=  getpasm()
        wb=  getwbmode()
        af=  getaf()
        time = gettime()
#        ge = getge()

        c+=1

        f.write (str(c) +'\n')
        f.write (str(sampletime(ssec,sdur)) + '\n')
        f.write ('Frame: ' + str(c) + '/' + duration + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
        f.write (ae +'  ISO: ' + str(iso) + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
        f.write ('WB mode: '+ wb + '  |  AF mode: ' + af + '\n')
        f.write ('Focus Distance: ' + dist  + '\n') #'D.zoom: '+dz+'x '+ + '  ' + ge
        f.write (time + '\n')
        f.write ('\n')
        ssec=ssec+sdur

    print 'Last frame processed:', c
print 'Success! SRT file created: ' + F[:-3]+'srt'
