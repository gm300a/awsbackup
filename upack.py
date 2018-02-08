import os.path,json,random
import hashlib
from Crypto.Cipher import AES
from random import randrange
from datetime import datetime
from treehash import TreeHash

cs=1024*1024*256

fn='20180209.084646.meta'
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
for x in range(0,fs,cs):
    fb=aes.decrypt(fh.read(cs))
    mt.update(fb)
    fw.write(fb)
    cn=cn+1
#meta['LongCRC'] = mt.hexdigest()
print("longcrs",mt.hexdigest())
print("pre cal","5b5087b45a90bf7e5e7d4e57795aaac5893d57d2b274f5b450c3de082e5a7236")
