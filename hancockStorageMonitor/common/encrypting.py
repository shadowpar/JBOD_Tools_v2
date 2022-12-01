from platform import node
from pathlib import Path
from paramiko import RSAKey

sshKeyPath = Path('/root').joinpath('.ssh').joinpath('id_rsa')
codyPath = Path('/root').joinpath('.ssh').joinpath('.cody')

def createEncodedPassword():
    flag = False
    hostname = node()+node()+node()+node()
    secret = 'terriblePassword'
    while not flag:
        secret = input("Please type the password for SSH key.\n")
        secret2 = input("Please retype the password.\n")
        if secret != secret2:
            print("The passwords do not match. Please try again")
        else:
            secretLenth = len(secret)
            hostLength = len(hostname)
            if secretLenth > hostLength:
                print("Please choose a password less than", hostLength, "characters long.")
            else:
                flag = True
    secretLi = [item for item in secret.encode()]
    hostLi = [item for item in hostname.encode()]
    combined = []
    for secretByte in secretLi:
        combinedByte = secretByte+hostLi.pop()
        combined.append(combinedByte)
    output = ''
    for intNum in combined:
        output = output + bin(intNum)
    codyPath.write_text(output)

def getRSAkey():
    hostname = node()+node()+node()+node()
    if codyPath.is_file():
        bitInput = codyPath.read_text().split('0b')
        bitInput.remove('')
        intInput = [int(item,2) for item in bitInput]
        hostnameBli = [item for item in hostname.encode()]
        origInts = []
        for mybyte in intInput:
            origInt = mybyte - hostnameBli.pop()
            origInts.append(origInt)
        pkey = RSAKey(filename=sshKeyPath.as_posix(),password=bytes(origInts).decode())
        return pkey
    else:
        print("you need to run teh createEncodedPassword function first.")
        return None
