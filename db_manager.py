import random
import time
from urllib.request import urlopen
from datetime import datetime

import sqlalchemy
from sqlalchemy import create_engine
import cv2
import pymysql
import requests
import pandas as pd
import numpy as np


def db_connect(db_cred):
    global cursor, conn, engine
    db_creds = []

    for keys, values in db_cred.items():
        db_creds.append(values)

    user = db_creds[0]
    passwd = db_creds[1]
    host = db_creds[2]
    database = db_creds[3]
    conn = pymysql.connect(user=user, passwd=passwd, host=host, database=database)
    engine = create_engine('mysql+pymysql://{}:{}@{}/{}?charset=utf8'.format(user, passwd, host, database))
    cursor = conn.cursor()
    return cursor, conn, engine


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
    cursor, conn, engine = db_connect(db_cred)
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
    cursor, conn, engine = db_connect(db_cred)
    cursor.execute('SELECT img_url_id, img_url FROM image_data')
    img_urls = cursor.fetchall()
    return img_urls


def data_roi_cv(img_blob, img_url_id):
    datetime = create_datetime()

    cursor.execute(
        "INSERT INTO cropped_images (img_url_id, cropped_img, datatime_img_cropped)"
        "VALUES(%s, %s, %s)", (img_url_id, img_blob, datetime))

    conn.commit()
    print('added cropped image')


def get_nlp_data(db_cred):
    cursor, conn, engine = db_connect(db_cred)
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
    cursor, conn, engine = db_connect(db_cred)

    # select image url id for insert into the images table
    cursor.execute("SELECT img_url_id FROM image_data")
    img_url_id = cursor.fetchall()
    img_url_id_list = [list(i) for i in img_url_id]

    for i in zip(fname, lname, img_url_id_list):
        datetime = create_datetime()

        # occasionally index error here
        cursor.execute(
            "INSERT INTO nlp_image_meta (img_url_id, fname, lname, datetime_updated)"
            "VALUES(%s, %s, %s, %s)", (i[2], i[0], i[1], datetime))

        conn.commit()


try:
    # TODO combine social and main into a single function/class
    def data_to_db_social(im_url, s_type, mag_names, db_cred):
        print(mag_names)
        cursor, conn, engine = db_connect(db_cred)

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
    cursor, conn, engine = db_connect(db_cred)

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

    data = []
    last_id = []

    #  select image url and id from image_data, add resulting BLOB/id to images table
    cursor.execute("SELECT img_url_id, img_url FROM image_data"
                   "")
    row = cursor.fetchall()
    count = 0
    for count, i in enumerate(row):
        image_page = requests.get(i[1])
        if image_page.status_code == 200:
            img_bin = url_to_image(i[1])
            data.append((i[0], m_name_id[0], s_type, img_bin))
    count += 1
    print(count)
    df = pd.DataFrame(data, columns=['img_url_id', 'mag_name_id', 'site_type', 'image'])

    if not data:
        pass
    else:
        df.to_sql(con=engine, name='images', if_exists='append', index=False)


    # if count == 0:
    #     df = pd.DataFrame(data, columns=['img_url_id', 'mag_name_id', 'site_type', 'image'])
    #     df.to_sql(con=engine, name='images', if_exists='append', index=False)
    #     print(df, 'ddddd')
    #
    # elif count != 0:
    #     df = pd.DataFrame(data, columns=['img_url_id', 'mag_name_id', 'site_type', 'image'])
    #     idx = df.index[-1]
    #     df1 = df.iloc[idx:]
    #     print(df1, 'fff')
    #     df1.to_sql(con=engine, name='images', if_exists='append', index=False)
    # print(count)


    # print('blobs added', s_type, mag_names)
