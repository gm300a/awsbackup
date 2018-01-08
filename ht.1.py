#! env python3
import sys
from treehash import TreeHash

fh=open(sys.argv[1],"rb")
ft=fh.read()
print(len(ft))
fh.close()
mt=TreeHash();mt.update(ft);print(mt.hexdigest())
mt=TreeHash();mt.update(ft);print(mt.hexdigest())
mt=TreeHash();mt.update(ft);print(mt.hexdigest())
mt=TreeHash();mt.update(ft);print(mt.hexdigest())

