#! env python3
import subprocess

# you need to set your own Account and Vault Name in local.py file
MyAccount="Empty"
MyVault="Empty"
#MySNS="Empty"
from cdbackup import *

if 'MySNS' in globals() and MySNS != "Empty":
    jpar="\'{\"Type\": \"inventory-retrieval\",\"SNSTopic\": \"%s\"}\'" % MySNS
else:
    jpar="\'{\"Type\": \"inventory-retrieval\"}\'"
r=subprocess.getoutput("aws glacier initiate-job --account-id %s --vault-name %s --job-parameters %s" % (MyAccount,MyVault,jpar))
print(r)
