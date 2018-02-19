import os.path,json,sys,re
from treehash import TreeHash

from keygen import *

opt=dict()
(cs,csh,opt['Verbose'])=(1024*1024*256,1024*16,('--verbose' in sys.argv))

fnl=sys.argv[1:-1]
fnl.append(sys.argv[-1])

for fn in fnl:
    if fn == '--verbose': continue
    #fn=sys.argv[1]
    #fn='20180211.071103.meta'
    print('# processing.. ',fn)
    m=re.search('^(.*/|)([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])\.([0-9][0-9])([0-9][0-9])([0-9][0-9])\.meta',fn)
    if m == None:
        print('file name error. should be 21341234.0123456.meta. no leading \'dot\', \'/ or full path')
        exit(1)
    elif int(m[2])<2017 or 2020<int(m[2]) or 12 < int(m[3]) or 31 < int(m[4]) or 24 < int(m[5]):
        print('file name error. should like time stamp')
        exit(1)
    (fh,fs)=(open(fn,'rb'),os.path.getsize(fn))

    fb=fh.read(csh)
    fe=DecMethod(fn).decrypt(fb).decode('utf-8')
#    fe=DecMethod(fn).decrypt(fb)
#    print(int(fe[0:10]))
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
    print('error,long crs doesn\'t match: Orignal file Name in header is {}'.format(js['FileName']))
    exit(1)
    
