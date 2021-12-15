import os
import re
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup, element, NavigableString

import download
import function


def replace_path_of_html(html, domain):
    """替换html里的路径"""
    # pattern = r''
    # re.sub(pattern, repl, string, count=0, flag=0)
    soup = BeautifulSoup(html, 'lxml')

    if not soup:
        return

    # 替换 link-href 的路径
    tags = soup.find_all('link')
    for item in tags:
        change_resource_path(item, domain, 'href')

    # 替换 script-src 的路径
    tags = soup.find_all('script')
    for item in tags:
        change_resource_path(item, domain, 'src')

    # 替换 img-src 的路径
    tags = soup.find_all('img')
    for item in tags:
        change_resource_path(item, domain, 'src')

    return str(soup)


def change_resource_path(item, domain, attr):
    """Change resource path to local path"""
    link = item.attrs.get(attr)
    if link:
        if ';base64,' in link:
            return

        parsed = urlparse(link)
        path = parsed.path

        # 得到目录和文件名
        dir_path, file_name = os.path.split(path)

        new_path = (function.absolute_root_path(domain) + function.replace_illegal_path(dir_path) + '/' + file_name).replace('/', '\\')

        item[attr] = new_path


def trim_page(html):
    """trim the ads and Archive's information"""
    soup = BeautifulSoup(html, 'lxml')

    if not soup:
        return

    # 删除跟 Archive 有关的广告
    if soup.select_one('div#wm-ipp-base'):
        soup.select_one('div#wm-ipp-base').extract()

    if soup.select_one('div#wm-ipp-print'):
        soup.select_one('div#wm-ipp-print').extract()

    if soup.select_one('div#donato'):
        soup.select_one('div#donato').extract()

    return str(soup)


def css_path_modify(text, domain):
    """modify the path in css file"""
    def call(m):
        # u = 'url(/web/20200524030037im_/https://www.skycoin.com/blog/fonts/skycoin-bold-webfont.woff)'
        old_path = m.group(1)

        # 得到目录和文件名
        dir_path, file_name = os.path.split(old_path)

        # 拼成新路径
        new_path = 'url(' + (function.absolute_root_path(domain) + function.replace_illegal_path(dir_path) + '/' + file_name).replace('/', '\\') + ')'
        return new_path

    modified = re.sub(r'url\((/web/20\d{12}[a-z]{0,2}_?/.+?)\)', call, text)
    return modified


def replace_hrefs(html, domain):
    """替换html里的 archive 超链接为本地链接"""
    soup = BeautifulSoup(html, 'lxml')

    if not soup:
        return

    # Get all hyperlinks on this page
    original_hrefs = []
    fixed_hrefs = []
    for h in soup.find_all('a'):
        url = h.get('href')
        if url:
            original_hrefs.append(url)

            page_path = url.replace('https://web.archive.org/web/', '/web/')  # 统一格式

            dir_path, file_name = download.remote_url_path_split(page_path)

            if not file_name:
                # 给伪静态目录添加.html后缀
                page_path = dir_path + '_.html'

            new_path = (function.absolute_root_path(domain) + page_path).replace('/', '\\')
            fixed_hrefs.append(new_path)

    for key, ori in enumerate(original_hrefs):
        html = html.replace(ori, fixed_hrefs[key])

    return html


# def css_callback(match):
#     print(match)
#     return "<a href=\"http://github.com/%s>%s</a>" % (match.group(0), match.group(0))
#
#
# string = "this is a #test #32345 dfsdf"
#
# print(re.sub('#[0-9]+', callback, string))