import requests
import time
import sys
from datetime import datetime
import subprocess


count:dict={'timeout':0,'connection':0,'unknown':0}
def my_check() -> str:
    global count
    try:
        url1 = "http://dnet.mb.qq.com/rsp204"
        # url1 = 'https://github.com'
        response1 = requests.get(url1,timeout=30)
        if response1.status_code == 204:
            return 'True'
        else:
            # return '非204'
            return 'timeout'
    except requests.exceptions.Timeout:
        count['timeout']+=1
        return 'timeout'
    except requests.exceptions.ConnectionError:
        count['connection']+=1
        return 'connection'
    except Exception as e:
        count['unknown']+=1
        return type(e)
    
def get_format_time() -> str:
    # 获取当前时间
    current_time = datetime.now()
    # 将时间格式化为字符串
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    # print(formatted_time)
    return '['+formatted_time+']'

def restart_wifi():
    print(get_format_time()+'开始重启wifi')
    command='sudo nmcli radio wifi off'
    shell_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    time.sleep(30)
    command='sudo nmcli radio wifi on'
    shell_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(get_format_time()+'重启wifi结束')

def reboot():
    print(get_format_time()+'开始重启电脑')
    command='reboot'
    shell_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    exit(get_format_time()+'重启电脑，退出程序')

def main():
    global count
    result=my_check()
    if result=='True':
        print(get_format_time()+'连接成功')
        return True
    elif result=='timeout':
        print(get_format_time()+'连接超时：'+str(count['timeout']))
        if count['timeout']%5==0:
            print(get_format_time()+'请稍等')
            time.sleep(180)
        elif count['timeout']%3==0:
            restart_wifi()
        elif count['timeout']==16:
            print(get_format_time()+'重启失败次数过多，开始重启电脑')
            reboot()
    elif result=='connection':
        print(get_format_time()+'连接建立错误')
        if count['connection']%5==0:
            restart_wifi()
        elif count['connection']==16:
            print(get_format_time()+'重启失败次数过多，开始重启电脑')
            reboot()
    else:
        print(get_format_time()+'未知错误'+result)
        if count['unknown']%5==0:
            restart_wifi()
        elif count['unknown']==16:
            print(get_format_time()+'重启失败次数过多，开始重启电脑')
            reboot()
    return False


if __name__=='__main__':
    result=main()
    while not result:
        time.sleep(15)
        result=main()