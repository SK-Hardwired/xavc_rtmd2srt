# -*- coding: utf-8 -*-
import sys
import os
import re
import msvcrt
import io
import mmap
import subprocess
#import numpy as np
from bitstring import  ConstBitStream, BitArray #, BitStream, pack, Bits,
from datetime import datetime, timedelta
#import gc

import argparse

parser = argparse.ArgumentParser(description='Extracts realtime meta-data from XAVC files and put to SRT (subtitle) file',)

parser.add_argument('infile',help='Put SOURCE XAVC S file path (ends with .MP4')
parser.add_argument('-muxmkv', action='store_true', help='Key to mux meta-data srt stream into new MKV file with ffmpeg')
parser.add_argument('-sidecar', action='store_true', help='Key to mux meta-data srt stream into new MKV file with ffmpeg')

args = parser.parse_args()

print (args)

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

0x3219 = CaptureColorPrimaries (rec709, S-Logx, Rec2100-HLG, e.t.c.)
0x321A = Coding Equations = (rec.709, rec2020nc, e.t.c.)

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
0xE000: UDAM ID (10 bytes) ???

unkn tags
E3 00 - 1 byte - in XAVC S always = 00
E3 01 - 4 bytes - ISO?
E3 02 - 1 byte - in XAVC S always = 01
E3 03 - 1 byte - in XAVC S always = FF (255)
E3 04 - 8 bytes - Current record date and time in YY-YY-MM-DD-HH-MM-SS format

GPS tags

0x8500 - 4 bytes - gps version - 2.2.0.0 (02020000)
0x8501 - 1 byte - LatitudeRef - N (4e)
0x8502 - 18h bytes - Latitude - [4]/[4]:[4]/[4]:[4]/[4] = 09:09:09.123
0x8503 - 1 byte - LongtitudeRef - E (45)
0x8504 - 18h bytes - Longtitude - [4]/[4]:[4]/[4]:[4]/[4] = 09:09:09.123
0x8507 - 18h bytes - Timestamp - [4]/[4]:[4]/[4]:[4]/[4] = 09:09:09.123
0x8509 - 1 byte - STATUS - 'A' (if GPS not acquired, = 'V')
0x850a - 1 byte - MeasureMode - '2'
0x8512 - 6 bytes - MapDatum  - 57 47 53 2D 38 34 (WGS-84)
0x851d - 0a bytes - string (2018:10:30)



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
    dist = round(dist,4)
    if dist >= 65500 :
        dist = 'Inf.'
    else: dist = str(dist)+'m'
    return dist


def getss():
#SHUTTER SPEED TAG = 0x8109, 2 parts by 4 bytes
    k = sub.find('0x810900',bytealigned = True)
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
        k = sub.find('0x810b00',bytealigned = True)
    if len(k) == 0:
        iso = 'N/A'
        return iso
    sub.pos+=32
    iso = sub.read(16).uint
    return str(iso)

def getdb():
    k = sub.find('0x810a00',bytealigned = True)
    if len(k) == 0:
        db = 'N/A'
        return db
    sub.pos+=32
    db = sub.read(16).uint/100
    return str(db)

def getdz():
    k = sub.find('0x810c00',bytealigned = True)
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
    k = sub.find('0x810100',bytealigned = True)
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
    k = sub.find('0x810000',bytealigned = True)
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
    k = sub.find('0x321000',bytealigned = True)
    if len(k) == 0:
        ge = 'N/A'
        return ge
    sub.pos+=32
    ge = sub.read(16*8).hex
    if ge ==   '060e2b34040101010401010101020000' : ge = 'Gamma: rec709'
    elif ge == '060e2b34040101010401010101030000' : ge = 'Gamma: SMPTE ST 240M'
    elif ge == '060e2b340401010d0401010101080000' : ge = 'rec709-xvycc'
    elif ge == '060e2b34040101060e06040101010602' : ge = 'Still'
    elif ge == '060e2b34040101060e06040101010301' : ge = 'Cine1'
    elif ge == '060e2b34040101060e06040101010302' : ge = 'Cine2'
    elif ge == '060e2b34040101060e06040101010303' : ge = 'Cine3'
    elif ge == '060e2b34040101060e06040101010304' : ge = 'Cine4'
    elif ge == '060e2b34040101060e06040101010508' : ge = 'S-Log2'
    elif ge == '060e2b34040101060e06040101010605' : ge = 'S-Log3-Cine'
    elif ge == '060e2b34040101060e06040101010604' : ge = 'S-Log3'
    elif ge == '060e2b340401010d04010101010b0000' : ge = 'Rec2100-HLG'
    else :
        ge = 'Gamma: Unkn/Custom'

    sub.pos+=32
    cp = sub.read(16*8).hex
    if cp == '060e2b34040101060401010103030000' : ge = ge + '/rec709'
    elif cp == '060e2b34040101060e06040101030103' : ge = ge + '/S-Gamut'
    elif cp == '060e2b34040101060e06040101030104' : ge = ge + '/S-Gamut3'
    elif cp == '060e2b34040101060e06040101030105' : ge = ge + '/S-Gamut3.Cine'
    elif cp == '060e2b340401010d0401010103040000' : ge = ge + '/rec2020'

    return ge

def getgps():
    k = sub.find('0x8512',bytealigned = True)
    if len(k) == 0:
        gps = 'N/A'
        return gps
    sub.find('0x850000',bytealigned = True)
    sub.pos+=32
    gpsver = sub.read(4*8)

    sub.pos+=32
    latref = BitArray(sub.read(8))
    latref = latref.tobytes().decode('utf-8')
    sub.pos+=32
    l1 = sub.read(4*8).uint
    l2 = sub.read(4*8).uint
    l3 = sub.read(4*8).uint
    l4 = sub.read(4*8).uint
    l5 = sub.read(4*8).uint
    l6 = sub.read(4*8).uint

    if ( l2 == 0 or l4 == 0 or l6 == 0):
        gps = 'N/A'
        return gps

    #lat = str(l1/l2)  + '°' + str(l3/l4) + "'" + str(float(l5)/float(l6)) + '"'
    lat = str(round(l1/l2)) + '°' + str(round(l3/l4)) + "'" + str(round(float(l5)/float(l6))) + '"'

    sub.pos+=32
    lonref = BitArray(sub.read(8))
    lonref = lonref.tobytes().decode('utf-8')

    #k = sub.find('0x8504',bytealigned = True)
    #if len(k) == 0:
    #    gps = 'N/A'
    #    return ae
    sub.pos+=32
    l1 = sub.read(4*8).uint
    l2 = sub.read(4*8).uint
    l3 = sub.read(4*8).uint
    l4 = sub.read(4*8).uint
    l5 = sub.read(4*8).uint
    l6 = sub.read(4*8).uint

    if ( l2 == 0 or l4 == 0 or l6 == 0):
        gps = 'N/A'
        return gps

    #lon = str(l1/l2)  + '°' + str(l3/l4) + "'" + str(float(l5)/float(l6)) + '"'
    lon = str(round(l1/l2)) + '°' + str(round(l3/l4)) + "'" + str(round(float(l5)/float(l6))) + '"'

    sub.pos+=32
    l1 = sub.read(4*8).uint
    l2 = sub.read(4*8).uint
    l3 = sub.read(4*8).uint
    l4 = sub.read(4*8).uint
    l5 = sub.read(4*8).uint
    l6 = sub.read(4*8).uint

    if ( l2 == 0 or l4 == 0 or l6 == 0):
        gps = 'N/A'
        return gps

    gpsts = str(int(l1/l2))  + ':' + str(int(l3/l4)) + ":" + str(int(float(l5)/float(l6)))

    gps = lat + str(latref) + ' ' + lon + str(lonref) + ' ' + gpsts

    return gps

def sampletime (ssec,sdur):
    sec = timedelta(seconds=float(ssec))
    delta = timedelta(seconds=float(sdur))
    d = datetime(1,1,1) + sec
    de = d+delta
    d=str(d).split(' ',1)[1]
    d=d.replace('.',',')
    de=str(de).split(' ',1)[1]
    de=de.replace('.',',')
    if len(d) == 8: d = d + ',000000'
    if len(de) == 8: de = de + ',000000'
    result =  d[:-3] + ' --> ' + de[:-3]
    return result

def opt_sidecar():
    print ('Extracting sidecar...')
    pos = s.find('0x3C3F786D6C',bytealigned=True)
    if pos == ():
        print ('Error: No embedded Non-Realtime Metadata XML found!')
        return
    endpos = s.find('0x3C2F4E6F6E5265616C54696D654D6574613E',bytealigned=True)
    sidecar = s[pos[0]:(endpos[0]+18*8)]
    with open(F[:-3]+'XML', 'wb') as f:
        sidecar.tofile(f)
    print ('Sidecar XML created: ' + (F[:-3]+'XML'))

def opt_muxmkv():
    if os.path.isfile('ffmpeg.exe') == False :
        print ('')
        print ('Error: No ffmpeg.exe found. MuxMKV operation skipped.')
        exit()
    print ('Muxing new file with built-in subtitle')
    f = (F[:-3]+'srt')
    fout = (F[:-4]+'_sub.mkv')
    subprocess.call(['ffmpeg','-i',F,'-i',f,'-c','copy','-c:s','srt','-hide_banner','-y',fout]) #ccopy,cs,

#Main Program###

if not os.path.exists(args.infile) :
    print ('Error! Given input file name not found! Please check path given in CMD or set in script code!')
    sys.exit()

F = args.infile

print ('Opened file ' + F)

print ('Analyzing...')
s = ConstBitStream(filename=F)
if s[:96] != '0x0000001C6674797058415643' :
    print ('No XAVC type tag detected. Please user original XAVC MP4 file. Exiting.')
    sys.exit()

### NRT_Acquire START ###
filesize = os.path.getsize(F)

sampl_check = s.find('0x6D646174000000', bytealigned=True)
if len(sampl_check) != 0:
    #s.bytepos+=13
    #sampl_string = s.read(4*8)
    sampl_string = '0x001C01'
else:
    print ('No mdat tags detected. Probably you have corrupted XAVC file. Exiting.')
    sys.exit()

all_the_data = open(F,'rb')
offset = (int(filesize/mmap.ALLOCATIONGRANULARITY)-10)* mmap.ALLOCATIONGRANULARITY

m = mmap.mmap(all_the_data.fileno(),0,access=mmap.ACCESS_READ, offset = int(offset))
pattern = b'Duration value="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
duration = rx.findall(m)[0]

pattern = b'Device manufacturer="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
vendor = rx.findall(m)[0]

pattern = b'modelName="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
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


print ('Model Name:', vendor.decode(), modelname.decode())
print ('Video duration (frames):', duration.decode())
print ('Framerate:', float(ts)/float(sd))

if args.sidecar == True:
    opt_sidecar()

all_the_data.close()
### NRT_Acquire END ###

print ('Processing...')

ssec = 0
k=0
offset = 0

f = io.StringIO()

for c in range(int(duration)):
    s = ConstBitStream(filename=F)
    #Debug# print s
    samples = (s.find(sampl_string, start = offset, bytealigned=True))
    offset = samples[0] + 1024*8
    i = samples[0]
    sub = s[i:(i+1024*8)]
    if '0x060e2b340401010b05100101' not in sub :
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
    ge = getge()
    gps = getgps()


    c+=1

    f.write (str(c) +'\n')
    f.write (str(sampletime(ssec,sdur)) + '\n')
    f.write ('Frame: ' + str(c) + '/' + duration.decode() + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
    f.write (ae +'  ISO: ' + str(iso) + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
    f.write ('WB mode: '+ str(wb) + '  |  AF mode: ' + str(af) + '\n')
    if dist != 'N/A' :
        f.write ('Focus Distance: ' + dist + '\n') #'D.zoom: '+dz+'x '+ + '  ' + ge
    if gps != 'N/A' :
        #print (gps)
        f.write ('GPS: ' + gps + '\n')
    if ge != 'N/A' :
        f.write (ge  + '\n')
    #f.write (time + '\n')
    f.write ('\n')
    ssec=ssec+sdur

    sys.stdout.write('\rProcessed ' + str(c) + ' frames of ' + duration.decode() + '   (' + str(round(samples[0]/8/1000000))+'MB' + ' of ' + str(round(filesize/1000000)) + 'MB)')
    sys.stdout.flush()

    if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode():
        print ('\n \n Aborted! Saving processed data...')
        break

with open(F[:-3]+'srt', 'w') as outfile:
    outfile.write(f.getvalue())

f.close()

print ('\nLast frame processed:', c)
print ('Success! SRT file created: ' + F[:-3]+'srt')

if args.muxmkv:
    opt_muxmkv()
