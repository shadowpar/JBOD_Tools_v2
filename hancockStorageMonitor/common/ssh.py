import paramiko
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand
from hancockStorageMonitor.common.encrypting import getRSAkey

pkey = getRSAkey()

def ssh_run_remote_command(cmd, hostname, username):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=hostname ,username=username ,pkey=pkey)
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    out = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if error:
        raise Exception('There was an error pulling the runtime: {}'.format(error))
    ssh_client.close()

    return out

def ssh_get_remote_file(remoteHost, remoteFileName, localFileName, username='root' ,sshport=22):
    ssh_client = paramiko.SSHClient()
    try:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=remoteHost ,username=username ,port=sshport ,pkey=pkey,compress=True)
    except Exception:
        returnCode = 1
        ssh_client.close()
        return returnCode
    try:
        trans = ssh_client.get_transport()
        sftp = paramiko.SFTPClient.from_transport(trans)
        sftp.get(remotepath=remoteFileName ,localpath=localFileName)
        sftp.close()
        return 0
    except Exception:
        returnCode = 2
        ssh_client.close()
        return returnCode

def ssh_get_remote_file_contents(remoteHost, remoteFileName, username='root' ,sshport=22):
    ssh_client = paramiko.SSHClient()
    try:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=remoteHost ,username=username ,port=sshport ,pkey=pkey,compress=True)
    except Exception:
        returnCode = 1
        ssh_client.close()
        return returnCode
    try:
        trans = ssh_client.get_transport()
        sftp = paramiko.SFTPClient.from_transport(trans)
        data = sftp.open(filename=remoteFileName,mode="r").read()
        sftp.close()
        return data
    except Exception:
        returnCode = 2
        ssh_client.close()
        return returnCode

def ssh_get_remote_dirlist(remoteHost,remoteDir,username='root',sshport=22,startpattern=None):
    ssh_client = paramiko.SSHClient()
    try:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=remoteHost ,username=username ,port=sshport ,pkey=pkey,compress=True)
    except Exception as e:
        print(e)
        returnCode = 1
        ssh_client.close()
        return returnCode

    try:
        trans = ssh_client.get_transport()
        sftp = paramiko.SFTPClient.from_transport(trans)
        data = sftp.listdir(path=remoteDir)
        sftp.close()
        if startpattern is None:
            return data
        else:
            data = [item for item in data if str(item).startswith(startpattern)]
            return data
    except Exception as e:
        print(e)
        returnCode = 2
        ssh_client.close()
        return returnCode

def ssh_external_run_remote_command(cmd, hostname, username):
    if type(cmd) == str:
        cmd = cmd.split()
    baseCmd = ['ssh',str(username)+'@'+str(hostname),'"']
    baseCmd.append(cmd)
    baseCmd.append('"')
    results = errorHandledRunCommand(command=cmd,timeout=10,autoretry=False)
    if results['returncode'] != 0:
        print("There was a problem running command",baseCmd)
        print(results['stderr'])
        print(results['stdout'])
        return None
    else:
        return results
    