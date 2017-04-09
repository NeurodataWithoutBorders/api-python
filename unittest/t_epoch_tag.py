#!/usr/bin/python
import sys
# import nwb
from nwb import nwb_file
from nwb import nwb_utils as utils
import test_utils as ut

# create two epochs, add different subset of tags to each
# verify main epoch folder has tag attribute that contains
#   exactly the unique tags of each epoch and that each
#   epoch contains the assigned tags
    
if __file__.startswith("./"):
    fname = "s" + __file__[3:-3] + ".nwb"
else:
    fname = "s" + __file__[1:-3] + ".nwb"
# borg = ut.create_new_file(fname, "Epoch tags")

f = nwb_file.open(fname,
    start_time="2008-09-15T15:53:00-08:00",
    mode="w",
    identifier=utils.create_identifier("Epoch tags"),
    description="softlink test",
    verbosity="none")

tags = ["tag-a", "tag-b", "tag-c"]

# epoch1 = borg.create_epoch("epoch-1", 0, 3);

epoch1 = f.make_group("<epoch_X>", "epoch-1")
epoch1.set_dataset("start_time", 0)
epoch1.set_dataset("stop_time", 3)

# for i in range(len(tags)-1):
#     epoch1.add_tag(tags[i+1])
epoch1.set_dataset("tags", tags[1:])

# epoch2 = borg.create_epoch("epoch-2", 1, 4);
epoch2 = f.make_group("<epoch_X>", "epoch-2")
epoch2.set_dataset("start_time", 1)
epoch2.set_dataset("stop_time", 4)

# for i in range(len(tags)-1):
#     epoch2.add_tag(tags[i])
epoch2.set_dataset("tags", tags[0:-1])

f.close()

# this test modified because tags are stored as dataset rather than attribute
# tags = ut.verify_attribute_present(fname, "epochs/epoch-1", "tags");
tags = ut.verify_present(fname, "epochs/epoch-1", "tags");
for i in range(len(tags)-1):
    if tags[i+1] not in tags:
        ut.error("Verifying epoch tag content", "All tags not present")

# tags = ut.verify_attribute_present(fname, "epochs/epoch-2", "tags");
tags = ut.verify_present(fname, "epochs/epoch-2", "tags");
for i in range(len(tags)-1):
    if tags[i] not in tags:
        ut.error("Verifying epoch tag content", "All tags not present")

tags = ut.verify_attribute_present(fname, "epochs", "tags");
for i in range(len(tags)):
    if tags[i] not in tags:
        ut.error("Verifying epoch tag content", "All tags not present")


print("%s PASSED" % __file__)

