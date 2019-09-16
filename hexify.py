import binascii
from functools import partial
filename = 'C:\\MyWork\\temp\\acam\\C0121_track3.rtmd'
with open(filename, 'rb') as f:
    for chunk in iter(partial(f.read, 1024*3), b''):
        content = f.read(1024*3)
        print(binascii.hexlify(content).decode())
        print('')
