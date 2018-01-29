#! env python3
import sys
import os.path
import json
import re
from datetime import datetime
from treehash import TreeHash
import subprocess

# you need to set your own Account and Vault Name in local.py file
(csize,MyAccount,MyVault)=(1024*1024*256,"Empty","Empty") # 256MB for test
from local import *

argv=sys.argv[1:]
opt=dict()
opt['Verbose']='--verbose' in argv
for i in range(0,10000):
    opt['FileName']=('log/glaws.%3.3X.output' % i)
    if not os.path.exists(opt['FileName']):break
#print(opt['FileName'])
jvault=dict()
t = '@None@' if not '--vault-name' in argv else argv[argv.index('--vault-name')+1]
if os.path.exists('.glaws.vault.json'):
    fh=open('.glaws.vault.json','r')
    jvault=json.load(fh)
    fh.close()
    for m in jvault['VaultList']:
        if 'ShortName' in m and m['ShortName'] == t: t=m['VaultName']
opt['VaultName']=t
jjob=dict()
t = '@None@' if not '--job-id' in argv else argv[argv.index('--job-id')+1]
if os.path.exists('.glaws.job.json'):
    fh=open('.glaws.job.json','r')
    jjob=json.load(fh)
    fh.close()
    for m in jjob['JobList']:
        if not 'ShortId' in m or m['ShortId'] != t:continue
        t=m['JobId']
        if not ('VaultName' in m):continue
        if not ('VaultName' in opt) or opt['VaultName'] != '@None@' : continue
        opt['VaultName'] = m['VaultName']
opt['JobId']=t
#print(opt['VaultName'])
#print(opt['JobId'])
if argv[0] == 'bucket' or argv[0] == 'vault':
    if argv[1] == 'ls':
        if not opt['Verbose']:print("#sid #name")
        else: print("#sid archive size name")
        jvault=json.loads(subprocess.getoutput(('aws glacier list-vaults --account-id %s' % MyAccount)))
        cnt=0
        for m in jvault['VaultList']:
            m['ShortName'] = ("@V%2.2x" % cnt)
            cnt = cnt+1
            print((m['ShortName']+' '),end='')
            if opt['Verbose']:
                  print(" %5d %7.3f GB " % (m['NumberOfArchives'],m['SizeInBytes']/1024/1024/1024),end='')
            print(m['VaultName'])
        fh=open('.glaws.vault.json','w')
        json.dump(jvault,fp=fh)
        fh.close()
    elif argv[1] == 'describe' or argv[1] == 'des':
        print(subprocess.getoutput(
            'aws glacier describe-vault --account-id %s --vault-name %s' % \
            (MyAccount,opt['VaultName'])))
    else:
        print('option for vault is \"ls\" or \"describe\"')

elif argv[0] == 'job':
    if argv[1] == 'ls':
        if opt['VaultName'] == '@None@':
            print('--vault-name is needed')
            exit(1)
        cnt=0
        jjob=dict()
        for v in jvault['VaultList']: ## multi vault code is not completed.
            if opt['VaultName'] != v['VaultName'] and opt['VaultName'] != '@ALL@': continue
            #print(('# vault %s is under scan' % v['VaultName']))
            r=subprocess.getoutput(
                'aws glacier list-jobs --account-id %s --vault-name %s'
                % (MyAccount,v['VaultName']))
            jjob=json.loads(r)
            for m in jjob['JobList']:
                m['ShortId'] = ("@J%2.2x" % cnt)
                m['VaultName'] = v['VaultName']
                s = re.sub('^.*?:vaults/','',m['VaultARN'])
                print("%s %s %s %s" % (m['ShortId'],m['Action'],m['StatusCode'],s))
                cnt = cnt+1
        fh=open('.glaws.job.json','w')
        json.dump(jjob,fp=fh)
        fh.close()
    elif argv[1] == 'describe' or argv[1] == 'des':
        if opt['VaultName'] == '@None@' or opt['JobId'] == '@None':
            print('--vault-name is needed')
            exit(1)
        print(json.loads(subprocess.getoutput(
            'aws glacier describe-job --account-id %s --vault-name %s --job-id %s'
            % (MyAccount,opt['VaultName'],opt['JobId']))))
    elif argv[1] == 'get':
        t0 = datetime.now()
        r=subprocess.getoutput(
            'aws glacier get-job-output --account-id %s --vault-name %s --job-id %s %s'
            % (MyAccount,opt['VaultName'],opt['JobId'],opt['FileName']))
        t1 = datetime.now()
        print(r)
        print('# download %s %d day, %d sec, %d msec' % (opt['FileName'],(t1-t0).days,(t1-t0).seconds,(t1-t0).microseconds))
        tn = ((t1-t0).days*24*3600+(t1-t0).seconds)*1000000+(t1-t0).microseconds
        jo= json.loads(r)
        jo['GetOps'] = {'Start': t0.strftime('v3/%Y-%m-%d %H:%M:%S'),
                        'End': t1.strftime('v3/%Y-%m-%d %H:%M:%S'),
                        'Duration': tn}
        for m in jjob['JobList']:
            if opt['JobId'] == m['JobId'] and 'ArchiveSizeInBytes' in m:
                jo['GetOps']['Size'] = m['ArchiveSizeInBytes']
                
        fh=open('.glaws.getjob.log','a')
        json.dump(jo,fp=fh)
        fh.write('\n')
        fh.close()
    else:
        print('option for job is \"ls\" or \"describe\"')
elif argv[0] == 'archieve' or argv[0] == 'arch':
    if argv[1] == 'submit-ls':
        if opt['VaultName'] != '@None@':
            r=subprocess.getoutput('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (MyAccount,opt['VaultName'],"\'{\"Type\": \"inventory-retrieval\"}\'"))
            jo = json.loads(r)
            print(r)
        else:
            print('--vault-name is needed')
            exit(1)
    else:
        print('option for archive is \"submit-ls\" or \"describe\"')
        
else:
    print('object type must be one \"vault\",\"job\",\"archive\"')
            #print(subprocess.getoutput('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (MyAccount,argv[argv.index('--vault-name')+1],"\'{\"Type\": \"inventory-retrieval\"}\'")))
        #if argv[2] != '--verbose': print("#name")
        #else: print("#archive size name")

