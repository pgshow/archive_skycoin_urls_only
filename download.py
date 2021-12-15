import os

import requests

import function
from urllib.parse import urlparse
from retry import retry
from loguru import logger


def download_resource(domain, resource_url):
    """to download a resource"""
    try:
        dir_path, file_name = remote_url_path_split(resource_url)

        # download filter
        if 'favicon.ico' in file_name:
            return
        if file_name.endswith('.woff2'):
            return
        if 'platform.twitter.com' in resource_url:
            return
        if 'ajax.googleapis.com' in resource_url:
            return
        if 's3.amazonaws.com' in resource_url:
            return
        if 'www.google-analytics.com' in resource_url:
            return

        dir_full_path = combine_domain_folder(domain, dir_path)  # domain folder is the root
        function.create_dirs(dir_full_path)  # create the dirs

        file_full_path = dir_full_path + file_name
        if os.path.exists(file_full_path):
            # 如果文件已经存在就跳过
            logger.debug(f"Already: {file_full_path}")
            return

        r = _download(resource_url)

        if not r or r.status_code != 200:
            return

        function.save_fetch(file_full_path, r, domain)
        # logger.debug(f"Saved: {file_full_path}")
    except:
        pass


def save_page(domain, page_url, body):
    """download page to local"""
    page_url = page_url.replace(f'/https://{domain}', '')

    dir_path, file_name = remote_url_path_split(page_url)

    if not file_name:
        # 给伪静态目录添加.html后缀
        page_path = dir_path + '_.html'
        dir_path, file_name = os.path.split(page_path)  # 拆分目录和文件名

    dir_full_path = combine_domain_folder(domain, dir_path)  # domain folder is the root
    function.create_dirs(dir_full_path)  # create the dirs

    full_page_path = dir_full_path + file_name

    # 保存文件
    with open(full_page_path, 'w', encoding='utf-8') as file:
        file.write(body)

    logger.info(f"Saved page: {full_page_path}")


def remote_url_path_split(url):
    """Convert Remote resource_url to Local path"""
    # get path
    parsed = urlparse(url)
    path = parsed.path

    # get dir path and file name
    dir_path, file_name = os.path.split(path)

    # replace the commas that Windows folder unavailable
    dir_path = function.replace_illegal_path(dir_path)

    return dir_path, file_name


def combine_domain_folder(domain, path):
    """convert the dir path with this domain folder"""
    if not path.endswith('/'):
        path = path + '/'

    if path.startswith('/'):
        return './' + domain.replace('.', '_') + path
    else:
        return './' + domain.replace('.', '_') + './' + path


@retry(tries=2, delay=5, backoff=2)
def _download(url):
    header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0(WindowsNT10.0;Win64;x64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/92.0.4515.131Safari/537.36',
    }

    logger.info(f"Download file: {url}")

    r = requests.get(url, headers=header, timeout=45)

    if r.status_code != 200:
        return

    return r
