#! env python3
import sys
import os.path
import json
import subprocess

# you need to set your own Account and Vault Name in local.py file
MyAccount="Empty"
MyVault="Empty"
from local import *

print("ACCNTID="+MyAccount,end=';')
print("VALNAME="+MyVault)

sw=1
if sw == 1:
    fj=open('log/arcret.job.log','r')
    jd=json.load(fj)
    fj.close()
else:
    r = subprocess.getoutput("aws glacier list-jobs --account-id %s --vault-name %s" % (MyAccount,MyVault))
    jd=json.loads(r)

for j in jd['JobList']:
    if j['Completed'] != 1 or j['Action'] != 'ArchiveRetrieval':
        continue
    if j['StatusMessage'] != 'Succeeded':
         print('#StatusMessage is',j['StatusMessage'])
         continue
    if j['StatusCode'] != 'Succeeded':
         print('#StatusCode is',j['StatusCode'])
         continue
    print("JOBID="+j['JobId'])
    print('aws glacier get-job-output --account-id $ACCNTID --vault-name $VALNAME --job-id $JOBID dst/valdwn.dat')
