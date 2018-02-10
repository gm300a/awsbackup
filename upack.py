import os.path,json,sys
from treehash import TreeHash

from keygen import *

opt=dict()
(cs,csh,opt['Verbose'])=(1024*1024*256,1024*16,('--verbose' in sys.argv))

fnl=sys.argv[1:-1]
fnl.append(sys.argv[-1])

for x in fnl:
    if x == '--verbose': continue
    #fn=sys.argv[1]
    fn='20180211.071103.meta'
    print('# processing.. ',fn)
    
    (fh,fs)=(open(fn,'rb'),os.path.getsize(fn))

    fb=fh.read(csh)
    fe=DecMethod(fn).decrypt(fb).decode('utf-8')
    js=json.loads((fe[10:10+int(fe[0:10])]))

    if opt['Verbose']: print(js)

    (mt,dec)=(TreeHash(),DecMethod(fn))
    if opt['Verbose']:
        print('## because verbose option is specified, decoding results is output to %sa' % fn)
        fw=open(fn+'a','wb')
    
    for x in range(js['Size'],0,-cs):
        fb=dec.decrypt(fh.read(cs))
        if( cs <= x ): mt.update(fb)
        else:     mt.update(fb[0:x])
        if not opt['Verbose']: continue
        if( cs <= x ): fw.write(fb)
        else:    fw.write(fb[0:x])

    if opt['Verbose']: fw.close()

    if mt.hexdigest() == js['LongCRC']: continue
    print('long crs doesn\'t match: File Name is ',fn)
    exit(1)
    
