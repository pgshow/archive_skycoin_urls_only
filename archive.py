import os
import re
import time
from urllib.parse import urljoin

import download
import function
import replace

import requests
import simplejson
from retry import retry
from loguru import logger
from urllib.parse import urlparse
from bs4 import BeautifulSoup, element, NavigableString


class Archive:
    def __init__(self, domain):
        self.domain = domain

    def import_urls(self, urls_file):
        """
        extract all the urls which on archive for this domain
        >1.Download the txt file from the list page
        https://web.archive.org/web/timemap/?url=http://blackhatworld.com/&matchType=prefix&collapse=urlkey&output=txt&fl=original&filter=!statuscode:[45]..&filter=mimetype:text/html&_=None
        >2.keep the list file with Python main.py
        """
        with open(urls_file, 'r') as f:
            tmp_urls = f.readlines()

        urls = []
        for u in tmp_urls:
            urls.append(u.replace('\n', ''))

        return urls

    def get_all_urls(self):
        """extract all the urls which on archive for this domain"""
        url = f'https://web.archive.org/web/timemap/?url=http://{self.domain}/&matchType=prefix&collapse=urlkey&output=txt&fl=original&filter=!statuscode:[45]..&filter=mimetype:text/html&_=None'
        r = self.fetch(url)

        if r.status_code == 302:
            logger.error('Bot Detector Active')
            exit()

        if r.status_code != 200:
            logger.error(F"status {r.status_code}")
            exit()

        if not r.text:
            logger.error("Fetch list page failed")
            exit()

        try:
            urls = r.text.split('\n')
        except Exception as e:
            logger.error("Convert data of list page failed", e)
            exit()

        return urls[:-1]

    @retry(tries=5, delay=5, backoff=2)
    def fetch(self, url, proxy_obj=None):
        # url = 'https://api.ipify.org/?format=json'  # 这个用来调试代理
        header = {
            'Connection': 'close',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 Edg/96.0.1054.53',
        }

        logger.info(f"Fetching: {url}")

        r = requests.get(url, headers=header, timeout=30, allow_redirects=False)

        return r

    def get_snapshot_codes(self, link):
        """Extract snapshot urls for a link"""
        url = "https://web.archive.org/cdx/search/cdx?output=txt&filter=mimetype:text/html&filter=statuscode:200&fl=original,timestamp&url=" + link

        r = self.fetch(url)

        if r.status_code == 302:
            r.close()
            logger.error('Bot Detector Active')
            return [], 'bot_detector'

        if r.status_code != 200:
            logger.error(F"status {r.status_code}")
            r.close()
            return [], 'status_not_200'

        if not re.match(r'^http.+? (\d{14})$', r.text, flags=re.MULTILINE):
            r.close()
            logger.error("Snapshot list page body is invalid")
            return [], 'body_issue'

        tmp = r.text.split('\n')
        r.close()

        url_code_pair = []
        for item in tmp:
            match = re.search(r'(http.+?) (\d{14})', item)
            if not match:
                continue

            url_code_pair.append({'url': match.group(1), 'code': match.group(2)})

        return url_code_pair, None