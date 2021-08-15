
# script to upload pre cropped images for Tineye metadata testing

import glob
import pathlib
from datetime import datetime
import pymysql


def db_connect(db_cred):
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


def create_datetime():
    # add date/time when entry is made
    now = datetime.now()
    date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return date_time


def get_img_from_dir():
    image_path = '.'
    list_of_files = glob.glob(r'*.{}'.format('jpg'))
    path_to_img = pathlib.Path(image_path)
    abs_path = path_to_img.absolute()
    return abs_path, list_of_files


def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData


def insertBLOB(img_blob, db_cred):

    datetimes = create_datetime()

    print("Adding image")
    try:
        cursor, conn = db_connect(db_cred)

        cursor.execute(
            "INSERT INTO cropped_images (cropped_img, datatime_img_cropped)"
            "VALUES(%s, %s)", (img_blob, datetimes))

        conn.commit()

    except pymysql.connect as error:
        print("Failed to insert {}".format(error))

    finally:
        pass


def main(creds):
    list_of_imgs = get_img_from_dir()
    for i in list_of_imgs[1]:
        img_blob = convertToBinaryData(i)
        insertBLOB(img_blob, creds)



