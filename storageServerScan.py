#!/usr/bin/python3.6
from pathlib import Path
from hancockStorageMonitor.localgatherers.storage_info import storage_info
from os import getuid, getgid
# import sys
from datetime import datetime

#check for root privileges. This program requirse them. exit if not.
if getuid() != 0:
    print("This program requires root privileges. Please try again as root or with sudo.")

# def tracefunc(frame, event, arg, indent=[0]):
#     if event == "call":
#         indent[0] += 2
#         frame.f_code
#         print("-" * indent[0] + "> call function", frame.f_code.co_name)
#     elif event == "return":
#         print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
#         indent[0] -= 2
#     return tracefunc
#
#
# sys.setprofile(tracefunc)

#Maintain consistency with changing cron choices. Additionally, cron is setup by manually running the associated program once.
associatedCron = Path('/etc').joinpath('cron.d').joinpath('storageMonitor.cron')
localCronCopy = Path('hancockStorageMonitor').joinpath('common').joinpath('storageMonitor.cron')
if not associatedCron.is_file() or associatedCron.read_text() != localCronCopy.read_text():
    associatedCron.write_text(localCronCopy.read_text())

logPath = Path('/var').joinpath('log').joinpath('storageMonitor')
if not  logPath.is_dir(): logPath.mkdir(mode=777)
for item in [logPath.joinpath('errors.log'),logPath.joinpath('storage_info.log')]:
    item.write_text("New run commenced on "+str(datetime.now())+"\n\n")
mainLog = logPath.joinpath('storageMonitor.log')
errorLog = logPath.joinpath('errors.log')

#This class gatherers all appropriate information about the system and writes it out to json data in /tmp on instantiation.
mine = storage_info()
mine.exportDictionary()