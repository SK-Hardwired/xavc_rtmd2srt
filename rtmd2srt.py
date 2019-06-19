# -*- coding: utf-8 -*-
import os

#multi-platform keyboard intercept load
if os.name == 'nt':
    import msvcrt
else:
    import select
import sys
import re
import io
import mmap
import math
import subprocess
import bitstring
from bitstring import  ConstBitStream, BitArray #, BitStream, pack, Bits,
from datetime import datetime, timedelta
import argparse
import gpxpy
import gpxpy.gpx
#import gpxpy.gpx as mod_gpx

try:
    import lxml.etree as mod_etree  # Load LXML or fallback to cET or ET
except:
    try:
        import xml.etree.cElementTree as mod_etree
    except:
        import xml.etree.ElementTree as mod_etree

#Variables



parser = argparse.ArgumentParser(description='Extracts realtime meta-data from XAVC files and put to SRT (subtitle) file',)

parser.add_argument('infile',help='Put SOURCE XAVC S file path (ends with .MP4')
parser.add_argument('-muxmkv', action='store_true', help='Key to mux meta-data srt stream into new MKV file with ffmpeg')
parser.add_argument('-sidecar', action='store_true', help='Key to generate XML sidecar file from XAVC S file (if you lost original XML sidecar written by camera)')
parser.add_argument('-gpx', action='store_true', help='Write GPX Track file if GPS data available')
parser.add_argument('-check',action='store_true', help='Just output some basic file data')

args = parser.parse_args()

#print (args)

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
    try:
        sub.pos+=32
        diste = sub.read('int:4')
        distm = sub.read('uint:12')
        dist = float(distm*(10**diste))
        dist = round(dist,4)
        if dist >= 65500 :
            dist = 'Inf.'
        else: dist = str(dist)+'m'
    except (bitstring.ReadError, ValueError) : return 'N/A'
    return dist


def getss():
#SHUTTER SPEED TAG = 0x8109, 2 parts by 4 bytes
    k = sub.find('0x810900',bytealigned = True)
    if len(k) == 0 :
        ss = 'N/A'
        return ss
    try:
        sub.pos+=32
        ss1 = sub.read(32).uint
        ss2 = sub.read(32).uint
    except (bitstring.ReadError, ValueError) : return 'N/A'
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
    try:
        sub.pos+=32
        iso = sub.read(16).uint
    except (bitstring.ReadError, ValueError, UnicodeDecodeError) : return 'N/A'
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
    try:
        sub.pos+=32
        wb = sub.read(8).int
        if wb == 0:
            wb = 'Man'
        elif wb == 1:
            wb = 'Auto'
        elif wb == 2:
            wb = 'Hold'
        elif wb == 3:
            wb = 'One Push'
    except (bitstring.ReadError, ValueError, UnicodeDecodeError) : return 'N/A'
    return str(wb)

def getaf():
    k = sub.find('0x810100',bytealigned = True)
    if len(k) == 0:
        af = 'N/A'
        return af
    sub.pos+=32
    af = sub.read(8).int
    if af == 0:
        af = 'MF'
    elif af == 1:
        af = 'AF Center'
    elif af == 2:
        af = 'AF Whole'
    elif af == 3:
        af = 'AF Multi'
    elif af == 4:
        af = 'AF Spot'
    return str(af)

def gettime():
    k = sub.find('0xe304',bytealigned = True)
    if len(k) == 0:
        time = 'N/A'
        return time
    try:
        sub.pos+=40
        time = str(sub.read(16).hex)+'/'+str(sub.read(8).hex)+'/'+str(sub.read(8).hex)+' '+str(sub.read(8).hex)+':'+str(sub.read(8).hex)+':'+str(sub.read(8).hex)
    except (bitstring.ReadError, UnicodeDecodeError) : return 'N/A'
    return str(time)


def getpasm():
    k = sub.find('0x810000',bytealigned = True)
    if len(k) == 0:
        ae = 'N/A'
        return ae
    sub.pos+=32
    ae = sub.read(16*8).hex
    if ae ==   '060e2b340401010b0510010101010000' : ae = 'Exp.mode: M '
    elif ae == '060e2b340401010b0510010101020000' : ae = 'Exp.mode: AUTO'
    elif ae == '060e2b340401010b0510010101030000' : ae = 'Exp.mode: GAIN'
    elif ae == '060e2b340401010b0510010101040000' : ae = 'Exp.mode: A'
    elif ae == '060e2b340401010b0510010101050000' : ae = 'Exp.mode: S'
    else : ae = 'N/A'
    return ae

def getge():
    k = sub.find('0x321000',bytealigned = True)
    if len(k) == 0:
        ge = 'N/A'
        return ge
    try:
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
        else :
            cp == 'ColorSpace Unkn/Custom'
    except (bitstring.ReadError, ValueError) : return 'N/A'
    return ge

'''
GPS tags

0x8500 - 4 bytes - gps version - 2.2.0.0 (02020000)
0x8501 - 1 byte - LatitudeRef - N (4e)
0x8502 - 18h bytes - Latitude - [4]/[4]:[4]/[4]:[4]/[4] = 09:09:09.123
0x8503 - 1 byte - LongtitudeRef - E (45)
0x8504 - 18h bytes - Longtitude - [4]/[4]:[4]/[4]:[4]/[4] = 09:09:09.123
0x8505 - 1 byte - AltitudeRef  (equal to 1)
0x8506 - 8 bytes - Altitude (meters) ([4]/[4]???). Second [4] almost always = 1000 dec
0x8507 - 18h bytes - Timestamp - [4]/[4]:[4]/[4]:[4]/[4] = 09:09:09.123
0x8509 - 1 byte - STATUS - 'A' (if GPS not acquired, = 'V')
0x850a - 1 byte - MeasureMode - (2 = 2D, 3 = 3D)
0x850b - 8 bytes - DOP ([4]/[4]???). Second [4] almost always = 1000 dec
read 0x850c -  1 byte - SpeedRef (K = km/h, M = mph, N = knots)
read 0x850d - 8 bytes ([4]/[4]???) - SPEED
read 0x850e - 1 byte - TrackRef (Direction Reference, T = True direction, M = Magnetic direction)
read 0x850f - Direction 8 bytes ([4]/[4]???) (degrees from 0.0 to 359.99)
0x8512 - 6 bytes - MapDatum  - 57 47 53 2D 38 34 (WGS-84)
0x851d - 0a bytes - string (2018:10:30)

used in GPX:
lat (calculated from latref and lat)
lon (calculated from lonref and lon)
time (timestamp = date+timestamp in UTZ format)
MeasureMode
speed (in GPX 1.0 only!)
altitude (calculated from altref and alitude)
DOP (?HDOP, VDOP, PDOP?)


'''

def getgps(old_dt):
#    k = sub.find('0x851200',bytealigned = True)
#    if len(k) == 0:
#        gps = 'N/A'
#        return gps
    sub.find('0x85000004',bytealigned = True)

    sub.pos+=32
    #read 0x850000 - GPS Ver
    gpsver = sub.read(4*8)

    sub.pos+=32
    #read 0x8501 - Latitude Ref (N or S)
    latref = BitArray(sub.read(8))
    latref = latref.tobytes().decode('utf-8')
    sub.pos+=32
    # read 0x8502 - latiture (6 chunks)
    l1 = sub.read(4*8).uint
    l2 = sub.read(4*8).uint
    l3 = sub.read(4*8).uint
    l4 = sub.read(4*8).uint
    l5 = sub.read(4*8).uint
    l6 = sub.read(4*8).uint

    if ( l2 == 0 or l4 == 0 or l6 == 0):
        gps = 'N/A'
        return gps

    #write latitute string for text output
    lat = str(l1/l2) + '°' + str(l3/l4) + "'" + str(float(l5)/float(l6)) + '"'
    latdd = round((float(l1)/float(l2) + (float(l3)/float(l4))/60 + (float(l5)/float(l6)/(60*60)) * (-1 if latref in ['W', 'S'] else 1)), 7)

    sub.pos+=32
    #read 0x8503 - longtitude ref (E or W)
    lonref = BitArray(sub.read(8))
    lonref = lonref.tobytes().decode('utf-8')
    # read 0x8504 - lontgiture (6 chunks)
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

    #write latitute string for text output
    lon = str(float(l1)/float(l2)) + '°' + str(float(l3)/float(l4)) + "'" + str(float(l5)/float(l6)) + '"'
    londd = round((float(l1)/float(l2) + float(l3)/float(l4)/60 + (float(l5)/float(l6)/(60*60)) * (-1 if lonref in ['W', 'S'] else 1)), 7)
    k = sub.find('0x85050001',bytealigned = True)
    if len(k) != 0 :
        sub.pos+=32
        #read 0x8505 - 1 bytes = AltitudeRef (0 = above sea level, 1 = below sea level)
        x8505 = sub.read (8).uint

        sub.pos+=32
        #read 0x8506 - 8 bytes ([4]/[4]) - Altitude
        x8506_1 = sub.read(4*8).uint
        x8506_2 = sub.read(4*8).uint

        x8506 = str(float(x8506_1)/float(x8506_2))
    else : x8505 = None

    sub.pos+=32
    # read 0x8507 - timestamp (6 chunks)
    l1 = sub.read(4*8).uint
    l2 = sub.read(4*8).uint
    l3 = sub.read(4*8).uint
    l4 = sub.read(4*8).uint
    l5 = sub.read(4*8).uint
    l6 = sub.read(4*8).uint
    if ( l2 == 0 or l4 == 0 or l6 == 0):
        gps = 'N/A'
        return gps
    #write timestamp for text output (hh:mm:ss.xxx)
    gpsts = str(int(float(l1)/float(l2))).zfill(2) + ':' + str(int(float(l3)/float(l4))).zfill(2) + ":" + str(int(float(l5)/float(l6))).zfill(2)
    #print (gpsts)

    sub.pos+=32
    #read 0x8509 - GPS fix STATUS (not used yet)
    gpsfix = BitArray(sub.read(8))
    gpsfix = gpsfix.tobytes().decode('utf-8')

    sub.pos+=32
    # read 0x850a - GPS Measure mode (2 = 2D, 3 = 3D) - not used yet
    gpsmeasure = BitArray(sub.read(8))
    gpsmeasure = gpsmeasure.tobytes().decode('utf-8')

    sub.pos+=32
    #read 0x850b -  8 bytes ([4]/[4]) -- DOP -not used yet
    x850b_1 = sub.read(4*8).uint
    x850b_2 = sub.read(4*8).uint

    x850b = str(float(x850b_1)/float(x850b_2))

    if sub.read(4*8) == '0x850c0001' :
        #read 0x850c -  1 byte - SpeedRef (K = km/h, M = mph, N = knots)
        x850c = BitArray(sub.read(8))
        x850c = x850c.tobytes().decode('utf-8')

        sub.pos+=32
        #read 0x850d - 8 bytes ([4]/[4]???) - SPEED
        x850d_1 = sub.read(4*8).uint
        x850d_2 = sub.read(4*8).uint

        x850d = round(float(x850d_1)/float(x850d_2),2)
    else : x850d = 'N/A'

    if sub.read(4*8) == '0x850e0001' :
        #read 0x850e - 1 byte - TrackRef (Direction Reference, T = True direction, M = Magnetic direction)
        x850e = BitArray(sub.read(8))
        x850e = x850e.tobytes().decode('utf-8')

        sub.pos+=32
        #read 0x850f - Course 8 bytes ([4]/[4]) (degrees from 0.0 to 359.99)
        x850f_1 = sub.read(4*8).uint
        x850f_2 = sub.read(4*8).uint

        x850f = round(float(x850f_1)/float(x850f_2),2)
    else : x850f = 'N/A'

    #write full lat + lon + timestamp for text output

    if latref == None or lonref == None : gps = 'N/A'
    else :
        gps = lat + str(latref) + ' ' + lon + str(lonref) + ' ' + gpsts
    # debug
    #gps = gps + '\n' +str(x8505) + ' ' + str(x8506) + ' ' + str(gpsfix) + ' ' + str(gpsmeasure) + ' ' + str(x850b) + ' ' + str(x850c) + ' ' + str(x850d) + ' ' + str(x850e) + ' ' + str(x850f)
    if x850d != 'N/A' or x850f != 'N/A' :
        gps = gps + '\n' 'Speed: ' + str(x850d) + 'km/h   Course: ' + str(x850f)

    k = sub.find('0x851d000a',bytealigned = True)
    sub.pos+=32
    gpxdate = BitArray(sub.read(8*10))
    gpxdate = gpxdate.tobytes().decode('utf-8')
    gpxdate = gpxdate.replace(':','-')
    gpxdate = gpxdate + 'T' + gpsts + 'Z'
    dt = datetime.strptime(gpxdate, '%Y-%m-%dT%H:%M:%SZ')

    #print (lat,lon, x850d, x850f)

    #write GPX.

    if (args.gpx and 'ExifGPS'.encode() in exifchk) and old_dt < dt.timestamp() :
        if x8505 != None:
            gpx_point = gpxpy.gpx.GPXTrackPoint(latdd, londd, position_dilution = x850b, type_of_gpx_fix = (gpsmeasure+'d'),  elevation=(float(x8506) * (-1 if x8505 == 1 else 1)),
            time=datetime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second))
        else :
            gpx_point = gpxpy.gpx.GPXTrackPoint(latdd, londd, position_dilution = x850b, type_of_gpx_fix = (gpsmeasure+'d'),
            time=datetime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second))
        gpx_segment.points.append(gpx_point)

    #GPX EXT TEST AREA

        namespace = '{gpxtx}'
        nsmap = {'gpxtpx' : namespace[1:-1]} #
        root = mod_etree.Element(namespace + 'TrackPointExtension')

        subnode1 = mod_etree.SubElement(root, namespace + 'speed')
        subnode2 = mod_etree.SubElement(root, namespace + 'course')
        if x850d != 'N/A' and x850c == 'K':
            subnode1.text = str(round(x850d_1/x850d_2/3.6,2))
        elif x850d != 'N/A' and x850c == 'M':
            subnode1.text = str(round(x850d_1/x850d_2/2.23694,2))
        elif x850d != 'N/A' and x850c == 'N':
            subnode1.text = str(round(x850d_1/x850d_2/1.94384,2))

        if x850f != 'N/A' :
            subnode2.text = str(x850f)
        gpx.nsmap = nsmap
        if x850d != 'N/A' or x850f != 'N/A' :
            gpx_point.extensions.append(root)
        old_dt = dt.timestamp()

#    except (bitstring.ReadError, UnicodeDecodeError) : return 'N/A'
    return gps, old_dt

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
        print ('Error: No embedded Non-Realtime Metadata XML part found in file!')
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

### Get filesize ###
filesize = os.path.getsize(F)

#check for mdat atom tag
sampl_check = s.find('0x6D646174000000', bytealigned=True)
if len(sampl_check) != 0:
    #s.bytepos+=13
    #sampl_string = s.read(4*8)
    sampl_string = '0x001C0100'
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

pattern = b'Group name="(.*?)"'#    .*?formatFps="(.*?)".*?Device manufacturer="(.*?)".*?modelName="(.*?)"'
rx = re.compile(pattern, re.IGNORECASE|re.MULTILINE|re.DOTALL)
exifchk = rx.findall(m)



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
print ('Video duration (sec):', float(duration.decode())/(float(ts)/float(sd)))
if 'ExifGPS'.encode() in exifchk : print ('ExifGPS group detected in non-realtime meta-data section. GPX Track extraction possible with "-gpx" argument.')
if args.gpx and 'ExifGPS'.encode() in exifchk : print ('"-gpx" argument specified. Will extract GPX track.')

if args.sidecar == True:
    opt_sidecar()

all_the_data.close()

if args.check :
    print ('XAVC S file check completed')
    sys.exit()

### NRT_Acquire END ###

print ('Processing...')

if args.gpx and 'ExifGPS'.encode() in exifchk :

    gpx = gpxpy.gpx.GPX()
    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack(name='Trackname')
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)


    gpx.nsmap = {
            'gpxtpx' : 'https://www.8garmin.com/xmlschemas/TrackPointExtension/v2',
            'version' : '1.1',
            'xsi' : 'http://www.w3.org/2001/XMLSchema-instance',
            'targetNamespace' : 'http://www.topografix.com/GPX/1/1',
            'elementFormDefault' : 'qualified'
                }

    gpx.schema_locations = [
           #'http://www.garmin.com/xmlschemas/GpxExtensions/v3',
           #'http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd',
           'http://www.topografix.com/GPX/1/1',
           'http://www.topografix.com/GPX/1/1/gpx.xsd',
           'https://www.8garmin.com/xmlschemas/TrackPointExtension/v2',
           'https://www.8garmin.com/xmlschemas/TrackPointExtensionv2.xsd'
        ]


#GPX EXT TEST AREA - to delete
"""
    namespace = '{gpx.py}'
    nsmap = {'gpxtpx' : namespace[1:-1]}
    root = mod_etree.Element(namespace + 'TrackPointExtension')
    #root.text = ''
    #root.tail = ''

    subnode1 = mod_etree.SubElement(root, namespace + 'speed')
    subnode1.text=''
    subnode1.tail=''
    subnode3 = mod_etree.SubElement(root, namespace + 'course')
    subnode3.text=''
    subnode3.tail=''

    gpx.nsmap = nsmap
"""
#GPX EXT TEST AREA

ssec = 0
k=0
offset = 0
old_dt = 0


f = io.StringIO()

for c in range(int(duration)):
    s = ConstBitStream(filename=F)
    #Debug# print s
    samples = (s.find(sampl_string, start = offset, bytealigned=True))
    offset = samples[0] + 1024*8
    i = samples[0]
    sub = s[i:(i+1024*8)]

    #skip if no XAVC S timestamp tag in block :
    if '0xe3040008' not in sub :
        """
        c+=1
        f.write (str(c) +'\n')
        f.write (str(sampletime(ssec,sdur)) + '\n')
        f.write ('Frame: ' + str(c) + '/' + duration.decode() + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
        f.write (ae +'  ' + iso + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
        f.write ('WB mode: '+ str(wb) + '  |  AF mode: ' + str(af) + '\n')
        if dist != 'N/A' :
            f.write ('Focus Distance: ' + dist + '\n') #'D.zoom: '+dz+'x '+ + '  ' + ge
        if gps != 'N/A' :
            #print (gps)
            f.write ('GPS: ' + gps[0] + '\n')
        if ge != 'N/A' :
            f.write (ge  + '\n')
        #f.write (time + '\n')
        f.write ('\n')
        if gps != 'N/A' :
            old_dt = gps[1]
        ssec=ssec+sdur
        """
        continue
    #get metadata
    fn = getfn()
    dist=getdist()
    ss=  getss()
    iso= getiso()
    if iso == 'N/A':
        iso = ''
    else:
        iso = 'ISO: ' + str(iso)

    db = getdb()
    #dz = getdz() --- digital zoom (turned off now)
    ae=  getpasm()
    if ae == 'N/A':
        ae = ''
    wb=  getwbmode()
    af=  getaf()
    time = gettime()
    ge = getge()
    if (args.gpx and 'ExifGPS'.encode() in exifchk) :
        gps = getgps(old_dt)
    else : gps = 'N/A'
    c+=1
    f.write (str(c) +'\n')
    f.write (str(sampletime(ssec,sdur)) + '\n')
    f.write ('Frame: ' + str(c) + '/' + duration.decode() + '\n') #removed ('Model: ' + vendor + ' ' + modelname + ' |)
    f.write (ae +'  ' + iso + '  Gain: ' + str(db) +'db' + '  F' + str(fn) + '  Shutter: ' + str(ss) + '\n')
    f.write ('WB mode: '+ str(wb) + '  |  AF mode: ' + str(af) + '\n')
    if dist != 'N/A' :
        f.write ('Focus Distance: ' + dist + '\n') #'D.zoom: '+dz+'x '+ + '  ' + ge
    if gps != 'N/A' :
        f.write ('GPS: ' + gps[0] + '\n')
    if ge != 'N/A' :
        f.write (ge  + '\n')
    #f.write (time + '\n') - timestamp (swiched off)
    f.write ('\n')
    if gps != 'N/A' :
        #print (gps)
        old_dt = float(gps[1])
    ssec=ssec+sdur
    sys.stdout.write ('\rProcessed ' + str(c) + ' frames of ' + str(duration.decode()) + '   (' + str(round(samples[0]/8/(1000**2))) + 'MB  of ' + str(round(filesize/(1000**2))) + 'MB)')
    sys.stdout.flush()

    if os.name == 'nt':
        if msvcrt.kbhit() and (msvcrt.getch() == b'\x1b'):
            print ('\n \n Aborted! Saving processed data...')
            break

""" This code to be used for non-windows OS, not FINISHED!!!
    else:
        dr,dw,de = select([sys.stdin], [], [], 0)
        kbinter = sys.stdin.read(1)
        if ord(kbinter) == 27:
            print ('\n \n Aborted! Saving processed data...')
            break
"""

with open(F[:-3]+'srt', 'w') as outfile:
    outfile.write(f.getvalue())

f.close()

print ('\nLast frame processed:', c)
print ('Success! SRT file created: ' + F[:-3]+'srt')

if args.gpx and 'ExifGPS'.encode() in exifchk :
    print ('Writting GPX file')
    #print ('Created GPX:', gpx.to_xml())
    with open(F[:-3]+'GPX', 'w') as outfile:
        outfile.write(gpx.to_xml('1.1'))
    print ('Finished writting GPX file:', F[:-3]+'GPX')



if args.muxmkv:
    opt_muxmkv()

sys.exit()
