from hancockStorageMonitor.localgatherers.storage_info import storage_info
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand
from pathlib import Path
from os import getuid, readlink
from pprint import pprint
from platform import node
from time import sleep
maxsize = 21
if getuid() != 0:
    print("This program must be run as root.")
    exit(1)
# cProfile.run("storage_info(quick=True)")
# exit(1)
print("--------------------Step 1-------------------------")
info = storage_info()
if len(info.raidarrays) != 0:
    print("Detected md RAID arrays on host. Cannot continue safely.")
    exit(1)

print("--------------------Step 3-------------------------")
lvnames = {info.lvs[dmname].attributes['name']:dmname for dmname in info.lvs}
bitmappath = Path('/bitmap')
if not bitmappath.is_dir():
    bitmappath.mkdir()

if 'sysvg-bitmap' not in lvnames:
    print("Trying to create sysvg-bitmap")
    command = ['lvcreate','-L','1G','-n','bitmap','sysvg']
    print("Running command", command)
    # result = {'returncode':0}
    result = errorHandledRunCommand(command=command)
    if result is None or result['returncode'] != 0:
        print("\nI encountered an error while trying to create a missing /bitmap lv on sysvg")
        print("\nI cannot continue.")
        exit(1)
    print(result['stdout'])
    print("Leaving sysvg-bitamp")
    sleep(5)

print("--------------------Step 4-------------------------")
filesystem = 'ext4'
#Check if there is a filesystem on /dev/mapper/sysvg-bitmap
command = ['wipefs','/dev/mapper/sysvg-bitmap']
result = errorHandledRunCommand(command=command)
print(result['stdout'].splitlines())
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to check for a filesystem on /dev/mapper/sysvg-bitmap")
    print("\nI cannot continue.")
    exit(1)
else:
    output = result['stdout'].splitlines()
    print(output)
    if len(output) > 2 and 'filesystem' in output[2]:
        print("The following filesystems were detected on /dev/mapper/sysvg-bitmap")
        print(result['stdout'])
        filesystem = output[2].split()[1].strip()
    else:
        #Create the missing filesystem.
        command = ['mkfs.ext4','/dev/mapper/sysvg-bitmap']
        result = errorHandledRunCommand(command=command)
        if result is None or result['returncode'] != 0:
            print("\nI encountered an error while trying to create a filesystem on /dev/mapper/sysvg-bitmap")
            print("\nI cannot continue.")
            exit(1)
        else:
            filesystem = 'ext4'
print("--------------------Step 5-------------------------")
#make sure the bitmaps logical volume is mounted
if '/bitmap' not in Path('/proc/mounts').read_text():
    command = ['mount','/dev/mapper/sysvg-bitmap','/bitmap']
    result = errorHandledRunCommand(command=command)
    if result is None or result['returncode'] != 0:
        print("\nI encountered an error while trying to mount /dev/mapper/sysvg-bitmap on /bitmap")
        print("\nI cannot continue.")
        exit(1)
    sleep(10)
print("--------------------Step 6-------------------------")
fstabpath = Path('/etc/').joinpath('fstab')
if '/bitmap' not in fstabpath.read_text():
    with fstabpath.open('a') as f:
        f.write("\n/dev/mapper/sysvg-bitmap	/bitmap	"+filesystem+"	defaults	0	0\n")