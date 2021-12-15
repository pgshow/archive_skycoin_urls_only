import csv
import config
import function as fc
from loguru import logger


def save_snapshot_url(snap_pair, csv_path, lock_db, lock_csv):
    """save snapshot url to csv"""
    # combine the snapshot url
    snapshot_url = f"https://web.archive.org/web/{snap_pair['code']}/{snap_pair['url']}"

    sql = f"select id from saved_snapshot where url_md5='{fc.md5(snapshot_url)}'"
    if config.DB_OBJ.select_exist(lock_db, sql):
        # don't save this snapshot url again
        return

    # save snapshot url to DB avoids to save twice
    sql = '''INSERT INTO Saved_snapshot(url_md5) VALUES(?)'''
    param = (fc.md5(snapshot_url),)
    config.DB_OBJ.add(lock_db, sql=sql, param=param)

    try:
        lock_csv.acquire()

        with open(csv_path, 'a+', newline='', encoding="utf-8") as f:
            data_row = [snap_pair['code'][0:8], snapshot_url]  # 组合数据（日期，网址）
            csv_write = csv.writer(f)
            csv_write.writerow(data_row)

        return True

    except Exception as e:
        logger.error(f'Save err: {e}')
        return

    finally:
        lock_csv.release()
