
# program to convert nwb_core.py specification language file to JSON 
# format

import nwb_core
import json

json=json.dumps(nwb_core.nwb, indent=4, separators=(',', ': '))
f1=open('nwb_core.json', 'w')
f1.write(json)
