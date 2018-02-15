#! env python3
from datetime import datetime
from treehash import TreeHash
import json,os.path,re,subprocess,sys

# you need to set your own Account and Vault Name in local.py file
opt=dict()
(csize,MyAccount,MyVault)=(1024*1024*256,"Empty","Empty") # 256MB for test
from local import *
def errorexit(msg):
    print(msg)
    exit(1)

argv=sys.argv[1:]
opt={'Account':MyAccount,
     'Description':'@None@' if not '--description' in argv else argv[argv.index('--description')+1],\
     'FileName':'@None@' if not '--file-name' in argv else argv[argv.index('--file-name')+1],\
     'ArchiveID':'@None@' if not '--arch-id' in argv else argv[argv.index('--arch-id')+1],\
     'Range':0 if not '--header' in argv else 1024*1024,\
     'Verbose':('--verbose' in argv),'ShowId':('--show-id' in argv),\
     'HumanRead':('-h' in argv or '--human-readable' in argv)}
awstmp='aws glacier {} --account-id '+opt['Account']
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
        (s,r)=subprocess.getstatusoutput(awstmp.format('list-vaults'))
        if s != 0 :errorexit(r)
        jvault=json.loads(r)
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
        (s,r)=subprocess.getstatusoutput(\
            'aws glacier describe-vault --account-id {} --vault-name {}'.format(opt['Account'],opt['VaultName']))
        print(r)
    else: errorexit('option for vault is \"ls\" or \"describe\"')

elif argv[0] == 'job':
    if argv[1] == 'ls':
        if opt['VaultName'] == '@None@': errorexit('error,--vault-name is needed')
        cnt=0
        jjob=dict()
        for v in jvault['VaultList']: ## multi vault code is not completed.
            if opt['VaultName'] != v['VaultName'] and opt['VaultName'] != '@ALL@': continue
            #print(('# vault %s is under scan' % v['VaultName']))
            (s,r)=subprocess.getstatusoutput(
                'aws glacier list-jobs --account-id {} --vault-name {}'.format(opt['Account'],v['VaultName']))
            if s != 0: errorexit(r)
            jjob=json.loads(r)
            for m in jjob['JobList']:
                m['ShortId'] = ("@J%2.2x" % cnt)
                m['VaultName'] = v['VaultName']
                s = re.sub('^.*?:vaults/','',m['VaultARN'])
                if not opt['Verbose'] :
                    print("%s %s %s %s" % (m['ShortId'],m['Action'],m['StatusCode'],s))
                elif not m['Completed']:
                    print("%s %s %s %s %s" % (m['ShortId'],m['Action'],m['CreationDate'],m['StatusCode'],s))
                else:
                    print("%s %s %s %s %s" % (m['ShortId'],m['Action'],m['CreationDate'],m['CompletionDate'],s))
                cnt = cnt+1
        fh=open('.glaws.job.json','w')
        json.dump(jjob,fp=fh)
        fh.close()
    elif argv[1] == 'describe' or argv[1] == 'des':
        if opt['VaultName'] == '@None@' or opt['JobId'] == '@None': print('error, --vault-name is needed')
        (s,r)=subprocess.getoutput(awstmp.format('describe-job')+' --vault-name {}'.format(opt['VaultName'])+\
                                   '--job-id {}'.format(opt['JobId']))
        if s != 0: errorexit(r)
        print(json.loads(r))
    elif argv[1] == 'get':
        if opt['JobId'] == '@None@' or opt['VaultName'] == '@None@' :
            print('error, job id is needed')
            exit(1)
        if opt['FileName'] == '@None@':
            for i in range(0,10000):
                opt['FileName']=('log/glaws.%3.3X.output' % i)
                if not os.path.exists(opt['FileName']):break

        print('## output to',opt['FileName'])
        t0 = datetime.now()
        (s,r)=subprocess.getstatusoutput(
            'aws glacier get-job-output --account-id {} --vault-name {} '.format(opt['Account'],opt['VaultName']) +
               '--job-id {} {}'.format(opt['JobId'],opt['FileName']))
        if s != 0 : errorexit(r)
        t1 = datetime.now()
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
        if opt['VaultName'] == '@None@': errorexit('error, --vault-name is needed')
        (s,r)=subprocess.getoutput(awstmp.format('initiate-job')+' --vault-name {}'.format(opt['VaultName'])+\
                                   ' --job-parameters {}'.format("\'{\"Type\": \"inventory-retrieval\"}\'"))
        if s != 0 :errorexit(r)
        print(json.loads(r))
    elif argv[1] == 'cache-ls':
        if opt['FileName'] == '@None@': errorexit('error, --file-name is needed')
        with open(opt['FileName'],'r') as fh: jo=json.load(fh)
        print('1. Header')
        print('  - VaultARN:',jo['VaultARN'])
        cnt = 0 if not 'LastShortName' in jo else jo['LastShortName']
        jo['LastShortName']=cnt
        for m in jo['ArchiveList']:
            if not 'ShortName' in m:
                m['ShortName']='@A{:03x}'.format(cnt)
                cnt=cnt+1
            if m['ArchiveDescription'] == '': dsc='-no descrtiption-'
            else:
                n = m['ArchiveDescription'].split('/')
                if n[0] != 'v3': dsc='-format error:'+n[0]
                elif not opt['HumanRead']:
                    dsc=m['ArchiveDescription']
                elif opt['Verbose']:
                    dsc=n[1].replace('@2',' ').replace('@1',':')+' '+\
                         n[2].replace('@3','/').replace('@2',' ').replace('@1',':').replace('@0','@')
                else:
                    dsc=n[2].replace('@3','/').replace('@2',' ').replace('@1',':').replace('@0','@')
                    #sz=('{:6.2f}'.format(int(m['Size'])/1024./1024./1024.)) if opt['HumanRead'] else ('{:10}'.format(int['Size']))
            sz=('{:5.2f}'.format(int(m['Size'])/1024./1024./1024.)) if opt['HumanRead'] else ('{:15}'.format(int(m['Size'])))
            cd=(m['CreationDate'].replace('T',' ').replace('Z',' ')) if opt['Verbose'] else ''
            im=('' if not opt['ShowId'] else m['ArchiveId']) # 
            print('{} {} {} '.format(m['ShortName'],cd,sz),end='')
            print('{} {}'.format(dsc.encode('utf-8'),im))
            #print('{} {} {:7,}G {}'.format(m['ShortName'],m['CreationDate'],m['Size'],dsc))
        if cnt != jo['LastShortName']:
            jo['LastShortName']=cnt
            with open(opt['FileName']+'t','w') as fh: json.dump(jo,fh)
    elif argv[1] == 'submit-copy':
        if opt['FileName'] != '@None@' :
            with open(opt['FileName'],'r') as fh: jo=json.load(fh)
            n=jo['VaultARN'].split(':')
            opt.update({'Region':n[3],'Account':n[4],'VaultName':n[5][7:]})
            for m in jo['ArchiveList']:
                if 'ShortName' in m and m['ShortName'] == opt['ArchiveID'] or m['ArchiveId'] == opt['ArchiveID']:
                    opt['ArchiveID'] = m['ArchiveId']
                    opt['Description'] = m['ArchiveDescription'] 
                    break
            if len(opt['ArchiveID']) < 10:
                errorexit('error, Archive ID too short or incorrect ({})'.format(opt['ArchiveID']))
        jpar=dict()
        jpar={'Type' : 'archive-retrieval', 'ArchiveId' : opt['ArchiveID'],'Tier' : 'Bulk', 'Description' : opt['Description']}
        if opt['Range'] != 0:
            jpar['RetrievalByteRange'] = '{}-{}'.format(0,opt['Range'])
        a=awstmp.format('initiate-job')+\
           ' --job-parameters \'{}\''.format(json.dumps(jpar))+\
           ' --vault-name {}'.format(opt['VaultName'])
#        print(a)
        (s,r)=subprocess.getstatusoutput(a)
        if s != 0 :
            print(r)
            exit(1)
        print(r)
    else: errorexit('error, option for archive is \"submit-ls\" or \"describe\"')
        
elif argv[0] == 'config' or argv[0] == 'conf':
    if argv[1] == 'region':
        if len(argv) < 3:
            fh=open(os.environ.get('HOME')+'/.aws/config','r')
            print(fh.readline(),end='')
            print(fh.readline(),end='')
            print(fh.readline(),end='')
#            (d,p)=input().rstrip().split(' ')
else:errorexit('error, object type must be one \"vault\",\"job\",\"archive\"')
            #print(subprocess.getoutput('aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s' % (opt['Account'],argv[argv.index('--vault-name')+1],"\'{\"Type\": \"inventory-retrieval\"}\'")))
        #if argv[2] != '--verbose': print("#name")
        #else: print("#archive size name")

