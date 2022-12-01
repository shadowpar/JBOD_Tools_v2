from pathlib import Path

def parseProcDevices():
    devType = None
    devices = {'character':{},'block':{}}
    procDevPath = Path('/proc/devices')
    contents = procDevPath.read_text().splitlines()
    for line in contents:
        if 'character devices:' in line.casefold():
            devType = 'character'
        elif 'block devices:' in line.casefold():
            devType = 'block'
        elif line.strip() == '':
            continue
        else:
            data = line.split()
            majornum = data[0].strip()
            driver = data[1].strip()
            devices[devType][majornum] = driver
    return devices

def parseProcPartitions(inverse=False):
    procPartPath = Path('/proc/partitions')
    blockDevices = {}
    if not procPartPath.is_file():
        print("Unable to locate the /proc/partitions file.")
        return None
    data = procPartPath.read_text().splitlines()
    for line in data:
        if 'blocks' in line.lower():
            continue
        parts = line.split()
        if len(parts) == 4:
            major = parts[0].strip()
            minor = parts[1].strip()
            name = parts[3].strip()
            if major in blockDevices:
                blockDevices[major][minor] = name
            else:
                blockDevices[major] = {minor:name}
    if not inverse:
        return blockDevices
    elif inverse:
        inverseBlockDevices = {}
        for major in blockDevices:
            for minor in blockDevices[major]:
                name = blockDevices[major][minor]
                inverseBlockDevices[name] = {'major':major,'minor':minor}
        return inverseBlockDevices


