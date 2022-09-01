import subprocess
import re
import os
import logging
import logging.handlers

cmd = 'nltest /dclist:sigma.sbrf.ru & nltest /dclist:msk.trd.ru & nltest /dclist:delta.sbrf.ru'
regex = [r'[a-zA-Z0-9\-]+\.sigma\.sbrf\.ru', r'[a-zA-Z0-9\-]+\.msk\.trd\.ru', r'[a-zA-Z0-9\-]+\.delta\.sbrf\.ru']
path_to_script_dir = r'D:/dc_check_script/'
old_num = ['']
new_num = ['']

# Адрес:порт для отправки Syslog
SYSLOG_ADDRESS = '10.34.248.96'
SYSLOG_PORT = 514

# last_query.txt - Предыдущая выгрузка DC, с которой сравниваем текущую
# new_dc.txt - список новых DC
# removed_dc.txt - список выведенных DC

# Получаем новый список домен контролеров в домене
def get_dc():
    result = []
    proc = subprocess.run(f'{cmd}', stdout=subprocess.PIPE, shell=True, encoding='utf-8')
    with open(f'{path_to_script_dir}pre_query.txt', 'w') as output:
        output.write(proc.stdout)

    with open(f'{path_to_script_dir}pre_query.txt', 'r') as output, open(f'{path_to_script_dir}query.txt', 'w') as output2:
        for line in output.readlines():
            for reg in regex:
                if re.findall(reg, line):
                    result += re.findall(reg, line)

        result_new = list(set(result))
        for dc in result_new:
            output2.write(f'{dc}\n')


def check_new_dc():
    files = open_files()
    with open(f'{path_to_script_dir}new_dc.txt', 'w') as output:
        for num in files[1]:
            if num not in files[0]:
                output.write(f'{num}\n')

    if not (os.stat(f'{path_to_script_dir}new_dc.txt').st_size == 0):
        with open(f'{path_to_script_dir}new_dc.txt', 'r') as f:
            new_dc_to_syslog = [line.strip() for line in f]
        send_syslog(f'These domain controllers have been added: {new_dc_to_syslog}')


def check_old_dc():
    files = open_files()
    with open(f'{path_to_script_dir}removed_dc.txt', 'w') as output:
        for num in files[0]:
            if num not in files[1]:
                output.write(f'{num}\n')

    if not (os.stat(f'{path_to_script_dir}removed_dc.txt').st_size == 0):
        with open(f'{path_to_script_dir}removed_dc.txt', 'r') as f:
            removed_dc_to_syslog = [line.strip() for line in f]
        send_syslog(f'These domain controllers have been removed: {removed_dc_to_syslog}')


def open_files():
    global old_num, new_num
    if os.path.isfile(f'{path_to_script_dir}last_query.txt'):
        with open(f'{path_to_script_dir}last_query.txt', 'r') as f:
            old_number = [line.strip() for line in f]
    else:
        open(f'{path_to_script_dir}last_query.txt', 'w').close()
        with open(f'{path_to_script_dir}last_query.txt', 'r') as f:
            old_number = [line.strip() for line in f]

    if os.path.isfile(f'{path_to_script_dir}query.txt'):
        with open(f'{path_to_script_dir}query.txt', 'r') as f:
            new_number = [line.strip() for line in f]
    else:
        open(f'{path_to_script_dir}query.txt', 'w').close()
        with open(f'{path_to_script_dir}query.txt', 'r') as f:
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
    os.remove(f'{path_to_script_dir}last_query.txt')
    os.remove(f'{path_to_script_dir}pre_query.txt')
    os.renames(f'{path_to_script_dir}query.txt', f'{path_to_script_dir}last_query.txt')


def main():
    get_dc()
    check_new_dc()
    check_old_dc()
    rename_files()


if __name__ == '__main__':
    main()
