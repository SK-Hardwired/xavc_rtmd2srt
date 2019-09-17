import binascii
import sys
import os
from functools import partial
from textwrap import wrap
from colorama import init, deinit
init()

from colorama import Fore, Back, Style

filename = 'd:\\Video Projects\\PRO-K\\2019-10-1\\3-SOKOLOVA-PINK-RED-VIDEO\\CAM1\\C0040_track4.rtmd'
prev = [None]*1024
s=""
with open(filename, 'rb') as f:
    for chunk in iter(partial(f.read, 1024), b''):
        #content = f.read()
        l = wrap(binascii.hexlify(chunk).decode(),2)
        for i in range(1024):
            if l[i] == prev[i]:
                s+=(Fore.WHITE+l[i]+" ")
            else:
                s+=(Fore.RED+l[i]+" ")
        print("\r"+s,flush=False)
        os.system('cls')
        #sys.stdout.write(s)
        #print(chr(27) + "[2J")
        prev = l
        s=""
deinit()
