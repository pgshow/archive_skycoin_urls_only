import threading
import time
from urllib.parse import urlparse

import agent
import save
import archive
import config
import function as fc
from loguru import logger
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


def scrape(link, lock_db, lock_csv):
    # start
    sql = f"select id from scraped where url_md5='{fc.md5(link)}'"
    if config.DB_OBJ.select_exist(lock_db, sql):
        # don't scrape again if scraped
        return

    snap_pairs, err = archive_cls.get_snapshot_codes(link)  # get all snap timestamps for a page

    if not snap_pairs:
        logger.warning(f"There has no snapshot for: {link}")
        if err == 'body_issue':
            # some [body_issue] are empty body, so save scraped url
            sql = '''INSERT INTO Scraped(url_md5) VALUES(?)'''
            param = (fc.md5(link),)
            config.DB_OBJ.add(lock_db, sql=sql, param=param)

        if err == 'bot_detector':
            # stop for a while
            time.sleep(6)

        return

    # save scraped url
    sql = '''INSERT INTO Scraped(url_md5) VALUES(?)'''
    param = (fc.md5(link),)
    config.DB_OBJ.add(lock_db, sql=sql, param=param)

    logger.info(f"Extracted {len(snap_pairs)} snapshot form: {link}")

    # extract the domain as csv file's name
    res = urlparse(link)
    csv_path = f"./result/{res.netloc.replace(':80', '').replace('www', '').replace('.', '')}.csv"

    for snap_pair in snap_pairs:
        save.save_snapshot_url(snap_pair, csv_path, lock_db, lock_csv)


if __name__ == '__main__':
    m1 = multiprocessing.Manager()
    lock_db = m1.Lock()
    m2 = multiprocessing.Manager()
    lock_csv = m2.Lock()

    archive_cls = archive.Archive(config.Domain)

    # get all the urls those have history on Archive
    if config.Is_Import_From_File:
        link_list = archive_cls.import_urls(config.Import_File)  # import urls by local txt file
    else:
        link_list = archive_cls.get_all_urls()  # import urls by list page

    logger.info(f'get {len(link_list)} links for this website on Archive')

    # scraping the html and files from Archive
    with ThreadPoolExecutor(max_workers=config.Threading_Num) as t:
        all_task = []
        for link in link_list:
            all_task.append(t.submit(scrape, link, lock_db, lock_csv))

        wait(all_task, return_when=ALL_COMPLETED)

        # all_task = [t.submit(scrape, link, lock_db, lock_csv) for link in link_list]
        #
        # wait(all_task, return_when=ALL_COMPLETED)
