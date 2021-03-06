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
     'Range':0 if not '--header' in argv else 1024*1024-1,\
     'Full':('--full-length' in argv),\
     'V3File':('--v3-file-name' in argv or '-v3' in argv),\
     'Verbose':('--verbose' in argv),'ShowId':('--show-id' in argv),\
     'HumanRead':('-h' in argv or '--human-readable' in argv)}
#print('## opt range {}'.format(opt['Range']))
if '--range-test' in argv:
    opt['Range'] = int(argv[argv.index('--range-test')+1])
#print('## opt range {}'.format(opt['Range']))
awstmp='aws glacier {} --account-id '+opt['Account']
if not opt['Full'] and opt['Range'] == 0:
    opt['Range'] = 1024*1024-1
if opt['Range'] != 0 and (opt['Range']+1) % 1024*1024 != 0:
    opt['Range'] = int((opt['Range']+1024*1024-1)/1024/1024)*1024*1024-1
    print('# range is aligned to MB boundary,{}'.format(opt['Range']))

jvault=dict()
t = '@None@' if not '--vault-name' in argv else argv[argv.index('--vault-name')+1]
if os.path.exists('.glaws.vault.json'):
    with open('.glaws.vault.json','r') as fh: jvault=json.load(fh)
    if len(jvault['VaultList']) == 1 and t == '@None@' :
        t = jvault['VaultList'][0]['VaultName']
    else:
        for m in jvault['VaultList']:
            if 'ShortName' in m and m['ShortName'] == t: t=m['VaultName']
opt['VaultName']=t
jjob=dict()
t = '@None@' if not '--job-id' in argv else argv[argv.index('--job-id')+1]
if os.path.exists('.glaws.job.json'):
    with open('.glaws.job.json','r') as fh:jjob=json.load(fh)
    for m in jjob['JobList']:
        if not 'ShortId' in m or m['ShortId'] != t:continue
        t=m['JobId']
        if 'JobDescription' in m: opt['JobDescription'] = m['JobDescription']
        if 'VaultName' in m and (not ('VaultName' in opt) or opt['VaultName'] == '@None@') :
            opt['VaultName'] = m['VaultName']
opt['JobId']=t
if argv[0] == 'bucket' or argv[0] == 'vault':
    if argv[1] == 'ls':
        if not opt['Verbose']:print("#sid #name")
        else: print("#sid  arch size(GB)  name")
        (s,r)=subprocess.getstatusoutput(awstmp.format('list-vaults'))
        if s != 0 :errorexit(r)
        jvault=json.loads(r)
        cnt=0
        for m in jvault['VaultList']:
            m['ShortName']=("@V%2.2x" % cnt)
            cnt = cnt+1
            print((m['ShortName']+' '),end='')
            if opt['Verbose']:
                  print("%5d %8.3f " % (m['NumberOfArchives'],m['SizeInBytes']/1024/1024/1024),end='')
            print(m['VaultName'])
        with open('.glaws.vault.json','w') as fh:json.dump(jvault,fp=fh)
    elif argv[1] == 'describe' or argv[1] == 'des':
        (s,r)=subprocess.getstatusoutput(
            awstmp.format('describe-vault')+\
            ' --vault-name {}'.format(opt['VaultName']))
        print(r)
    else: errorexit('option for vault is \"ls\" or \"describe\"')

elif argv[0] == 'job':
    if argv[1] == 'ls':
        if opt['VaultName'] == '@None@': errorexit('error,--vault-name is needed')
        (s,r)=subprocess.getstatusoutput(
            awstmp.format('list-jobs')+' --vault-name {}'.format(opt['VaultName']))
        if s != 0: errorexit(r)
        jjob=dict()
        jjob=json.loads(r)
        cnt=0
        for m in jjob['JobList']:
            m['ShortId'] = ("@J%2.2x" % cnt)
            m['VaultName'] = opt['VaultName']
            s = re.sub('^.*?:vaults/','',m['VaultARN'])
            print("{} {:20} ".format(m['ShortId'],m['Action']),end='')
            if not opt['Verbose'] :  print("%-25s %s" % (m['StatusCode'],s))
            elif not m['Completed']: print("%-25s %-25s %s" % (m['CreationDate'],m['StatusCode'],s))
            else:                    print("%-25s %-25s %s" % (m['CreationDate'],m['CompletionDate'],s))
            cnt = cnt+1
        if cnt == 0 :print('## no job found')
        with open('.glaws.job.json','w') as fh:json.dump(jjob,fp=fh)
    elif argv[1] == 'describe' or argv[1] == 'des':
        if opt['VaultName'] == '@None@' or opt['JobId'] == '@None': print('error, --vault-name is needed')
        (s,r)=subprocess.getoutput(awstmp.format('describe-job')+' --vault-name {}'.format(opt['VaultName'])+\
                                   '--job-id {}'.format(opt['JobId']))
        if s != 0: errorexit(r)
        print(json.loads(r))
    elif argv[1] == 'get':
        if opt['JobId'] == '@None@' or opt['VaultName'] == '@None@' : errorexit('error, job id is needed')
        if opt['FileName'] != '@None@':
            pass
        elif opt['V3File'] and 'JobDescription' in opt:
            n = opt['JobDescription'].split('/')
            if n[0] != 'v3' :errorexit('description is not a V3 format({})'.format(opt['JobDescription']))
            #fn=n[2].replace('@3','/').replace('@2',' ').replace('@1',':').replace('@0','@')
            opt['FileName'] = n[2]
        else:
            for i in range(0,10000):
                opt['FileName']=('log/glaws.%3.3X.output' % i)
                if not os.path.exists(opt['FileName']):break

        print('## output to',opt['FileName'])
        t0 = datetime.now()
        tcmd=awstmp.format('get-job-output')+' --vault-name {}'.format(opt['VaultName']) +\
               ' --job-id {} {}'.format(opt['JobId'],opt['FileName'])
        #print(tcmd)
        (s,r)=subprocess.getstatusoutput(tcmd)
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

        with open('.glaws.getjob.log','a') as fh:
            json.dump(jo,fp=fh)
            fh.write('\n')
    else:
        print('error, option for job is \"ls\", \"describe\" or "get"')
elif argv[0] == 'archieve' or argv[0] == 'arch':
    if argv[1] == 'submit-ls':
        if opt['VaultName'] == '@None@': errorexit('error, --vault-name is needed')
        jpar=dict({'Type':'inventory-retrieval'})
        tcmd=awstmp.format('initiate-job')+' --vault-name {}'.format(opt['VaultName'])+\
            ' --job-parameters \'{}\''.format(json.dumps(jpar))
        #print(tcmd)
        (s,r)=subprocess.getstatusoutput(tcmd)
        if s != 0 :errorexit(r)
        jo=json.loads(r)
        print('# job id {}'.format(jo['jobId']))
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
        jpar=dict({'Type' : 'archive-retrieval', 'ArchiveId' : opt['ArchiveID'],'Tier' : 'Bulk',\
                   'Description' : opt['Description']})
        print('## json jpar {}'.format(json.dumps(jpar)))
        #print('## opt range {}'.format(opt['Range']))
        print("### you need to specify the option to down load whole file")
        if opt['Range'] != 0:
            jpar['RetrievalByteRange'] = '{}-{}'.format(0,opt['Range'])
            if 1024*1024*128 < opt['Range']: r='{:.3}G'.format(opt['Range']/1024/1024/1024)
            elif 1028*128 < opt['Range']: r='{:.3f}M'.format(opt['Range']/1024/1024)
            print('## range applied {}Byte'.format(r))
        a=awstmp.format('initiate-job')+\
           ' --job-parameters \'{}\''.format(json.dumps(jpar))+\
           ' --vault-name {}'.format(opt['VaultName'])
        print('## debug {}'.format(a))
        print('## json jpar {}'.format(json.dumps(jpar)))
        
        (s,r)=subprocess.getstatusoutput(a)
        if s != 0 : errorexit(r)
        print('next line may cause an error. but job is already submitted successfully')
        jo=json.loads(r)
        if opt['Verbose']:print('# job id {}'.format(jo['jobId']))
    else: errorexit('error, option for archive is \"submit-ls\", "submit-copy", "cache-ls" or \"describe\"')

elif argv[0] == 'config' or argv[0] == 'conf':
    if argv[1] == 'region':
        if len(argv) < 3:
            fh=open(os.environ.get('HOME')+'/.aws/config','r')
            print(fh.readline(),end='')
            print(fh.readline(),end='')
            print(fh.readline(),end='')
#            (d,p)=input().rstrip().split(' ')
else:errorexit('error, object type must be one \"vault\",\"job\",\"archive\"')

