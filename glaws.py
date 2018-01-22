#! env python3
import sys
import os.path
import json
import re
from datetime import datetime
from treehash import TreeHash
import subprocess

cmdsw = 0
# you need to set your own Account and Vault Name in local.py file
(csize,MyAccount,MyVault)=(1024*1024*256,"Empty","Empty") # 256MB for test
from local import *

#(sys.argv).append('@dummy@')
argv=sys.argv[1:]
cmd=argv[0]
if cmd == 'none':
    a=0
elif cmd == 'bucket':
    if argv[1] == 'ls':
        r=json.loads(subprocess.getoutput(('aws glacier list-vaults --account-id %s' % MyAccount)))
        if argv[2] != '--verbose': print("#name")
        else: print("#archive size name")
        for m in r['VaultList']:
            if argv[2] != '--verbose': print(m['VaultName'])
            else: print("%5d %7.3f %s" % (m['NumberOfArchives'],m['SizeInBytes']/1024/1024/1024,m['VaultName']))
elif cmd == 'job':
    if argv[1] == 'ls':
        if '--vault-name' in argv:
            r=json.loads(subprocess.getoutput('aws glacier list-jobs --account-id %s --vault-name %s' % (MyAccount,argv[argv.index('--vault-name')+1])))
            for m in r['JobList']:
                if m['Action'] == 'InventoryRetrieval':
                    s = re.sub('^.*?:vaults/','',m['VaultARN'])
                    print("%s %s %s" % (m['Action'],m['StatusCode'],s))
            
elif cmd == 'archieve' or cmd == 'arch':
    if argv[1] == 'ls':
        if '--vault-name' in argv:
            print('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (MyAccount,argv[argv.index('--vault-name')+1],"\'{\"Type\": \"inventory-retrieval\"}\'"))
            #print(subprocess.getoutput('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (MyAccount,argv[argv.index('--vault-name')+1],"\'{\"Type\": \"inventory-retrieval\"}\'")))
        #if argv[2] != '--verbose': print("#name")
        #else: print("#archive size name")
    
