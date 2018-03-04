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

def logevent(msg):
    print(msg)
    with open('.up2val.file.log','a') as fh: print(msg,file=fh,flush=True)
    
cmdsw = 0
def cmd(a):
    if cmdsw == 1:
        print(a)
        return ('--debug mode--')
    else:
        (s,r)=subprocess.getstatusoutput(a)
        if s != 0:
            print('## status code ...{0:<3}'.format(s))
            print('## {}'.format(r))
            print('## {}'.format(a))
        return(s,r)

# you need to set your own Account and Vault Name in local.py file
(csize,MyAccount,MyVault)=(1024*1024*256,'Empty','Empty') # 256MB for test
from useast1 import *

opt={'Account': MyAccount, 'VaultName': MyVault,'Verbose': ('--verbose' in sys.argv),
     'Move2tmp': ('--move-to-tmp' in sys.argv) and os.path.exists('tmp') and os.path.isdir('tmp')}

if opt['Move2tmp'] : print('# when the upload is completed, file is moved to ./tmp/.')
opt['MinSize'] = int(csize/128) if opt['Move2tmp'] else 0
#print(opt['MinSize'])

awstmp='aws glacier {} --account-id '+opt['Account']
print(('## chunk size : %.3f Gb' % (int(csize)/1024/1024/1024)))
for fn in sys.argv[1:]:
    if fn == '--verbose' or fn == '--move-to-tmp' : continue
    if not os.path.exists(fn) :
        if opt['Verbose'] : print('## file {} cannot be accessed'.format(fn))
        continue
    (fs,ft,mt,cn)=(os.path.getsize(fn),open(fn,'rb'),TreeHash(),0)
    if fs < opt['MinSize'] :
        if opt['Verbose'] : print('## file {} is shoter than lower limit {}.'.format(fn,opt['MinSize']))
        continue
    logevent('# target file: '+fn)
    for x in range(0,fs,csize):
        rs=ft.read(csize)
        fw=open('tmp{:0=2d}'.format(cn),'wb') ;fw.write(rs) ;fw.close()
        mt.update(rs);
        cn=cn+1
    ft.close()
    arcdsc=datetime.now().strftime('v3/%Y-%m-%d@2%H@1%M@1%S/')+\
            fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+\
            '/'+mt.hexdigest()+'/0'
    while(1):
        (s,r)=cmd(awstmp.format('initiate-multipart-upload')+ ' --vault-name {}'.format(opt['VaultName'])+
                  ' --archive-description \"{}\" --part-size {}'.format(arcdsc,csize))
        if s!=0 : errorexit(r)
        upid=json.loads(r)['uploadId']
        if opt['Verbose'] : print("## upload id "+upid)
        if upid[0] != '-':
            break

    (rp,cn)=(0,0)
    for x in range(0,fs,csize):
        fp='tmp{:0=2}'.format(cn)
        fr=open(fp,'rb') ;rs=fr.read(csize) ;fr.close()
        mp=TreeHash();mp.update(rs);fl=len(rs)

        (s,r)=cmd(awstmp.format('upload-multipart-part')+' --vault-name {}'.format(opt['VaultName'])+\
           ' --body \'{}\' --upload-id {}'.format(fp,upid)+\
           ' --range \"bytes {}-{}/*\" --checksum \"{}\"'.format(rp,rp+fl-1,mp.hexdigest()))
        if s != 0:errorexit(r)
        if opt['Verbose'] :
            print('##  done part {:2}, {:6.2f} Gb ({:12} b)'.format(cn,fl/1024/1024/1024.,fl),flush=True)
        elif cn == 0 : print('##  done part {:2}'.format(cn),end='',flush=True)
        else: print(' {:2}'.format(cn),end='',flush=True)
        (rp,cn)=(rp+fl,cn+1)
        fr.close()

    print('')
    (s,r)=cmd(awstmp.format('complete-multipart-upload')+' --vault-name {}'.format(opt['VaultName'])+\
              ' --upload-id {} --checksum \"{}\"  --archive-size {}'.format(upid,mt.hexdigest(),fs))
    if s != 0:errorexit(r)
    logevent('##  done {}'.format(upid))
    if opt['Move2tmp'] and os.path.exists('tmp'):
        os.rename(fn,'tmp/{}'.format(fn))
