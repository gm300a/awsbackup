import os.path,json,random,sys
import hashlib
from Crypto.Cipher import AES
from random import randrange
from datetime import datetime
from treehash import TreeHash

cs=1024*1024*256
css=1024*1024*16
csh=1024*16
fn=sys.argv[1]
print(fn)
#fn='/cygdrive/d/Cloud/tmpZZ'
fm=datetime.now().strftime('%Y%m%d.%H%M%S.meta')
fkey=fm[0:16]
fs=os.path.getsize(fn)

meta=dict()
meta['FileName'] = fn
meta['Size'] = fs
meta['CTime']=os.path.getctime(fn)
meta['DTime']=fm
aes=AES.new (fkey, AES.MODE_CBC, 'This is an IV456')
mt=TreeHash()

fh=open(fn,'rb')
fw=open(fm+'.tmp','wb')

fb=fh.read(css)
mt.update(fb)
meta['ShortCRC'] = mt.hexdigest()
fw.write(aes.encrypt(fb))

for x in range(css,fs,cs):
    fb=fh.read(cs)
    mt.update(fb)
    fl=int((len(fb)+15)/16)*16
    fe=aes.encrypt((fb+b'@'*16)[0:fl])
    fw.write(fe)
fh.close()
fw.close()
meta['LongCRC'] = mt.hexdigest()
print("longcrs",meta['LongCRC'])
print("pre cal","5b5087b45a90bf7e5e7d4e57795aaac5893d57d2b274f5b450c3de082e5a7236")
fh=open('.spar.log','a')

fbj=json.dumps(meta)
fh=open('.spar.log','a');fh.write(fbj);fh.write('\n');fh.close()

fb=('%d           ' % len(fbj))[0:10]+fbj+' '
for i in range(0,10000):
    fb=fb+('%10.10d' % randrange(0,1000000000))
#print(len(fb[0:csh]))
fe=AES.new (fkey, AES.MODE_CBC, 'This is an IV456').encrypt(fb[0:csh])
fw=open(fm,"wb")
fw.write(fe)
fh=open(fm+'.tmp','rb')
for x in range(0,100):
    fw.write(fh.read(cs))
fh.close()
fw.close()

