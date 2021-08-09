import random
from datetime import datetime
import pymysql
import requests
import pandas as pd


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


# query image for reverse search links
def get_image_from_db_reverse(db_cred):
    cursor, conn = db_connect(db_cred)
    cursor.execute('SELECT cropped_img FROM cropped_images')
    numrows = cursor.rowcount
    img_urls = cursor.fetchmany(numrows)  # can return all links or one and call the db every time
    cropped_image_list = [item for list2 in img_urls for item in list2]
    return cropped_image_list



# create img_url_id
# should create a db trigger and concat img_metadata_id and mag_name_id
def create_img_url_id(m_name_id):
    url_ids = random.randint(1000, 9999)
    url_id = str(url_ids) + str(m_name_id[0])
    return url_id


def create_datetime():
    # add date/time when entry is made
    now = datetime.now()
    date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return date_time


# query image links
def get_image_from_db_cv(db_cred):
    cursor, conn = db_connect(db_cred)
    cursor.execute('SELECT img_url FROM image_data')
    numrows = cursor.rowcount
    img_urls = cursor.fetchmany(numrows)  # can return all links or one and call the db every time
    img_url_list = [item for list2 in img_urls for item in list2]
    return img_url_list


def data_roi_cv(img_blob):

    # URL images ids are added to table 'cropped_images' using a trigger
    # create trigger 'add_url_id_to_cropped_images' after update on 'image_data'
    # FOR EACH ROW
    # INSERT INTO cropped_images(img_url_id) VALUES(new.img_url_id)
    datetime = create_datetime()

    cursor.execute(
        "INSERT INTO cropped_images (cropped_img, datatime_img_cropped)"
        "VALUES(%s, %s)", (img_blob, datetime))

    conn.commit()
    print('added cropped image')


def get_nlp_data(db_cred):
    cursor, conn = db_connect(db_cred)
    cursor.execute('SELECT img_url, img_caption, img_page_url FROM image_data')
    img_caption = cursor.fetchall()
    dataset = pd.DataFrame(img_caption, columns=["URL", "Caption", "img_page_url"])
    return dataset


def data_to_db_nlp(fname, lname, db_cred):
    cursor, conn = db_connect(db_cred)

    # URL images ids are added to table 'nlp_image_meta' using a trigger
    # create trigger 'add_url_id_to_nlp' after update on 'image_data'
    # FOR EACH ROW
    # INSERT INTO nlp_image_meta(img_url_id) VALUES(new.img_url_id)

    datetime = create_datetime()

    cursor.execute(
        "INSERT INTO nlp_image_meta (fname, lname, datatime_img_url_scrapped)"
        "VALUES(%s, %s, %s)", (fname, lname, datetime))

    conn.commit()


# TODO combine social and main into a single function
def data_to_db_social(im_url, s_type, mag_names, db_cred):
    print(mag_names)
    cursor, conn = db_connect(db_cred)

    mag_names = mag_names[0]
    # add data to metadata table
    cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
    m_name_id = cursor.fetchone()

    for matches_img_url in im_url:
        image_page = requests.get(matches_img_url)

        date_time = create_datetime()
        url_id = create_img_url_id(m_name_id)

        if image_page.status_code == 200:
            response = requests.get(matches_img_url, stream=True)

            cursor.execute(
                "INSERT INTO image_data (mag_name_id, img_url_id, img_url, datatime_img_url_scrapped)"
                "VALUES(%s, %s, %s, %s)", (m_name_id, url_id, matches_img_url, date_time))

            cursor.execute("INSERT INTO images (img_url_id, mag_name_id, site_type, image)"
                           "VALUES(%s, %s, %s, %s)", (url_id, m_name_id, s_type, response.raw))

            conn.commit()

        print('added', s_type)


def data_to_db_main(matches_img_urls, mag_names, owners, credited, metadatas, host_urls, img_page_urls, s_type,
                    art_date, art_title, db_cred):
    cursor, conn = db_connect(db_cred)

    for matches_img_url, img_page_url, metadata, credit in zip(matches_img_urls, img_page_urls, credited, metadatas):

        # table - publisher
        cursor.execute('SELECT mag_name FROM publisher WHERE mag_name = %s', [mag_names])
        exits = cursor.fetchone()
        exits = exits[0]
        exits = check_entry_exist(mag_names, exits)

        if exits is False:
            cursor.executemany("INSERT INTO publisher (pub_name, mag_name)" "VALUES(%s, %s)", [(owners, mag_names)])
            print('Owner and title added to db')
        else:
            print('skipping, owner and title exist in database')

            # add data to metadata table
            cursor.execute("SELECT mag_name_id FROM publisher WHERE mag_name = %s", [mag_names])
            m_name_id = cursor.fetchone()

            date_time = create_datetime()
            url_id = create_img_url_id(m_name_id)

            cursor.execute(
                "INSERT INTO image_data (mag_name_id, img_url_id, img_caption, img_credited, img_url, img_page_url, "
                "article_created_data, article_name, datatime_img_url_scrapped) "
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (m_name_id, url_id, metadata, credit, matches_img_url, img_page_urls, art_date, art_title, date_time))
            #conn.commit()

            #  select image url from image_data, add resulting BLOB to images table
            cursor.execute('SELECT img_url FROM image_data WHERE mag_name_id = %s', [m_name_id])
            im_url = cursor.fetchone()
            im_url = im_url[0]

            # URL images ids are added to table 'nlp_image_meta' using a trigger
            # create trigger 'add_url_id_to_img' after update on 'image_data'
            # FOR EACH ROW
            # INSERT INTO images(img_url_id) VALUES(new.img_url_id)

            image_page = requests.get(im_url)
            if image_page.status_code == 200:
                response = requests.get(im_url, stream=True)
                cursor.execute(
                    "INSERT INTO images (mag_name_id, site_type, image)" "VALUES(%s, %s, %s)",
                    (m_name_id, s_type, response.raw))

            conn.commit()

            print('added', s_type)
