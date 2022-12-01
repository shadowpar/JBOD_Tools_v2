from typing import ItemsView
from hancockStorageMonitor.common.ssh import ssh_external_run_remote_command, ssh_get_remote_dirlist,  ssh_get_remote_file_contents, ssh_external_run_remote_command, ssh_run_remote_command
from pprint import pprint
import random
from hancockStorageMonitor.localgatherers.scsiOperations import multiExecute

sysctlclasses = {'abi':'Execution domains and personalities',
                'crypto':'Cryptographic interfaces',
                'debug':'Kernel debugging interfaces ',
                'dev':'Device-specific information ',
                'fs':'Global and specific file system tunables',
                'kernel':'Global kernel tunables ',
                'net':'Network tunables',
                'sunrpc':'Sun Remote Procedure Call (NFS)',
                'user':'User Namespace limits',
                'vm':'Tuning and management of memory, buffers, and cache '}

class comparehosts(object):
    def __init__(self,host1=None,host2=None) -> None:
        super().__init__()
        self.host1 = str(host1)
        self.host2 = str(host2)
        self.host1data = {'sysctl':{},'SDqueue':{},'ZFS':{},'MDraid':{},'OS_Facts':{}}
        self.host2data = {'sysctl':{},'SDqueue':{},'ZFS':{},'MDraid':{},'OS_Facts':{}}
        self.diffs = {'sysctl':{},'SDqueue':{},'ZFS':{},'MDraid':{},'OS_Facts':{}}
        self.getOSfacts()
        self.getHostSysctl()
        self.getHostSDqueue()
        self.getMDparams()
        self.getZFSparams()
        self.diffHosts()

    
    def getOSfacts(self):
        try:
            host1OSversion = ssh_run_remote_command('uname -a',self.host1,'root').split()[2]
            self.host1data['OS_Facts']['os_version'] = host1OSversion
            host2OSversion = ssh_run_remote_command('uname -a',self.host2,'root').split()[2]
            self.host2data['OS_Facts']['os_version'] = host2OSversion
        except Exception as e:
            print(e)
            exit(1)

    def getHostSysctl(self):
        #For some reason sysctl -a will not run properly when using normal non command line ssh remote execution with paramiko so we use external ssh program here.
        try:
            host1result = ssh_external_run_remote_command('sysctl -a',self.host1,'root')['stdout'].splitlines()
            host2result = ssh_external_run_remote_command('sysctl -a',self.host2,'root')['stdout'].splitlines()
        except Exception as e:
            print(e)
            exit(1)
        for line in host1result:
            parts = line.split('=')
            self.host1data['sysctl'][parts[0].strip()] =  parts[1].strip()
        for line in host2result:
            parts = line.split('=')
            self.host2data['sysctl'][parts[0].strip()] =  parts[1].strip()
        self.host1data['sysctl']

    def getHostSDqueue(self):
        #Host one data gather
        results = ssh_get_remote_dirlist(self.host1,'/sys/block')
        # print(results,type(results))
        results = [item for item in results if 'sd' in item]
        omits = ['sda','sdb','sdc','sdd','sde','sdf']
        results = list(set(results) - set(omits))
        target = random.choice(results)
        queueparams = {}
        for item in ssh_get_remote_dirlist(self.host1,'/sys/block/'+str(target)+'/queue'):
            try:
              contents = ssh_get_remote_file_contents(self.host1,'/sys/block/'+str(target)+'/queue/'+item).decode().strip()
            #   print(item,contents)
              queueparams[item] = str(contents)
            except Exception as e:
                pass
                # print(item)
                # print(e)
        self.host1data['SDqueue'] = queueparams

        #Host 2 data gather.
        results = ssh_get_remote_dirlist(self.host2,'/sys/block')
        # print(results,type(results))
        results = [item for item in results if 'sd' in item]
        omits = ['sda','sdb','sdc','sdd','sde','sdf']
        results = list(set(results) - set(omits))
        target = random.choice(results)
        queueparams = {}
        for item in ssh_get_remote_dirlist(self.host2,'/sys/block/'+str(target)+'/queue'):
            try:
              contents = ssh_get_remote_file_contents(self.host2,'/sys/block/'+str(target)+'/queue/'+item).decode().strip()
            #   print(item,contents)
              queueparams[item] = str(contents)
            except Exception as e:
                pass
                # print(item)
                # print(e)
        self.host2data['SDqueue'] = queueparams

    def getMDparams(self):
        mdparams = {}
        #Get host1 mdraid data
        results = ssh_get_remote_dirlist(self.host1,'/sys/block')
        if not (type(results) == int or len(results) == 0):
            # print(results,type(results))
            results = [item for item in results if str(item).startswith('md')]
            if len(results) == 0:
                return
            target = random.choice(results)
            for item in ssh_get_remote_dirlist(self.host1,'/sys/block/'+str(target)+'/md'):
                try:
                    contents = ssh_get_remote_file_contents(self.host1,'/sys/block/'+str(target)+'/md/'+item).decode().strip()
                    # print(item,contents)
                    mdparams[item] = str(contents)
                except Exception as e:
                    pass
                    # print(item)
                    # print(e)
        mdversion = ssh_external_run_remote_command('mdadm --version',self.host1,'root')['stderr'].strip()
        mdparams['md_version'] = mdversion
        self.host1data['MDraid'] = mdparams

        #Get host2 mdraid data
        mdparams = {}
        results = ssh_get_remote_dirlist(self.host2,'/sys/block')
        if not (type(results) == int or len(results) == 0):
            results = [item for item in results if str(item).startswith('md')]
            target = random.choice(results)
            for item in ssh_get_remote_dirlist(self.host2,'/sys/block/'+str(target)+'/md'):
                try:
                    contents = ssh_get_remote_file_contents(self.host2,'/sys/block/'+str(target)+'/md/'+item).decode().strip()
                    mdparams[item] = str(contents)
                except Exception as e:
                    pass
        mdversion = ssh_external_run_remote_command('mdadm --version',self.host2,'root')['stderr'].strip()
        mdparams['md_version'] = mdversion
        self.host2data['MDraid'] = mdparams
    
    def getZFSparams(self):
        zfsparams = {}
        results = ssh_get_remote_dirlist(self.host1,'/sys/module/zfs/parameters')
        if not (type(results) == int or len(results) == 0):
            for item in results:
                try:
                    contents = ssh_get_remote_file_contents(self.host1,'/sys/module/zfs/parameters/'+item).decode().strip()
                    # print(item,contents)
                    zfsparams[item] = str(contents)
                except Exception as e:
                    print(e)
                    pass
                    # print(item)
                    # print(e)
        try:
            zfsversions = ssh_run_remote_command('zfs --version',self.host1,username='root')
            zfsparams['zfs_versions'] = zfsversions.replace('\n',' ')
            zfsparams['zfs_list'] = ssh_run_remote_command('zfs list',self.host1,'root').splitlines()
        except Exception as e:
            print(e)
            pass
        self.host1data['ZFS'] = zfsparams

        zfsparams = {}
        results = ssh_get_remote_dirlist(self.host2,'/sys/module/zfs/parameters')
        if not (type(results) == int or len(results) == 0):
            for item in results:
                try:
                    contents = ssh_get_remote_file_contents(self.host2,'/sys/module/zfs/parameters/'+item).decode().strip()
                    zfsparams[item] = str(contents)
                except Exception as e:
                    pass
        try:
            zfsversions = ssh_run_remote_command('zfs --version',self.host2,username='root')
            zfsparams['zfs_versions'] = zfsversions.replace('\n',' ')
            zfsparams['zfs_list'] = ssh_run_remote_command('zfs list',self.host2,'root').splitlines()
        except Exception:
            pass
        self.host2data['ZFS'] = zfsparams

    def diffHosts(self):
        for paramset in self.host1data:
            for item in self.host1data[paramset]:
                if item in self.host2data[paramset] and self.host1data[paramset][item] != self.host2data[paramset][item]:
                    self.diffs[paramset][item] = {self.host1:self.host1data[paramset][item],self.host2:self.host2data[paramset][item]}
        
        