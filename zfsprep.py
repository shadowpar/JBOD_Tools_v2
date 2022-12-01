from hancockStorageMonitor.localgatherers.storage_info import storage_info
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand, multiExecuteExternal
from os import getuid
maxsize = 21
if getuid() != 0:
    print("This program must be run as root.")
    exit(1)


print("--------------------Step 1-------------------------")
info = storage_info()
# if len(info.raidarrays) != 0:
#     print("Detected md RAID arrays on host. Cannot continue safely.")
#     exit(1)
print("--------------------Step 2-------------------------")
chassis = [chassis for chassis in info.harddrivesByChassis]
chassis = {chassis.index(serial):serial for serial in chassis}
if len(chassis) > 1:
    while True:
        print("Please select a chassis to create a ZFS pool from the following list.")
        for entry in chassis:
            print(entry,':',chassis[entry])
        try:
            choice = int(input())
            if choice in chassis:
                chosenChassis = choice
                break
            else:
                print("please only enter a number from the list")
        except ValueError:
            print("please only enter a number from the list")
else:
    chosenChassis = 0
chosenChassis = chassis[chosenChassis]
print("--------------------Step 3-------------------------")
targets = {}
exDriveCapacity = None
for serial in  info.harddrivesByChassis[chosenChassis]:
    if exDriveCapacity is None: exDriveCapacity = info.harddrivesByChassis[chosenChassis][serial].attributes['capacity']
    index = int(info.harddrivesByChassis[chosenChassis][serial].attributes['index'])
    firstld = info.harddrivesByChassis[chosenChassis][serial].attributes['children'][0]
    targets[index] = firstld
targets = {key:targets[key] for key in sorted(targets)}
targets = list(targets.values())
alldisks = targets
print("--------------------Step 4-------------------------")
#Flush multipath maps
command = ['multipath','-F']
print("Running command",command)
# result = {'returncode':0}
result = errorHandledRunCommand(command=command)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to flush multipath maps.")
    print("\nI cannot continue.")
    exit(1)

#now we partition the disks to prepare them to become part of RAID arrays
print("--------------------Step 5-------------------------")
#use async commands to parallel run all dd's
commands = ['dd if=/dev/zero bs=1M count=2048 of=/dev/'+target for target in alldisks]
results = multiExecuteExternal(commandStrings=commands)
shouldQuit = False
for command in commands:
    if results[command]['returncode'] != 0:
        print("There was an error running command",command)
        shouldQuit=True
        print(results[command]['stdout'])
        print(results[command]['stderr'])
if shouldQuit:
    exit(1)
print("--------------------Step 6-------------------------")
# use async commands to parallel run all parted's
commands = ['parted -s /dev/'+target+' mklabel gpt' for target in alldisks]
results = multiExecuteExternal(commandStrings=commands)
shouldQuit = False
for command in commands:
    if results[command]['returncode'] != 0:
        print("There was an error running command", command)
        shouldQuit = True
        print(results[command]['stdout'])
        print(results[command]['stderr'])
if shouldQuit:
    exit(1)
print("--------------------Step 7-------------------------")
#Ensure multipath is running.
command = ['multipath']
print("Running command",command)
# result = {'returncode':0}
result = errorHandledRunCommand(command=command)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to rebuild the multipath maps.")
    print("\nI cannot continue.")
    exit(1)
print("ZFS prep finished. Please run python3 zfspoolmaker.py to continue creating a zfs pool on this chassis.")