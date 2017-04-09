# script to set the "orig" (original) directory to the "curr" (current) directory

# Details: 
# If orig exists, moves it to orig_bkNN (NN == 01, 02, 03, ...).
# then moves "curr" to "orig".

import shutil
import os
import glob
import re

if not os.path.isdir("curr"):
    print ("Directory 'curr' does not exist.  Cannot set orig to curr.  Aborting.")
    sys.exit(1)

if os.path.isdir("orig"):
    # orig exists, move it to orig_bkNN
    
    bk_files=sorted(glob.glob("orig_bk[0-9]*"))
    if bk_files:
        lastf=bk_files[-1]
        match = re.match("orig_bk([0-9]*)", lastf)
        if not match:
            print("Unable to isolate integer in name: %s" % lastf)
            sys.exit(1)
        last_num = int(match.group(1))
        next_num =last_num + 1
        next_name = "orig_bk%02i" % next_num
        # print ("next_name is %s" % next_name)
    else:
        next_name = "orig_bk01"
    print ("Renaming 'orig' => '%s'" % next_name)
    os.rename("orig", next_name)

# now copy 'curr' to 'orig'
print ("Copying 'curr' to 'orig'")
shutil.copytree("curr", "orig")

print ("all done")





