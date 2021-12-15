import hashlib
import os
import sys

import replace


def link_list():
    with open("./links.txt") as f:
        text = f.read()
        return text.split('\n')


def replace_illegal_path(the_str):
    """replace all str to a new str"""
    commas = ['https://', 'http://', ':', '.']

    for old in commas:
        the_str = the_str.replace(old, '-', -1)

    return the_str


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def file_exist(file_path):
    """is file exist in the folder"""
    if os.path.exists(file_path):
        return True


def save_fetch(full_path, request, domain):
    """save the fetched resource from requests"""
    if full_path.endswith('.css'):
        css_code = replace.css_path_modify(request.text, domain)
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(css_code)

    else:
        with open(full_path, 'wb') as file:
            file.write(request.content)


def absolute_root_path(domain):
    """absolute path for the domain folder"""
    return sys.path[0] + '/' + domain.replace('.', '_')


def md5(s):
    h = hashlib.sha256()
    h.update(s.encode('utf-8'))

    return h.hexdigest()