# Notes:
# 1. Images have been downloaded from Google Drive and stored on a local drive
# 1a. Input path is hardcoded in and will require modification to access another folder
# 2. Output path has been hardcoded.
# 2a. Output names do not contain information from which folder they were inputted.
# 2b. If images from a different folder are loaded, care must be taken to ensure output files are not overwritten
#     due to same filenames.
# 3. Adjusting contour_area up reduces "noise" (non-artwork ROI), but also reduces artwork detection
# 3a. ROI == Region of Interest == area inside bounding box
# 4. Few artworks returned a rectangular shape, which is why there is no contour search for a rectangle
# 5. The functions image_pathways() and get_roi() will require rewriting for use with the database
# 6. It produces 930 ROI from the 363 images in the Facebook folder
# 6a. Not all artworks were detected, but perhaps enough for proof-of-concept

import cv2
import numpy as np
import requests

from db_manager import data_roi_cv, get_image_from_db_cv


# convert to binary for db insert
def convert_to_binary(img_name, img_url_id):
    img_str = cv2.imencode('.jpg', img_name)[1].tobytes()
    data_roi_cv(img_str, img_url_id)  # to db manager


def image_preprocess(image):
    # Make grey image
    image_grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Filters
    filtered_image = cv2.bilateralFilter(image_grey, 13, 75, 75)
    filtered_image = cv2.GaussianBlur(filtered_image, (9, 9), 0)
    # Canny Edge Detection
    canny_image = cv2.Canny(filtered_image, 100, 200)
    kernel = np.ones((1, 1), np.uint8)
    dilation_image = cv2.dilate(canny_image, kernel, iterations=3)
    return dilation_image


# Region of Interest Extraction
def get_roi(dilation_image, image, img_url_id):  # InputOutputArray only required for development
    roi_number = 0
    contours, _ = cv2.findContours(dilation_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.06 * cv2.arcLength(contour, True), True)
        # Calculate area in contour
        contour_area = cv2.contourArea(contour)
        # Get bounding dimensions
        x, y, w, h = cv2.boundingRect(approx)
        # Calculate area under bounding rectangle
        bound_area = w * h
        if bound_area >= 14000 and contour_area >= 3.5:
            roi = image[y:y + h, x:x + w]
            # cv2.imwrite('img_{}.png'.format(roi_number), roi)
            convert_to_binary(roi, img_url_id)
            roi_number += 1
    return roi_number


def main(db_cred):

    img_urls = get_image_from_db_cv(db_cred)
    for i in img_urls:
        img_url_id = i[0]
        img_url = i[1]
        resp_url = requests.get(img_url)
        if resp_url.status_code == 200:
            image_links = requests.get(img_url, stream=True).raw
            img = np.asarray(bytearray(image_links.read()), dtype="int8")
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)
            # cv2.imshow('test', img)
            # cv2.waitKey(0)
            dilation_image = image_preprocess(img)
            get_roi(dilation_image, img, img_url_id)
