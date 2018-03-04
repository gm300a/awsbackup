#! env python3
from datetime import datetime
from treehash import TreeHash
import json,os.path,re,subprocess,sys

def errorexit(msg):
    print(msg)
    exit(1)

def logevent(msg):
    print(msg)
    with open('.up2valZ.file.log','a') as fh: print(msg,file=fh,flush=True)

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
     'TempFile': ('' if '--no-temp' in sys.argv else os.environ.get('TMP')+'/')+\
     'upload{:05X}{}'.format(os.getpid(),'.{:03X}.{:03X}'),
     'Move2Done': '--move-to-done' in sys.argv and os.path.exists('done') and os.path.isdir('done')}

if opt['Move2Done'] : print('# when the upload is completed, file is moved to ./done/.')
opt['MinSize'] = int(csize/128) if opt['Move2Done'] else 0

(fcnt,gbyte,awstmp)=(0,1024*1024*1024,'aws glacier {} --account-id '+opt['Account'])
awstmp=awstmp+' --vault-name {}'.format(opt['VaultName'])
print('## chunk size : {:6.2f} GB'.format(csize/gbyte))
for fn in sys.argv[1:]:
    print(fn)
exit(1)
for fn in sys.argv[1:]:
    if re.match('^--',fn): continue
    elif not os.path.exists(fn) :
        if opt['Verbose'] : print('## file {} cannot be accessed'.format(fn))
        continue
    fs=os.path.getsize(fn)
    if fs < opt['MinSize'] :
        if opt['Verbose'] :
            print('## file {} is shoter than lower limit {}.'.format(fn,opt['MinSize']))
        continue
    (ft,mt)=(open(fn,'rb'),TreeHash())
    logevent('#{:03} target file: {}'.format(fcnt,fn))
    for x in range(0,fs,csize): mt.update(ft.read(csize))
    ft.close()

    arcdsc=datetime.now().strftime('v3/%Y-%m-%d@2%H@1%M@1%S/')+\
            fn.replace('@','@0').replace(':','@1').replace(' ','@2').replace('/','@3')+\
            '/'+mt.hexdigest()+'/0'    
    while(1):
        (s,r)=cmd(awstmp.format('initiate-multipart-upload')+
                  ' --archive-description \"{}\" --part-size {}'.format(arcdsc,csize))
        if s!=0 : errorexit(r)
        upid=json.loads(r)['uploadId']
        if opt['Verbose'] : print("## upload id "+upid)
        if upid[0] != '-':
            break

    (rp,scnt,ft,awstmp)=(0,0,open(fn,'rb'),awstmp+' --upload-id {}'.format(upid))
    for x in range(0,fs,csize):
        rs=ft.read(csize);
        (fl,fp)=(len(rs),opt['TempFile'].format(fcnt,scnt))
        with open(fp,'wb') as fw : fw.write(rs)
        mp=TreeHash();mp.update(rs)

        (s,r)=cmd(awstmp.format('upload-multipart-part')+' --body \'{}\''.format(fp)+\
                  ' --range \"bytes {}-{}/*\" --checksum \"{}\"'.format(rp,rp+fl-1,mp.hexdigest()))
        if s != 0:errorexit(r)
        if opt['Verbose'] :
            print('##  done part {:2}, {:6.2f} GB ({:12} b)'.format(scnt,fl/gbyte,fl), flush=True)
        elif scnt == 0 : print('##  done part {:2}'.format(scnt),end='',flush=True)
        else: print(' {:2}'.format(scnt),end='',flush=True)
        (rp,scnt)=(rp+fl,scnt+1)
        os.remove(fp)
    ft.close()

    print('')
    (s,r)=cmd(awstmp.format('complete-multipart-upload')+
              ' --checksum \"{}\" --archive-size {}'.format(mt.hexdigest(),fs))
    if s != 0:errorexit(r)
    logevent('##  done {}'.format(upid))
    if opt['Move2Done'] : os.rename(fn,'done/{}'.format(fn))
