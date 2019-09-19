import binascii
import sys
import os
import bitstring
from bitstring import  ConstBitStream, BitArray #, BitStream, pack, Bits,
from functools import partial
from textwrap import wrap
from colorama import init, deinit
init(autoreset=True)

from colorama import Fore, Back, Style

#RTMD READ
#filename = 'F:\\Skiba_video\\C0012_track3.rtmd'
filename = "F:\PRIVATE\M4ROOT\CLIP\C0004_track3.rtmd"
rtmd_size = 1024*3
prev = [None]*rtmd_size
s=""
fr=1
os.system('cls')
with open(filename, 'rb') as f:
    for chunk in iter(partial(f.read, rtmd_size), b''):
        print ("Frame: ",fr)
        fr+=1
        #content = f.read()
        l = wrap(binascii.hexlify(chunk).decode(),2)
        for i in range(rtmd_size):
            if l[i] != prev[i] and prev[i] != None:
                s+=(Fore.RED+l[i]+'\033[0m'+" ")

            else:
                s+=(l[i]+" ")

        ghl=('06 0e 2b 34 02 53 01 01 0c 02 01 01 7f 01 00 00')
        #print(s.find('06 0e 2b 34 02 53 01 01 0c 02 01 01 7f 01 00 00'))
        s.replace(ghl,Fore.GREEN+ghl+'\033[0m')

        print("\r"+s,flush=True)
        input()
        os.system('cls')
        #sys.stdout.write(s)
        #print(chr(27) + "[2J")
        prev = l
        s=""
deinit()

"""
f = 'C:\\MyWork\\temp\\acam\\C0121.MP4'
bs = ConstBitStream(filename=f)
rtmd_size = 1024*3*8
prev = [None]*rtmd_size
s=""
with open(filename, 'rb') as f:
    for chunk in iter(partial(f.read, rtmd_size), b''):
        #content = f.read()
        l = wrap(binascii.hexlify(chunk).decode(),2)
        for i in range(rtmd_size):
            if l[i] == prev[i]:
                s+=(Fore.WHITE+l[i]+" ")
            else:
                s+=(Fore.RED+l[i]+" ")
        print("\r"+s,flush=True)
        input()
        os.system('cls')
        #sys.stdout.write(s)
        #print(chr(27) + "[2J")
        prev = l
        s=""
deinit()
"""
