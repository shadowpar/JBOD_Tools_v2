#!/usr/bin/python3

from hancockStorageMonitor.common.displays import showdisks
from hancockStorageMonitor.localgatherers.storage_info import storage_info
from hancockStorageMonitor.localgatherers.storage_infoAsync import storage_infoAsync
from contextlib import redirect_stdout, redirect_stderr
from os import system
import cProfile

def main():
    system("clear")
    with open('/dev/null','w') as f, redirect_stdout(f), redirect_stderr(f):
        info = storage_infoAsync()
    colors = {'sep':"BLUE",'header':"WHITE",'clabel':"WHITE",'normal':"GREEN"}
    highlights = {'None':"LIGHTRED_EX",'Error':"RED",'missing':"RED",'Missing':"RED"}
    if info.this_server.hasdmraid:
        showdisks(info=info,colors=colors,highlights=highlights)
    elif info.this_server.haszfs:
        #  Later add a different showdisks function for ZFS hosts that does not reference MD RAID stuff
        showdisks(info=info,colors=colors,highlights=highlights)
    else:
        #  Later add a different showdisks function for non storage servers.
        showdisks(info=info,colors=colors,highlights=highlights)
main()
from pathlib import Path
Path().resolve()