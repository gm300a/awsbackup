#! env python3
# use like, ./up2val.py <filename> | sh
# This program write a shell script to review the job before be submitted
# you need to set your own Account and Vault Name in local.py file
from datetime import datetime
from treehash import TreeHash
import json
import os.path
import re
import subprocess
import sys

cmdsw = 1
def cmd(a):
    if cmdsw == 1:
        print(a)
    else:
        fw = open('.up2val.cmd.log','w')
        fw.write(a+'\n')
        fw.close()
        subprocess.getoutput(a)

# you need to set your own Account and Vault Name in local.py file
(csize,MyAccount,MyVault)=(1024*1024*256,'Empty','Empty') # 256MB for test
from useast1 import *

sys.argv.append('dummy')
fnl=sys.argv[1:-1]
flog=open('.up2val.file.log','a')

for fn in fnl:
    print('# target file:'+fn)
    print('# target file:'+fn,file=flog,flush=True)
    (fs,cs,ft,mt,cn)=(os.path.getsize(fn),cszie,open(fn,'rb'),TreeHash(),0)
    print(('## chunk size :%.3f Gb' % (int(cs)/1024/1024/1024)))
    for x in range(0,fs,cs):
        rs=ft.read(cs)
        fw=open(('tmp%2.2d' % cn),'wb') ;fw.write(rs) ;fw.close()
        mt.update(rs);
        cn=cn+1
    ft.close()
    arcdsc=datetime.now().strftime('v3/%Y-%m-%d@2%H@1%M@1%S/')+\
            fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+'/'+mt.hexdigest()+'/0'
    jt=json.loads(subprocess.getoutput(('aws glacier initiate-multipart-upload --account-id %s --vault-name %s ' \
                                      % (MyAccount,MyVault))+\
                                      ('--archive-description \"%s\" --part-size %d' % (arcdsc,cs))))
    print(jt)
    upid=jt['uploadId']
    print("## upload id "+upid)
    (rp,cn)=(0,0)
    for x in range(0,fs,cs):
        fr=open(('tmp%2.2d' % cn),'rb') ;rs=fr.read(cs) ;fr.close()
        mp=TreeHash();mp.update(rs);fl=len(rs)
        r=subprocess.getoutput(('aws glacier upload-multipart-part --account-id %s --vault-name %s ' \
                               % (MyAccount,MyVault))+\
                               ('--body \'%s\' --upload-id %s ' % (('tmp%2.2d' % cn),upid))+\
                               ('--range \"bytes %d-%d/*\" --checksum \"%s\"' % (rp,rp+fl-1,mp.hexdigest())))
        print(r)
        print(('#   done part %2d, %6.3f Gb (%12d b)' % (cn,fl/1024/1024/1024.,fl)),flush=True)
        cn=cn+1
        rp=rp+fl
        fr.close()

    r=subprocess.getoutput(('aws glacier complete-multipart-upload --account-id %s --vault-name %s ' \
                            % (MyAccount,MyVault))+\
                           ('--upload-id %s --checksum \"%s\"' % (upid,mt.hexdigest())))
        
    #print('#  done',file=flog,flush=True)
