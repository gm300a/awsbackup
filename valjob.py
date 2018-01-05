#! env python3
import sys
import os.path
import json

# you need to set your own Account and Vault Name in local.py file
MyAccount="Empty"
MyVault="Empty"
from local import *

fn=sys.argv[1]

print("ACCNTID="+MyAccount,end=';')
print("VALNAME="+MyVault)

fj=open("p1","r")
jd=json.load(fj)
cnt=0
for j in jd['JobList']:
    if j['Completed'] != 1 or j['Action'] != 'InventoryRetrieval':
        continue
    if j['StatusMessage'] != 'Succeeded':
         print('StatusMessage is',j['StatusMessage'])
         continue
    if j['StatusCode'] != 'Succeeded':
         print('StatusCode is',j['StatusCode'])
         continue
    print("JOBID="+j['JobId'])
    print("aws glacier describe-job --account-id $ACCNTID --vault-name $VALNAME --job-id $JOBID")
    print("aws glacier get-job-output --account-id $ACCNTID --vault-name $VALNAME --job-id $JOBID "+fn+(".%2.2d" % cnt))
    cnt = cnt+1
    
          
