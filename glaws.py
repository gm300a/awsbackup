#! env python3
from datetime import datetime
from treehash import TreeHash
import json
import os.path
import re
import subprocess
import sys

# you need to set your own Account and Vault Name in local.py file
(csize,MyAccount,MyVault)=(1024*1024*256,"Empty","Empty") # 256MB for test
from local import *

argv=sys.argv[1:]
opt=dict()
opt['Verbose']=('--verbose' in argv)
opt['FileName'] = '@None@' if not '--file-name' in argv else argv[argv.index('--file-name')+1]
    
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
        else: print("#sid  arch size(GB)  name")
        jvault=json.loads(subprocess.getoutput(('aws glacier list-vaults --account-id %s' % MyAccount)))
        cnt=0
        for m in jvault['VaultList']:
            m['ShortName'] = ("@V%2.2x" % cnt)
            cnt = cnt+1
            print((m['ShortName']+' '),end='')
            if opt['Verbose']:
                  print("%5d %8.3f " % (m['NumberOfArchives'],m['SizeInBytes']/1024/1024/1024),end='')
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
                if not opt['Verbose'] :
                    print("%s %s %s %s" % (m['ShortId'],m['Action'],m['StatusCode'],s))
                if not m['Completed']:
                    print("%s %s %s %s %s" % (m['ShortId'],m['Action'],m['CreationDate'],m['StatusCode'],s))
                else:
                    print("%s %s %s %s %s" % (m['ShortId'],m['Action'],m['CreationDate'],m['CompletionDate'],s))
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
        if opt['JobId'] == '@None@':
            print('error, job id is neede')
            exit(1)
        if opt['FileName'] == '@None@':
            for i in range(0,10000):
                opt['FileName']=('log/glaws.%3.3X.output' % i)
                if not os.path.exists(opt['FileName']):break

        print('## output to',opt['FileName'])
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
        print('error, option for job is \"ls\" or \"describe\"')
elif argv[0] == 'archieve' or argv[0] == 'arch':
    if argv[1] == 'submit-ls':
        if opt['VaultName'] != '@None@':
            r=subprocess.getoutput('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (MyAccount,opt['VaultName'],"\'{\"Type\": \"inventory-retrieval\"}\'"))
            jo = json.loads(r)
            print(r)
        else:
            print('--vault-name is needed')
            exit(1)
    elif argv[1] == 'cache-ls':
        if opt['FileName'] == '@None@':
            print('error, --file-name is needed')
        else:
            fh=open(opt['FileName'],'r')
            jo=json.load(fh)
            for m in jo['ArchiveList']:
                if m['ArchiveDescription'] == '':
                    dsc='-no descrtiption-'
                else:
                    n = m['ArchiveDescription'].split('/')
                    if n[0] != 'v3':
                        dsc='-format error:'+n[0]
                    else:
                        dsc=n[1].replace('@2',' ').replace('@1',':')+' '+n[2].replace('@3','/').replace('@2',' ').replace('@1',':').replace('@0','@')
                print(('%s %7.3fG %s' % (m['CreationDate'],int(m['Size'])/1024/1024/1024,dsc)))
    else:    
        print('error, option for archive is \"submit-ls\" or \"describe\"')
        
elif argv[0] == 'config' or argv[0] == 'conf':
    if argv[1] == 'region':
        if len(argv) < 3:
            fh=open(os.environ.get('HOME')+'/.aws/config','r')
            print(fh.readline(),end='')
            print(fh.readline(),end='')
            print(fh.readline(),end='')
#            (d,p)=input().rstrip().split(' ')
else:
    print('object type must be one \"vault\",\"job\",\"archive\"')
            #print(subprocess.getoutput('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (MyAccount,argv[argv.index('--vault-name')+1],"\'{\"Type\": \"inventory-retrieval\"}\'")))
        #if argv[2] != '--verbose': print("#name")
        #else: print("#archive size name")

