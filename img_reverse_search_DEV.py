import glob
import os
import pathlib
import time
import cv2
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver


# Define the Chrome Driver options
from db_manager import get_image_from_db_reverse


def selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-infobars")
    options.add_argument('--remote-debugging-port=9222')
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    # prefs = {"profile.default_content_setting_values.notifications": 2}
    prefs = {"credentials_enable_service": False,
             "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)
    # ------------ IMPORTANT: Change the 'executable path' to ensure Chrome Driver is accessible ---------------
    driver = webdriver.Chrome(executable_path=r'C:/seleniumChromeDriver/chromedriver_win32/chromedriver.exe',
                              options=options)
    return driver


def search_Google(img_files):
    # Read and import the CSV containing unique image file directories created by "get_img_files.py"
    # img_paths = pd.read_csv('img_paths.csv')

    # Run the Google reverse image search function
    # search_Google(df['Img_path'])

    # Initialise the driver using below selenium_driver() function
    driver = selenium_driver()

    # Initialise the lists to be stored for scraping
    # Image file directory is for creating a unique/foreign key for each record/image
    Img_path = []
    # Most important text from Google search query results is the 'related search'
    related_search_list = []

    # Iterate through each image file directory as listed in the CSV export from "get_img_files.py"
    for i in img_files:
        img_i = str(i)
        # Append and store the unique image file directories
        Img_path.append(img_i)
        try:
            # Open Google Images
            driver.get('https://www.google.com/imghp?hl=EN')
            time.sleep(2)

            # Locate the 'search by image' button
            cam_button = driver.find_elements_by_xpath("//div[@aria-label=\"Search by image\" and @role=\"button\"]")[0]
            time.sleep(1)
            cam_button.click()
            time.sleep(1)

            # Locate the 'upload image' tab
            upload_tab = driver.find_elements_by_xpath("//a[@class=\"iOGqzf H4qWMc aXIg1b\"]")[0]
            time.sleep(1)
            upload_tab.click()
            time.sleep(1)

            # Find image input
            upload_btn = driver.find_element_by_name('encoded_image')
            time.sleep(1)
            # Send the file directory to upload image
            upload_btn.send_keys(i)
            time.sleep(5)

            # Use BeautifulSoup to parse the search results
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')

            # Locate and append the Google 'related search query' result text
            related_search = soup.find("a", class_="fKDtNb").text
            related_search_list.append(related_search)

        except Exception as e:
            print(e)

    # Quit the driver
    driver.quit()

    # Create a pandas dataframe to store and output scraped text
    google_df = pd.concat([pd.DataFrame(Img_path),
                           pd.DataFrame(related_search_list)], axis=1)
    google_df.columns = ['Img_Directory', 'Google_Related']

    return google_df
    # Output a CSV table containing image directories and google related search results
    # google_df.to_csv("google_df.csv", index=False)


# Tineye web-scraping function
def search_tineye(driver, abs_path, file_name):

    # Initialise empty dictionary for data storage and CSV output
    tin_dict = {'Img_Directory': [],
                'num_res': [],
                'tineye_filename': [],
                'tin_text': []}

    record_match_all = []
    record_match_filename = []

    driver.get('https://tineye.com/')
    time.sleep(2)
    # Find Image Upload Box
    upload_btn = driver.find_element_by_id("upload_box")
    time.sleep(3)
    # Upload each (for i) image from directory
    file_path = ('{}\{}').format(abs_path, file_name)
    upload_btn.send_keys(file_path)
    time.sleep(5)
    content = driver.page_source
    soup = BeautifulSoup(content, 'html.parser')

    # If 'number of results' return is None, then append "none" to all,else continue with the scrape
    if soup.find('span', {"id": "result_count"}) is None:
        tin_dict['num_res'].append([None])
        record_match_all.append(None)
        record_match_filename.append(None)
    else:
        # Find the number of results returned
        result_count = soup.find('span', {"id": "result_count"}).string
        tin_dict['num_res'].append([result_count])

        # scrape all text for each 'match' returned
        # each match is contained within an array stored into "record_match_all" and then "tin_text"
        soup_match = soup.find_all('div', {"class": "match"})
        for match in soup_match:
            record_match_all.append([match.get_text(strip=True)])

    tin_df = pd.DataFrame.from_dict(tin_dict, orient='index')
    tin_df2 = tin_df.transpose()
    tin_df2 = pd.DataFrame(tin_df2, columns=['Img_Directory', 'num_res', 'tineye_filename', 'tin_text'])
    pd.DataFrame(tin_df2).to_csv("tineye_dict_data.csv")
    return tin_df2


# write img to a temp dir for processing and then remove
def write_temp_img(img_url_id, image):
    cv2.imwrite('img_{}.jpg'.format(img_url_id), image)
    image_path = '.'
    list_of_files = glob.glob(r'*.{}'.format('jpg'))

    for file_path in list_of_files:
        path_to_img = pathlib.Path(image_path)
        abs_path = path_to_img.absolute()
        file_name = file_path
        print(file_name)
        return abs_path, file_name


def main(db_cred):
    driver = selenium_driver()
    img_bytes = get_image_from_db_reverse(db_cred)
    for i in img_bytes:
        img_url_ids = i[0]
        cropped_imgs = i[1]
        nparr = np.fromstring(cropped_imgs, np.uint8)
        img_array = np.asarray(bytearray(nparr), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        # cv2.imshow('test', img)
        # cv2.waitKey(0)
        abs_path, file_name = write_temp_img(img_url_ids, img)
        search_tineye(driver, abs_path, file_name)
        try:
            os.remove(file_name)
        except PermissionError as e:
            time.sleep(5)



    #data_tineye = search_Tineye(image_id['Img_Directory'])
    # Send images to Google and scrape results
    #data_google = search_Google(image_id['Img_Directory'])
    # join Tineye & Google dataframes by foreign key (image ID)
    #joint_data = pd.concat([data_tineye, data_google], join="inner", axis=1)
    #joint_data.to_csv('joint_data.csv', index=False)
    #return joint_data


# Setup the parent directory containing sub-folders of image files.
img_direct = '/Users/alighterness/PycharmProjects/image_search_main/image_data'

#main(img_direct)

# if __name__ == "__main__":
#    try:
#        lambda: get_img_files.main(directory)
