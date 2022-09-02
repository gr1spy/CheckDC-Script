import subprocess
import re
import os
import logging
import logging.handlers

cmd = 'nltest /dclist:omega.sbrf.ru & nltest /dclist:ca.sbrf.ru'
regex = [r'[a-zA-Z0-9\-\.]+\.sbrf\.ru']
path_to_script_dir = r'D:/dc_check_script/'
old_num = ['']
new_num = ['']

# Адрес:порт для отправки Syslog
SYSLOG_ADDRESS = '10.119.248.99'
SYSLOG_PORT = 514


# last_query.txt - Предыдущая выгрузка DC, с которой сравниваем текущую
# new_dc.txt - список новых DC
# removed_dc.txt - список выведенных DC

# Получаем новый список домен контролеров в домене
def get_dc():
    result = []
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    with open('%spre_query.txt' % path_to_script_dir, 'w', errors='ignore') as output:
        output.write(proc.stdout.decode('cp850'))

    with open('%spre_query.txt' % path_to_script_dir, 'r') as output, open('%squery.txt' % path_to_script_dir,
                                                                           'w') as output2:
        for line in output.readlines():
            for reg in regex:
                if re.findall(reg, line):
                    result += re.findall(reg, line)

        result_new = list(set(result))
        for dc in result_new:
            output2.write('%s\n' % dc)


def check_new_dc():
    files = open_files()
    with open('%snew_dc.txt' % path_to_script_dir, 'w') as output:
        for num in files[1]:
            if num not in files[0]:
                output.write('%s\n' % num)

    if not (os.stat('%snew_dc.txt' % path_to_script_dir).st_size == 0):
        with open('%snew_dc.txt' % path_to_script_dir, 'r') as f:
            new_dc_to_syslog = [line.strip() for line in f]
        send_syslog(' CheckDCScript These domain controllers have been added: %s' % new_dc_to_syslog)


def check_old_dc():
    files = open_files()
    with open('%sremoved_dc.txt' % path_to_script_dir, 'w') as output:
        for num in files[0]:
            if num not in files[1]:
                output.write('%s}\n' % num)

    if not (os.stat('%sremoved_dc.txt' % path_to_script_dir).st_size == 0):
        with open('%sremoved_dc.txt' % path_to_script_dir, 'r') as f:
            removed_dc_to_syslog = [line.strip() for line in f]
        send_syslog(' CheckDCScript These domain controllers have been removed: 5s' % removed_dc_to_syslog)


def open_files():
    global old_num, new_num
    if os.path.isfile('%slast_query.txt' % path_to_script_dir):
        with open('%slast_query.txt' % path_to_script_dir, 'r') as f:
            old_number = [line.strip() for line in f]
    else:
        open('%slast_query.txt' % path_to_script_dir, 'w').close()
        with open('%slast_query.txt' % path_to_script_dir, 'r') as f:
            old_number = [line.strip() for line in f]

    if os.path.isfile('%squery.txt' % path_to_script_dir):
        with open('%squery.txt' % path_to_script_dir, 'r') as f:
            new_number = [line.strip() for line in f]
    else:
        open('%squery.txt' % path_to_script_dir, 'w').close()
        with open('%squery.txt' % path_to_script_dir, 'r') as f:
            new_number = [line.strip() for line in f]

    return [old_number, new_number]


def send_syslog(dc_list):
    log = logging.getLogger('dc')
    log.setLevel(logging.NOTSET)
    formatter = logging.Formatter(fmt='%(asctime)-4s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    syslog = logging.handlers.SysLogHandler(address=(SYSLOG_ADDRESS, SYSLOG_PORT))
    syslog.setLevel(logging.NOTSET)
    syslog.setFormatter(formatter)

    log.addHandler(syslog)
    log.error(dc_list)


def rename_files():
    os.remove('%slast_query.txt' % path_to_script_dir)
    os.remove('%spre_query.txt' % path_to_script_dir)
    os.renames('%squery.txt' % path_to_script_dir, '%slast_query.txt' % path_to_script_dir)


def main():
    get_dc()
    check_new_dc()
    check_old_dc()
    rename_files()


if __name__ == '__main__':
    main()
