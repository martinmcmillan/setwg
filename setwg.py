#!/usr/bin/python

from os.path import exists
import subprocess
import sys
import argparse
import json


def setupConf():
    stdOut = subprocess.getoutput(
        'tar --exclude=\'*tar\' -cvf /etc/wireguard/wireguardConfs_$(date +%s).tar /etc/wireguard')
    print(stdOut)
    with open('/etc/wireguard/servers.txt', 'r') as f:
        for l in range(4):
            f.readline()
        try:
            while True:
                location = next(f)
                server = next(f)
                ip = next(f)
                publicKey = next(f)
                server = server.split('.')[0]
                print(server)
                print(publicKey)
                writeConf(server, publicKey)
        except StopIteration:
            print('EOF!')

    sys.exit('exiting setupConf')


def writeConf(server, publicKey):
    if (exists(f'/etc/wireguard/{server}.conf')):
        stdOut = subprocess.getoutput(f'rm -rf /etc/wireguard/{server}.conf')
        print(stdOut)

    with open(f'/etc/wireguard/{server}.conf', 'w') as f:
        f.write(
            f'[Interface]\nPrivateKey = ABfAIl9vkcvlJvmZEbrg0SY99NTX4dT+qPR+A7ec/Xw=\nAddress = 172.25.251.250/32\nDNS = 172.16.0.1\n\n[Peer]\nPublicKey = {publicKey}Endpoint = {server}.wg.ivpn.net:58237\nAllowedIPs = 0.0.0.0/0')

    stdOut = subprocess.getoutput(f'chmod 700 /etc/wireguard/{server}.conf')
    print(stdOut)


def setDefault(default):
    _, defServer = getStatus()
    if defServer:
        stdOut = subprocess.getoutput('rm -rf /etc/wireguard/wg-default.conf')
        print(stdOut)
    stdOut = subprocess.getoutput(
        f'ln -s /etc/wireguard/{default}.conf /etc/wireguard/wg-default.conf')
    print(stdOut)
    getStatus()

    sys.exit('exiting setDefault')


def useServer(server):
    service, _ = getStatus()
    if service:
        stopService(server, service)
    if server == 'wg':
        server = 'wg-default'
    stdOut = subprocess.getoutput(f'systemctl start wg-quick@{server}')
    print(stdOut)
    getStatus()

    sys.exit('exiting useServer')


def stopService(server, service):
    if service:
        stdOut = subprocess.getoutput(f'systemctl stop {service}')
        print(stdOut)
    getStatus()
    if server == 'stop':
        sys.exit('exiting stopService')


def getStatus():
    ip = city = asn_org = None
    stdOut = subprocess.getoutput('curl -s ifconfig.co/json')
    if stdOut:
        print(f'Current internet connection:\n{stdOut}\n')
        outDict = json.loads(stdOut)
        ip = outDict['ip']
        city = outDict['city']
        asn_org = outDict['asn_org']
    else:
        print(f'\nNO INTERNET CONNECTION\n')

    stdOut = subprocess.getoutput(
        'systemctl list-units --type=service | grep wg-quick')
    if stdOut:
        print(f'{stdOut}\n')
        service = stdOut.split()[0]

        service = service.split('.')[0]
        server = service.split('@')[1]
        print(f'Wireguard service: {service}')
        print(f'Server: {server}')
    else:
        service = ''
        print('No Wireguard services active')

    stdOut = subprocess.getoutput(
        'ls -l /etc/wireguard/ | grep ^l | grep wg-default')
    if stdOut:
        link = ' '.join(stdOut.split()[8:])
        defServer = stdOut.split()[10]
        defServer = defServer.split('.')[0]
        defServer = defServer.split('/')[-1]
        print(f'Default Link: {link}')
        print(f'Default server: {defServer}\n')
    else:
        defServer = ''
        print('No default server\n')

    print(f'ip: {ip} | city: {city} | asn_org: {asn_org}\n')

    return service, defServer


parser = argparse.ArgumentParser()
parser.add_argument('server', nargs='?', type=str, default='',
                    help='Usage: setwg us-ny1')
parser.add_argument('-d', '--default', nargs=1, type=str,
                    default='', help='Usage: setwg --default us-ny1')
parser.add_argument('--setup', nargs=1, type=bool, default=False,
                    help='Usage: setwg --setup True')
parser.add_argument('-s', '--stop', nargs=1, type=bool,
                    default=False, help='Usage: setwg --stop True')

args = parser.parse_args()
# print(args)

if args.server:
    useServer(args.server)
elif args.default:
    setDefault(args.default[0])
elif (args.setup):
    setupConf()
elif args.stop:
    server = 'stop'
    service, _ = getStatus()
    stopService(server, service)
else:
    getStatus()

sys.exit('exiting setwg')


'''
cd /etc/systemd/system/multi-user.target.wants/
ln -s /lib/systemd/system/wg-quick@.service wg-quick@wg-default.service
cd /etc/wireguard/
ln -s us-ny1.conf wg-default.conf
curl ifconfig.co/json
'''
