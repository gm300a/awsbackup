#! env python3
import sys
import os.path
import json
import subprocess

# you need to set your own Account and Vault Name in local.py file
MyAccount="Empty"
MyVault="Empty"
#from cdbackup import *
from largebackup import *

#fn=sys.argv[1]
jid=
print(subprocess.getoutput("aws glacier describe-job --account-id %s --vault-name %s --job-id %s" % (MyAccount,MyVault,jid)))

exit(1)
#
print('not')
#r = subprocess.getoutput("aws glacier list-jobs --account-id %s --vault-name %s" % (MyAccount,MyVault))
#jd=json.loads(r)
#cnt=0
#for j in jd['JobList']:
#    if j['Completed'] != 1 or j['Action'] != 'InventoryRetrieval':
#        continue
#    if j['StatusMessage'] != 'Succeeded':
#         print('StatusMessage is',j['StatusMessage'])
#         continue
#    if j['StatusCode'] != 'Succeeded':
#         print('StatusCode is',j['StatusCode'])
#         continue
#    jid=j['JobId']
#    print(subprocess.getoutput("aws glacier describe-job --account-id %s --vault-name %s --job-id %s" % (MyAccount,MyVault,jid)))
#    print(subprocess.getoutput("aws glacier get-job-output --account-id %s --vault-name %s --job-id %s %s.%2.2d" % \
#                               (MyAccount,MyVault,jid,fn,cnt)))
#    cnt = cnt+1
#    
          
