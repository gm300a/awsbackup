import os.path,json,random,sys
import hashlib
from Crypto.Cipher import AES
from random import randrange
from datetime import datetime
from treehash import TreeHash

cs=1024*1024*256

fn=sys.argv[1]
print(fn)
fkey=fn[0:16]

fh=open(fn,'rb')
fs=os.path.getsize(fn)

csh=1024*16
fb=fh.read(csh)
fe=AES.new (fkey, AES.MODE_CBC, 'This is an IV456').decrypt(fb)
js=json.loads((fe.decode('utf-8')[10:10+int(fe.decode('utf-8')[0:10])]))
print(js)
mt=TreeHash()
aes=AES.new (fkey, AES.MODE_CBC, 'This is an IV456')

fw=open(fn+'a','wb')
#exit(1)
cn=0
cs0=js['Size']
for x in range(0,js['Size'],cs):
    fb=aes.decrypt(fh.read(cs))
    if( cs0 < cs ):
        mt.update(fb[0:cs0])
        fw.write(fb[0:cs0])
    else:
        mt.update(fb)
        fw.write(fb)
    cn=cn+1
    cs0=cs0-cs
#meta['LongCRC'] = mt.hexdigest()
#print("longcrs",mt.hexdigest())
if mt.hexdigest() != js['LongCRC']:
    print('long crs doesn\'t match')
#print("pre cal","5b5087b45a90bf7e5e7d4e57795aaac5893d57d2b274f5b450c3de082e5a7236")
