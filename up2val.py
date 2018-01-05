#! env python3
# use like, ./up2val.py <filename> | sh
# This program write a shell script to review the job before be submitted
# you need to set your own Account and Vault Name in local.py file
import sys
import os.path
from datetime import datetime
from treehash import TreeHash

# you need to set your own Account and Vault Name in local.py file
MyAccount="Empty"
MyVault="Empty"
from local import *

fn=sys.argv[1]
fs=os.path.getsize(fn)

csize=1024*1024*1024*1 # 1GB
csize=1024*1024*256 # 256MB for test

csize=fs if fs < csize else (int(fs/(int((fs-1)/csize)+1)/512)+1)*512

print("ACCNTID="+MyAccount,end=';')
print("VALNAME="+MyVault)

ft=open(fn,"rb")
mt=TreeHash();mt.update(ft.read(1024*1024))
ft.close()
print(datetime.now().strftime('ARCDES0=v3/%Y-%m-%d@2%H@1%M@1%S/')+\
     fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+"/"+\
     mt.hexdigest())

ft=open(fn,"rb")
cn=0
for x in range(0,fs,csize):
    fs=ft.read(csize)
    mt=TreeHash();mt.update(fs)
    fwn = "tmp%2.2d" % cn
    fw = open(fwn,"wb")
    fw.write(fs)
    fw.close()

    print("BDNNAME="+fwn,end=';')
    print("ARCDES1="+("%d" % cn),end=';')
    print("CSUM="+mt.hexdigest())
    print("aws glacier upload-archive --account-id $ACCNTID --vault-name $VALNAME --body $BDNNAME --archive-description $ARCDES0/$ARCDES1 --checksum=$CSUM")
    cn = cn+1
ft.close()
