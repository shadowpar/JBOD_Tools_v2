from hancockStorageMonitor.analysis.dbaudit import dbaudit
from json import dump
from storageMonitorWeb.views import staticErrorDataFile
print(staticErrorDataFile.as_posix())

mine = dbaudit()

if not staticErrorDataFile.is_file():
    staticErrorDataFile.touch(mode=777)
#sort the output according to display name for prettier displaying.
data = mine.overviewErrorData
with staticErrorDataFile.open(mode='w') as f:
    weboutput = {'overviewErrorData':data,'displayNameMaps':mine.maps.getDisplayNameMaps()}
    dump(weboutput,f)