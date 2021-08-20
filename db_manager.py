import random
from urllib.request import urlopen
from datetime import datetime

import cv2
import pymysql
import requests
import pandas as pd
import numpy as np


def db_connect(db_cred):
    global cursor, conn
    db_creds = []

    for keys, values in db_cred.items():
        db_creds.append(values)

    user = db_creds[0]
    passwd = db_creds[1]
    host = db_creds[2]
    database = db_creds[3]
    conn = pymysql.connect(user=user, passwd=passwd, host=host, database=database)
    cursor = conn.cursor()

    return cursor, conn


# check if entry entry exists in db, if so return True
def check_entry_exist(entry, exits):
    if entry == exits:
        return True
    if entry != exits:
        return False


# need to change to a trigger
def check_id_exist(urlID, url_id):
    i = [list(i) for i in urlID]
    res = any(url_id in sublist for sublist in i)
    if res is False:
        return False
    else:
        pass


# adds nlp results of tineye/google to db
def add_nlp_reverse_search_results(db_cred):
    pass


# query image for reverse search links
def get_image_from_db_crop(db_cred):
    cursor, conn = db_connect(db_cred)
    cursor.execute('SELECT img_url_id, cropped_img FROM cropped_images')
    img_bytes = cursor.fetchall()  # can return all links or one and call the db every time
    return img_bytes


def create_datetime():
    # add date/time when entry is made
    now = datetime.now()
    date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return date_time


# query image links
def get_image_from_db_cv(db_cred):
    cursor, conn = db_connect(db_cred)
    cursor.execute('SELECT img_url_id, img_url FROM image_data')
    img_urls = cursor.fetchall()  # can return all links or one and call the db every time
    return img_urls


def data_roi_cv(img_blob, img_url_id):
    # URL images ids are added to table 'cropped_images' using a trigger
    # create trigger 'add_url_id_to_cropped_images' after update on 'image_data'
    # FOR EACH ROW
    # INSERT INTO cropped_images(img_url_id) VALUES(new.img_url_id)

    datetime = create_datetime()

    cursor.execute(
        "INSERT INTO cropped_images (img_url_id, cropped_img, datatime_img_cropped)"
        "VALUES(%s, %s, %s)", (img_url_id, img_blob, datetime))

    conn.commit()
    print('added cropped image')


def get_nlp_data(db_cred):
    cursor, conn = db_connect(db_cred)
    cursor.execute('SELECT img_url, img_caption, img_page_url FROM image_data')
    img_caption = cursor.fetchall()
    dataset = pd.DataFrame(img_caption, columns=["URL", "Caption", "img_page_url"])
    return dataset


# download the image, convert to a np array and read
try:
    def url_to_image(url):
        resp = urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = cv2.imencode('.jpg', image)[1].tobytes()
        return image

except cv2.error as e:
    print('No image to display')  # sometime an images does not exist


def data_to_db_nlp(fname, lname, db_cred):
    cursor, conn = db_connect(db_cred)

    # URL images ids are added to table 'nlp_image_meta' using a trigger
    # create trigger 'add_url_id_to_nlp' after update on 'image_data'
    # FOR EACH ROW
    # INSERT INTO nlp_image_meta(img_url_id) VALUES(new.img_url_id)

    datetime = create_datetime()

    # occasionally index error here
    cursor.execute(
        "INSERT INTO nlp_image_meta (fname, lname, datatime_img_url_scrapped)"
        "VALUES(%s, %s, %s)", (fname, lname, datetime))

    conn.commit()


try:
    # TODO combine social and main into a single function
    def data_to_db_social(im_url, s_type, mag_names, db_cred):
        print(mag_names)
        cursor, conn = db_connect(db_cred)

        mag_names = mag_names[0]
        # add data to metadata table
        cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
        m_name_id = cursor.fetchone()

        # select image url id for insert into the images table
        cursor.execute("SELECT img_url_id FROM image_data")
        img_url_id = cursor.fetchall()

        for img_url_id, matches_img_url in zip(img_url_id, im_url):
            image_page = requests.get(matches_img_url)

            date_time = create_datetime()

            if image_page.status_code == 200:

                cursor.execute("SELECT img_url_id FROM images")
                exits = cursor.fetchall()
                exits = check_id_exist(exits, img_url_id)

                if exits is False:
                    cursor.execute(
                        "INSERT INTO image_data (mag_name_id, img_url, datatime_img_url_scrapped)"
                        "VALUES(%s, %s, %s)", (m_name_id, matches_img_url, date_time))

                    conn.commit()

                    print('added', s_type)
                else:
                    print('skipping, img_url_id existing')

except IndexError as e:
    print(e)
except AttributeError as e:
    print(e)
except pymysql.IntegrityError as e:
    print(e)
    pass


def image_data_to_db_main(matches_img_urls, mag_names, owners, credited, metadatas, host_urls, img_page_urls, s_type,
                          art_date, art_title, db_cred):
    cursor, conn = db_connect(db_cred)

    for matches_img_url, img_page_url, metadata, credit in zip(matches_img_urls, img_page_urls, credited, metadatas):
        #  add data to metadata table
        cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
        m_name_id = cursor.fetchone()

        date_time = create_datetime()

        cursor.execute(
            "INSERT INTO image_data (mag_name_id, img_caption, img_credited, img_url, img_page_url, "
            "article_created_data, article_name, datatime_img_url_scrapped) "
            "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
            (m_name_id, metadata, credit, matches_img_url, img_page_urls, art_date, art_title, date_time))
        conn.commit()

        print('added', s_type, mag_names)


def image_blob_to_db(mag_names, s_type):
    # add data to metadata table
    cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
    m_name_id = cursor.fetchone()

    #  select image url from image_data, add resulting BLOB to images table
    cursor.execute('SELECT img_url FROM image_data WHERE mag_name_id')
    img_url = cursor.fetchall()

    # select image url id for insert into the images table
    cursor.execute("SELECT img_url_id FROM image_data")
    img_url_id = cursor.fetchall()

    for i, j in zip(img_url_id, img_url):
        img_url_id = i[0]
        img_url = j[0]
        #print(img_url_id, s_type)
        image_page = requests.get(img_url)
        if image_page.status_code == 200:
            img_bin = url_to_image(img_url)

            # a dumb way of adding eh img_url_ids, should use trigger
            # occasionally index error here
            cursor.execute("SELECT img_url_id FROM images")
            exits = cursor.fetchall()
            exits = check_id_exist(exits, img_url_id)

            if exits is False:
                cursor.execute(
                    "INSERT INTO images (img_url_id, mag_name_id, site_type, image)" "VALUES(%s, %s, %s, %s)",
                    (img_url_id, m_name_id, s_type, img_bin))
            else:
                pass
                #print('skipping, img_url_id existing', img_url_id)

        conn.commit()

    print('blob added', s_type, mag_names)
