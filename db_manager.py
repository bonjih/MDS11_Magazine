from urllib.request import urlopen
from datetime import datetime
from sqlalchemy import create_engine
import cv2
import pymysql
import requests
import pandas as pd
import numpy as np
import json


# db credentials
def db_cred_json_parser():
    with open('config_creds_db.json', 'r') as jsonFile2:
        db_credentials = json.load(jsonFile2)
        return db_credentials


def db_connect():
    db_cred = db_cred_json_parser()
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


# need to change to a trigger
def check_id_exist(urlID, url_id):
    i = [list(i) for i in urlID]
    res = any(url_id in sublist for sublist in i)
    if res is False:
        return False
    else:
        pass


# adds nlp results of tineye/google to db
def add_nlp_reverse_search_results():
    pass


# query image for reverse search links
def get_image_from_db_crop():
    cursor, conn, engine = db_connect()

    cursor.execute('SELECT img_url_id, cropped_img FROM cropped_images')
    img_bytes = cursor.fetchall()  # can return all links or one and call the db every time
    return img_bytes


def create_datetime():
    # add date/time when entry is made
    now = datetime.now()
    date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return date_time


# query image links
def get_image_from_db_cv():
    cursor, conn, engine = db_connect()

    cursor.execute('SELECT img_url_id, img_url FROM image_data')
    img_urls = cursor.fetchall()
    return img_urls


def data_roi_cv(img_blob, img_url_id):
    cursor, conn, engine = db_connect()

    datetime = create_datetime()

    cursor.execute(
        "INSERT INTO cropped_images (img_url_id, cropped_img, datatime_img_cropped)"
        "VALUES(%s, %s, %s)", (img_url_id, img_blob, datetime))

    conn.commit()
    print('added cropped image')


def get_nlp_data():
    cursor, conn, engine = db_connect()

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


def data_to_db_nlp(fname, lname):
    cursor, conn, engine = db_connect()

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


def image_data_to_db(matches_img_urls, mag_names, owners, credited, metadatas, host_urls, img_page_urls, s_type, art_date, art_title):
    cursor, conn, engine = db_connect()

    for matches_img_url, img_page_url, metadata, credit in zip(matches_img_urls, img_page_urls, credited, metadatas):
        #  add data to metadata table
        cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
        m_name_id = cursor.fetchone()

        date_time = create_datetime()

        if s_type == 'main_site':
            cursor.execute(
                "INSERT INTO image_data (mag_name_id, img_caption, img_credited, img_url, img_page_url, "
                "article_created_data, article_name, datatime_img_url_scrapped) "
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                (m_name_id, metadata, credit, matches_img_url, img_page_urls, art_date, art_title, date_time))
            conn.commit()

        else:
            cursor.execute(
                "INSERT INTO image_data (mag_name_id, img_url, datatime_img_url_scrapped)"
                "VALUES(%s, %s, %s)", (m_name_id, matches_img_url, date_time))

        print('added', s_type, mag_names)


def image_blob_to_db(mag_names, s_type):
    cursor, conn, engine = db_connect()

    # add data to metadata table
    cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
    m_name_id = cursor.fetchone()

    data = []

    #  select image url and id from image_data, add resulting BLOB/id to images table
    cursor.execute("SELECT img_url_id, img_url FROM image_data"
                   "")
    row = cursor.fetchall()

    for i in row:
        image_page = requests.get(i[1])
        if image_page.status_code == 200:
            img_bin = url_to_image(i[1])
            data.append((i[0], m_name_id[0], s_type, img_bin))

    df = pd.DataFrame(data, columns=['img_url_id', 'mag_name_id', 'site_type', 'image'])

    if not data:
        pass
    else:
        df.to_sql(con=engine, name='images', if_exists='append', index=False)
