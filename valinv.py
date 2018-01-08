#! env python3
import sys
import os.path
import json

fj=open(sys.argv[1],"r")
jd=json.load(fj)
cnt=0
for j in jd['ArchiveList']:
    #print(j['CreationDate'])
    #print(j['Size'])
    if j['ArchiveDescription'] == '':
        dsc='-no descrtiption-'
    else:
        n = j['ArchiveDescription'].split('/')
        if n[0] != 'v3':
            dsc='-format error:'+n[0]
        else:
            dsc=n[2].replace('@3','/').replace('@2',' ').replace('@1',':').replace('@0','@')+' part '+n[4]
    print(dsc,("%7.3fGB"%(int(j['Size'])/1024/1024/1024)))
    
    
          
