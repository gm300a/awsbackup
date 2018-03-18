#! env python3
import os.path,json,sys
#import hashlib
from random import randrange
from datetime import datetime
from treehash import TreeHash

from keygen import *

opt=dict()
(cs,css,csh,csd)=(1024*1024*256,1024*1024*16,1024*16,10)
rt=int('1'+'0'*(csd+1))
opt={'NoTmp': '--no-tmp' in sys.argv or '--no-temp' in sys.argv,
     'Verbose': '--verbose' in sys.argv }

for fn in sys.argv[1:]:
    if fn == '--verbose': continue

    (fs,fm)=(os.path.getsize(fn),datetime.now().strftime('%Y%m%d.%H%M%S.meta'))
    ft=('' if 1024*1024*1024*32 <fs or opt['NoTmp'] else os.environ.get('TMP')+'/')+fm+'.tmp'
#    print('### tmp=',ft)
#    exit(1)
    print('# processing.. ',fn)
    if opt['Verbose']: print('## formatting to.. ',fm)

    (mt,enc)=(TreeHash(),EncMethod(fm))
    (fh,fw)=(open(fn,'rb'),open(ft,'wb'))

    fb=fh.read(css)
    mt.update(fb)
    if fs <= css:
        fb=(fb+b'@'*16)[0:int((len(fb)+15)/16)*16]
    fw.write(enc.encrypt(fb))
    meta={'FileName':fn,'Size':fs,'CTime':os.path.getctime(fn),'DTime':fm,'ShortCRC':mt.hexdigest()}

    for x in range(css,fs,cs):
        fb=fh.read(cs)
        mt.update(fb)
        fw.write(enc.encrypt((fb+b'@'*16)[0:int((len(fb)+15)/16)*16]))
    fh.close()
    fw.close()
    meta['LongCRC'] = mt.hexdigest()
    if opt['Verbose']: print("## longcrs",meta['LongCRC'])
    if fs < css and meta['ShortCRC'] != meta['LongCRC']:
        print('## short ',meta['ShortCRC'])
        print('## long  ',meta['LongCRC'])
        
    fbj=json.dumps(meta)
    fh=open('.spar.log','a');fh.write(fbj);fh.write('\n');fh.close()

    (fh,fw)=(open(ft,'rb'),open(fm,"wb"))

    fb=('%d           ' % len(fbj))[0:csd]+fbj+' '
    for i in range(0,int(csh/10)+1): fb=fb+('%*.*d' % (csd,csd,randrange(0,rt)))
    fw.write(DecMethod(fm).encrypt(fb[0:csh]))

    for x in range(0,fs,cs): fw.write(fh.read(cs))
    fh.close()
    fw.close()
    os.remove(ft)

