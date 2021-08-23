#!/usr/bin/python3

# Imports
import sys
import os
import datetime
import subprocess
from time import sleep
import logging

# Config
backups_path = '/srv/backups/linux'

# Logger
logging.basicConfig(filename='/var/log/backup.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Arguments array
args = [arg for arg in sys.argv[1:]]

# If unknown argument
for arg in args:
    if not arg in ['-help', '-db', '-srv', '-full']:
        print(f'Unknown argument: {arg}')
        exit()

# If zero arguments or requested help
if len(args) <= 0 or '-help' in args:
    print('Use: backup [-db|-srv|-full]')
    exit()

# Date
def date():
    return datetime.datetime.now().strftime('%Y.%m.%d-%H.%M')

# Copy dirs and files
def copyanything(src, dst, exclude=None):
    if exclude is None:
        logging.debug(f'Copying {src} to {dst} ...')
        subprocess.call(['rsync', '-aAXv', src, dst])
    else:
        logging.debug(f'Copying {src} to {dst} without {exclude} ...')
        subprocess.call(['rsync', '-aAXv', src, dst, '--exclude', f'{exclude}'])

# Compress with 7zip
def compress7z(src, dst):
    logging.debug(f'7z {src} to {dst} ...')
    subprocess.call(['7z', 'a', dst, src])

# Remove file
def remove(f):
    if '/srv/backups/linux' in f:
        logging.debug(f'Removing {f} ...')
        subprocess.call(['rm', '-r', f])

# Create folder
def mkdir(f):
    logging.debug(f'Making directory {f} ...')
    subprocess.call(['mkdir', f])

#------------------------
#-------- Backups -------
#------------------------
logging.debug('---------- START BACKUP ----------')

if '-db' in args:
    folder = f'{backups_path}/db/db-{date()}'
    mkdir(folder)

    logging.debug(f'Downloading databases ...')
    databases = os.popen('mysql --login-path=backup -e "SHOW DATABASES;" | grep -Ev "(Database|information_schema|performance_schema)"').read().split()

    for db in databases:
        os.popen(f'mysqldump --login-path=backup --force --opt --databases {db} > {folder}/{db}.sql')

    sleep(12)
    compress7z(folder, f'{folder}.7z')
    remove(folder)

if '-srv' in args:
    folder = f'{backups_path}/srv/srv-{date()}'
    mkdir(folder)

    copyanything('/srv', f'{folder}/.')

    sleep(5)
    compress7z(folder, f'{folder}.7z')
    remove(folder)

if '-full' in args:
    folder = f'{backups_path}/full/full-{date()}'
    mkdir(folder)

    copyanything('/bin', f'{folder}/.')
    copyanything('/etc', f'{folder}/.')
    copyanything('/opt', f'{folder}/.')
    copyanything('/boot', f'{folder}/.')
    copyanything('/home', f'{folder}/.')
    copyanything('/lib', f'{folder}/.')
    copyanything('/sbin', f'{folder}/.')
    copyanything('/usr', f'{folder}/.')
    copyanything('/lib64', f'{folder}/.')
    copyanything('/root', f'{folder}/.')
    copyanything('/var', f'{folder}/.')

    sleep(5)
    compress7z(folder, f'{folder}.7z')
    remove(folder)

logging.debug(f'chmod 755 -R /srv/backups/linux ...')
subprocess.call(['chmod', '755', '-R', '/srv/backups/linux'])
logging.debug('---------- END BACKUP ----------')
