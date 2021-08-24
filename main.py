import json
import time
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import TimeoutException
import pymysql
import cv2

import db_manager
import get_main_site_bauer
# import get_main_site_media
import cv_processing_crop
import get_social_img
import nlp_name_search
import img_reverse_search_DEV
import nlp_imagescrape_tineye


# TODO gets credentials for social media sites, should be called from a db, no json
# TODO the site type, twitter etc, should be a separate table in the db (not the json)
# TODO facebook scrape needs work, chrome freezes.. sometimes
# json for testing only
def cred_json_parser():
    with open('config_options.json', 'r') as jsonFile1:
        data = json.load(jsonFile1)
        return data


# parallel downloads
def run_io_tasks_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()


if __name__ == "__main__":  # only executes if imported as main file

    creds = cred_json_parser()
    # db_creds = db_cred_json_parser()
    db_manager.db_cred_json_parser()

    try:
        # add scrape calls here
        # multithread all scrapes
        # added sleep cause pymsql can make simultaneous db connections (currently PyMySQL threadsafe = 1)
        run_io_tasks_in_parallel([
            lambda: get_main_site_bauer.main(creds),
            # time.sleep(3),
            # lambda: get_main_site_media.main(creds), # TODO media site not complete, behind JS
            # time.sleep(3),
            # lambda: get_social_img.call_facebook(creds),

            # TODO pinterest Vogue Australia needs work, when to stop, goes of forever. Need a stop date
            # TODO mostly fashion, need CV to detect clothes to reject image
            # lambda: get_social_img.call_pinterest(creds),
            # time.sleep(3),
            # lambda: get_social_img.call_instagram(creds),
            # time.sleep(3),
            #lambda: get_social_img.call_twitter(creds),
        ])

        # TODO CV and NLP processing, more work is required to time the threading
        # cv_processing_crop.main(db_creds)
        # nlp_name_search.main(db_creds)
        # img_reverse_search_DEV.main(db_creds)
        # nlp_imagescrape_tineye.main()

    except TimeoutException as e:
        print("Wait timeout, check 'WebDriverWait(driver, n)' in Class Helper. Error: {}".format(e))
    except pymysql.OperationalError as e:
        print(
            'No connection to database. Please check connection details in config.json or database connection: {}'.format(
                e))
        pass
    except pymysql.DataError as e:
        print('Data too long, check variable length in database : {}'.format(e))
    except PermissionError as e:
        print(e)
        time.sleep(15)  # need to test wait time, depends on time to load image
    except pymysql.IntegrityError as e:
        print(e)
        pass
    except AssertionError as e:  # strange error, appears to be specific to pymysql and random
        print(e)
        pass
    except pymysql.InternalError as e:  # multithreading causing this error, need a queue manager
        print(e)
        pass
    except IndexError as e:  # need to chase this error down  - image_blob_to_db_main(mag_names, s_type) line 127  cursor.execute("SELECT img_url_id FROM images") line 223
        print(e)
        pass
    except cv2.error as e:  # to catch cv2 errors line 205
        print(e)
        pass

# below means there was no image for cv to process - line line 105 in db_manager.py
# cv2.error: OpenCV(4.5.3) C:\Users\runneradmin\AppData\Local\Temp\pip-req-build-q3d_8t8e\opencv\modules\imgcodecs\src\loadsave.cpp:978: error: (-215:Assertion failed) !image.empty() in function 'cv::imencode'
