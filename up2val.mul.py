#! env python3
# use like, ./up2val.py <filename> | sh
# This program write a shell script to review the job before be submitted
# you need to set your own Account and Vault Name in local.py file
from datetime import datetime
from treehash import TreeHash
import json,os.path,re,subprocess,sys

def errorexit(msg):
    print(msg)
    exit(1)

cmdsw = 0
def cmd(a):
    if cmdsw == 1:
        print(a)
        return ('--debug mode--')
    else:
        (s,r)=subprocess.getstatusoutput(a)
        print('## status code ...Z>>{0:<3}<<Z'.format(s))
        if s != 0:
            print('## status code ...{0:<3}'.format(s))
            print('## {}'.format(a))
        return(s,r)

# you need to set your own Account and Vault Name in local.py file
(csize,MyAccount,MyVault)=(1024*1024*256,'Empty','Empty') # 256MB for test
from useast1 import *
(cs,css,csh,csd)=(1024*1024*256,1024*1024*16,1024*16,10)

argv=sys.argv[1:]
opt={'Account':MyAccount,
     'Verbose':('--verbose' in sys.argv)}
opt['VaultName'] = MyVault
 #    'VaultName':'@None@' if not '--vault-name' in argv else argv[argv.index('--vault-name')+1]}

#     'FileName':'@None@' if not '--file-name' in argv else argv[argv.index('--file-name')+1],

awstmp='aws glacier {} --account-id '+opt['Account']

flog=open('.up2val.file.log','a')
#exit(1)
for fn in sys.argv[1:]:
    print('# target file:'+fn)
    print('# target file:'+fn,file=flog,flush=True)
    (fs,cs,ft,mt,cn)=(os.path.getsize(fn),csize,open(fn,'rb'),TreeHash(),0)
    print(('## chunk size :%.3f Gb' % (int(cs)/1024/1024/1024)))
    for x in range(0,fs,cs):
        rs=ft.read(cs)
        fw=open(('tmp%2.2d' % cn),'wb') ;fw.write(rs) ;fw.close()
        mt.update(rs);
        cn=cn+1
    ft.close()
    arcdsc=datetime.now().strftime('v3/%Y-%m-%d@2%H@1%M@1%S/')+\
            fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+\
            '/'+mt.hexdigest()+'/0'
    while(1):
        (s,r)=cmd(awstmp.format('initiate-multipart-upload')+ ' --vault-name {}'.format(opt['VaultName'])+
                  ' --archive-description \"{}\" --part-size {}'.format(arcdsc,cs))
        if s!=0 : errorexit(r)
        upid=json.loads(r)['uploadId']
        if opt['Verbose'] : print("## upload id "+upid)
        if upid[0] != '-':
            break

    (rp,cn)=(0,0)
    for x in range(0,fs,cs):
        fr=open(('tmp%2.2d' % cn),'rb') ;rs=fr.read(cs) ;fr.close()
        mp=TreeHash();mp.update(rs);fl=len(rs)
        
        a=awstmp.format('upload-multipart-part')+' --vault-name {}'.format(opt['VaultName'])+\
           ' --body \'{}\' --upload-id {}'.format(('tmp%2.2d' % cn),upid)+\
           ' --range \"bytes %d-%d/*\" --checksum \"%s\"' % (rp,rp+fl-1,mp.hexdigest())
#        print(a)
        (s,r)=subprocess.getstatusoutput(a)
        if s != 0:errorexit(r)
        print(('#   done part %2d, %6.3f Gb (%12d b)' % (cn,fl/1024/1024/1024.,fl)),flush=True)
        cn=cn+1
        rp=rp+fl
        fr.close()

    a=awstmp.format('complete-multipart-upload')+' --vault-name {}'.format(opt['VaultName'])+\
       ' --upload-id {} --checksum \"{}\"  --archive-size {}'.format(upid,mt.hexdigest(),fs)
    print(a)
    (s,r)=subprocess.getstatusoutput(a)
    if s != 0:errorexit(r)
    print(r)
    #print('#  done',file=flog,flush=True)
