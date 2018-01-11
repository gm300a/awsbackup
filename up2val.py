#! env python3
# use like, ./up2val.py <filename> | sh
# This program write a shell script to review the job before be submitted
# you need to set your own Account and Vault Name in local.py file
import sys
import os.path
import subprocess
from datetime import datetime
from treehash import TreeHash

cmdsw = 0
def cmd(a):
    if cmdsw == 1:
        print(a)
    else:
        fw = open('.up2val.cmd.log','w')
        fw.write(a)
        fw.close()
        subprocess.getoutput(a)

# you need to set your own Account and Vault Name in local.py file
csize=1024*1024*1024*1 # 1GB
csize=1024*1024*256 # 256MB for test
MyAccount="Empty"
MyVault="Empty"
from cdbackup import *
#from local import *

fnl=sys.argv[1:-1]
fnl.append(sys.argv[-1])
for fn in fnl:
    print("# "+fn)
    fs=os.path.getsize(fn)
    cs=fs if fs < csize else (int(fs/(int((fs-1)/csize)+1)/512)+1)*512
    
    ft=open(fn,"rb")
    mt=TreeHash();mt.update(ft.read(1024*1024))
    ft.close()
    arcdsc=datetime.now().strftime('v3/%Y-%m-%d@2%H@1%M@1%S/')+\
            fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+"/"+mt.hexdigest()

#    arcdsc = datetime.now().strftime('ARCDES0=v3/%Y-%m-%d@2%H@1%M@1%S/')+\
#          fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+"/"+\

    ft=open(fn,"rb")
    cn=0
    for x in range(0,fs,cs):
        fs=ft.read(cs)
        fwn="tmp%2.2d" % cn
        fw=open(fwn,"wb") ;fw.write(fs) ;fw.close()

        mt=TreeHash();mt.update(fs); csum=mt.hexdigest();#print("CSUM="+csum)

        #fw=open(fwn,"rb") ;fs=fw.read() ;fw.close()
        #mt=TreeHash();mt.update(fs); print("WSUM="+mt.hexdigest())
        cmd(("aws glacier upload-archive --account-id %s --vault-name %s --body %s " % (MyAccount,MyVault,fwn))+
            ("--archive-description %s/%d --checksum=%s" % (arcdsc,cn,csum)))
        print(("#   part %d,%d byte" % (cn,len(fs))),flush=True)
        cn = cn+1
    ft.close()

#        cmd(("aws glacier upload-archive --account-id $ACCNTID --vault-name $VALNAME --body $BDNNAME --archive-description $ARCDES0/$ARCDES1 --checksum=$CSUM")
