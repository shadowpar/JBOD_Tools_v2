from hancockStorageMonitor.localgatherers.scsiOperations import multiExecuteExternal, multiExecute, errorHandledRunCommand
from pprint import pprint
import json
from datetime import datetime
timeNow = datetime.now()
drives = ['sda','sdb','sdc']
commands = ['smartctl -a /dev/'+item+' --json' for item in drives]
results = multiExecuteExternal(commandStrings=commands)
results = {key:json.loads(results[key]['stdout']) for key in results}
pprint(results)
timeone = datetime.now()
timefirst = timeone-timeNow
print('------------------old way-------------------------')
func = errorHandledRunCommand
kwargs = [{'command':'smartctl -a /dev/sda --json'},{'command':'smartctl -a /dev/sdb -json'},{'command':'smartctl -a /dev/sdb --json'}]
results = multiExecute(func,kwargs)
results = {key:json.loads(results[key]['stdout']) for key in results}
pprint(results)
print("First version took ",timefirst)
print("The second version took",datetime.now()-timeone)

