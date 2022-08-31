import subprocess
import re
import os
import logging
import logging.handlers

cmd = r'nltest /dclist:'

# Домены, список которых проверяем
sigma_domain = r'sigma.sbrf.ru'
cib_domain = r'msk.trd.ru'
delta_domain = r'delta.sbrf.ru'

# Регулярки для доменов
regex_sigma = r'[a-zA-Z0-9\-]+\.sigma\.sbrf\.ru'
regex_cib = r'[a-zA-Z0-9\-]+\.msk\.trd\.ru'
regex_delta = r'[a-zA-Z0-9\-]+\.delta\.sbrf\.ru'

# Адрес:порт для отправки Syslog
SYSLOG_ADDRESS = '10.34.248.96'
SYSLOG_PORT = 514


# Получаем новый список домен контролеров в домене
def get_dc():
    proc = subprocess.Popen(f'{cmd}{sigma_domain}', stdout=subprocess.PIPE, encoding='cp866')
    with open('new_query.txt', 'w+') as output:
        for line in proc.stdout:
            if re.findall(regex_sigma, line):
                result = re.findall(regex_sigma, line)
                output.write(f'{result[0]}\n')

    with open('new_query.txt', 'r') as source, open('query.txt', 'w') as dest:
        dest.writelines(source.readlines()[1:])


def check_new_dc():
    files = open_files()
    with open('new_dc_list.txt', 'w+') as output:
        for num in files[1]:
            if num not in files[0]:
                output.write(f'{num}\n')

    if not (os.stat('new_dc_list.txt').st_size == 0):
        with open('new_dc_list.txt', 'r') as f:
            new_dc_to_syslog = [line.strip() for line in f]
        send_syslog(f'These domain controllers have been added: {new_dc_to_syslog}')


def check_old_dc():
    files = open_files()
    with open('removed_dc.txt', 'w+') as output:
        for num in files[0]:
            if num not in files[1]:
                output.write(f'{num}\n')

    if not (os.stat('removed_dc.txt').st_size == 0):
        with open('removed_dc.txt', 'r') as f:
            removed_dc_to_syslog = [line.strip() for line in f]
        send_syslog(f'These domain controllers have been removed: {removed_dc_to_syslog}')


def open_files():
    if os.path.isfile('last_query.txt'):
        with open('last_query.txt', 'r') as f:
            old_number = [line.strip() for line in f]
    else:
        open('last_query.txt', 'w').close()

    if os.path.isfile('query.txt'):
        with open('query.txt', 'r') as f:
            new_number = [line.strip() for line in f]

    return [old_number, new_number]


def send_syslog(dc_list):
    log = logging.getLogger('dc')
    log.setLevel(logging.NOTSET)

    syslog = logging.handlers.SysLogHandler(address=(SYSLOG_ADDRESS, SYSLOG_PORT))
    syslog.setLevel(logging.NOTSET)

    log.addHandler(syslog)
    log.error(dc_list)


def rename_files():
    os.remove('last_query.txt')
    os.remove('new_query.txt')
    os.renames('query.txt', 'last_query.txt')


def main():
    get_dc()
    check_new_dc()
    check_old_dc()
    rename_files()


if __name__ == '__main__':
    main()
