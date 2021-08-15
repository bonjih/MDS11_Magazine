import json
import time
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import TimeoutException
import pymysql

import get_main_site_bauer
# import get_main_site_media
import cv_processing_crop
import get_social_img
import nlp_search
import img_reverse_search_DEV
import nlp_imagescrape_tineye


# TODO gets credentials for social media sites, should be called from a db, no json
# TODO the site type, twitter etc, should be a separate table in the db (not the json)
# TODO facebook scrape needs work, chrome freezes
# json for testing only
def cred_json_parser():
    with open('config_options.json', 'r') as jsonFile1:
        data = json.load(jsonFile1)
        return data


# db credentials
def db_cred_json_parser():
    with open('config_creds_db.json', 'r') as jsonFile2:
        db_credentials = json.load(jsonFile2)
        return db_credentials


# parallel downloads
def run_io_tasks_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()


if __name__ == "__main__":  # only executes if imported as main file

    creds = cred_json_parser()
    db_creds = db_cred_json_parser()

    try:
        # add scrape calls here
        # multithread all scrapes
        run_io_tasks_in_parallel([
            #lambda: get_main_site_bauer.main(creds, db_creds),
            # lambda: get_main_site_media.main(creds, db_creds), # TODO media site not complete, behind JS
            #lambda: get_social_img.call_facebook(creds, db_creds),
            #lambda: get_social_img.call_pinterest(creds, db_creds),
            # lambda: get_social_img.call_instagram(creds, db_creds),
            # lambda: get_social_img.call_twitter(creds, db_creds),
        ])

        # TODO CV and NLP processing, more work is required to time the threading
        cv_processing_crop.main(db_creds)
        # nlp_search.main(db_creds)
        #img_reverse_search_DEV.main(db_creds)
        nlp_imagescrape_tineye.main()

    except TimeoutException as e:
        print("Wait timeout, check 'WebDriverWait(driver, n)' in Class Helper. Error: {}".format(e))
    except pymysql.OperationalError as e:
        print('No connection to database. Please check connection details in config.json: {}'.format(e))
    except pymysql.DataError as e:
        print('Data too long, check variable length in database : {}'.format(e))
    except PermissionError as e:
        print(e)
        time.sleep(15)  # need to test wait time, depends on time to load image
    except pymysql.IntegrityError as e:
        print(e)
        pass
