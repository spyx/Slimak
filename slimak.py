from getpass import getpass
from netmiko import ConnectHandler, file_transfer
import sys, os
import argparse

from netmiko.scp_functions import progress_bar

parser = argparse.ArgumentParser()
parser.add_argument(dest="ip", help="IP address of device")
parser.add_argument(dest="source_file", help="file name to upload")
parser.add_argument(dest="timeout", help="Set temporary exec-timeout to 60  min", default="0")

args = parser.parse_args()

source_file = args.source_file
if not(os.path.isfile(source_file)):
    print ("Image file doesnt exist")
    sys.exit(1)

direction = 'put'
username = input("Enter username: ")
password=getpass()
net_device = {
    'device_type': 'cisco_ios',
    'host': args.ip,
    'username': username,
    'password': password
}


ssh_conn = ConnectHandler(**net_device)
print("\nTransfering file")
try:
    ssh_conn.send_config_set(["ip scp server enable","line vty 0 4","exec-timeout 60 0"])
    transfer_dict = file_transfer(ssh_conn, source_file=source_file, dest_file=source_file, file_system="flash:", direction=direction,overwrite_file=True, progress=progress_bar)
    if args.timeout == "0":
        ssh_conn.send_config_set(["no ip scp server enable","line vty 0 4","no exec-timeout 60 0"]) 
    else:
        ssh_conn.send_config_set(["no ip scp server enable","line vty 0 4","exec-timeout "+args.timeout+" 0"])
except e as err:
    print(err)
    sys.exit(1)
print("Transfered!\n")

for res in transfer_dict:
    if ((not transfer_dict[res]) and res == 'file_exists' ):
        print("! File doesn't exist on flash")
    elif ( transfer_dict[res] and res == 'file_exists' ):
        print("File exist on flash")   
    elif ((not transfer_dict[res]) and res == 'file_verified' ):
        print("! MD5 checksum failled")
    elif ( transfer_dict[res] and res == 'file_verified' ):
        print("MD5 checksum passed")
    elif ((not transfer_dict[res]) and res == 'file_transferred' ):
        print("! File did not get transfered")
    elif ( transfer_dict[res] and res == 'file_transferred' ):
        print("File transfered")

setConfig = input("Configure config file for you? = [yes] ")
if (setConfig == 'yes'):
    print("Replace system boot with file "+source_file)
    ssh_conn.send_config_set(["no boot system","boot system flash:"+source_file, 'do wr'])
    print("Done")
else:
    print("Did not set up system boot config")
    

reload = input("Reload switch now?")
if (reload == "yes"):
    print("\nReloading switch now...")
    # As connection get immediatelly terminated try to catch that condition
    try:
        ssh_conn.send_command("reload", expect_string="[confirm]")
        ssh_conn.send_command("\n")
    except:
        print ("Switch reloaded")
    
else:
    print("Please reload switch in your earlieast convenience :) ")

ssh_conn.disconnect()