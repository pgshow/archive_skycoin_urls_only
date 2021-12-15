import threading
import time

import requests
import random
import re

from retry import retry


class Agent:
    """代理池类"""
    def __init__(self, lock):
        self.api = 'http://list.rola.info:8088/user_get_ip_list?token=&type=4g&qty=1&country=&time=1&format=json&protocol=http&filter=1'
        self.ips = []
        self.lock = lock
        self.i = 0  # 给同一时间随机数增加变化

    @retry(tries=5, delay=5, backoff=2)
    def requests_api(self):
        try:
            r = requests.get(self.api, timeout=30)
            tmp = r.json()

            if tmp['code'] != '成功':
                print(tmp['msg'])

            for item in tmp['data']:
                try:
                    tmp = re.search(r'(\d+.\d+.\d+.\d+):(\d+)', item)
                    self.ips.append({'ip': tmp.group(1), 'port': tmp.group(2), 'rest': 7})

                except:
                    pass

            print('-----Request new proxy success')
        except:
            print('-----Request new proxy failed')

    def get_one(self):
        """随机获取一个代理"""
        self.lock.acquire()

        self.clear(self.ips)  # 清理代理

        # 代理用尽后重新获取
        if len(self.ips) <= 0:
            self.requests_api()

        # 获取
        time_seed = "%.20f" % time.time()
        time_seed = int(time_seed[-15:])
        random.seed(time_seed)

        lid = random.randint(0, len(self.ips) - 1)
        agent = self.ips[lid]

        # if not self.check(agent):
        #     print('代理 {}:{} 不可用'.format(agent['ip'], agent['port']))
        #     agent['rest'] = 0
        #     return

        agent['rest'] -= 1

        self.lock.release()

        # print('代理 {}:{} 有效，剩余次数 {}'.format(agent['ip'], agent['port'], agent['rest']))
        return agent

    def clear(self, ips):
        # 清理用了几次的代理
        for item in self.ips:
            if item['rest'] <= 0:
                self.ips.remove(item)
                return self.clear(self.ips)

    def check(self, agent):
        """检查可用性"""
        # proxies = {
        #     'https': '{}:{}'.format(agent['ip'], agent['port']),
        # }
        # session = requests.session()
        # session.proxies = proxies
        try:
            r = requests.get('https://api.ipify.org/?format=json', timeout=15, proxies={'https': f'{agent["ip"]}:{agent["port"]}'})
            if agent['ip'] in r.text:
                return True
        except Exception as e:
            print(e)
            return


# if __name__ == '__main__':
#     proxy_lock = threading.Lock()
#     a = Agent(proxy_lock)
#
#     while 1:
#         ip = a.get_one()
#         print(a.ips)
#         print(ip)
