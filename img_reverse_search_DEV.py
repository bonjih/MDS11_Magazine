import glob
import os
import pathlib
import time

import cv2
import pandas as pd
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

# Function to get image directory file names
def get_img_files(img_folder):
    # Walk through each folder and sub-folder
    for subdir, dirs, files in os.walk(img_folder):
        # Initialise list for filepath names
        filepath = []
        for filename in files:
            f = subdir + os.sep + filename
            # Append names of files ending with .jpg or .png
            if f.endswith(".jpg") or f.endswith(".png"):
                filepath.append(f)

    # Store into dataframe for csv output
    #df = pd.DataFrame(filepath, columns=['Img_Directory'])
    #return df


# Tineye web-scraping function
def search_tineye(img_files):
    # Setup Chrome driver
    driver = selenium_driver()
    # Initialise empty dictionary for data storage and CSV output
    tin_dict = {'Img_Directory': [],
                'num_res': [],
                'tineye_filename': [],
                'tin_text': []}

    # Iterate through each image file directory
    for i in img_files:
        img_i = str(i)
        # Store unique image directory filename to output csv
        tin_dict['Img_Directory'].append([img_i])
        record_match_all = []
        record_match_filename = []
        try:
            # Open the website
            driver.get('https://tineye.com/')
            time.sleep(2)
            # Find Image Upload Box
            upload_btn = driver.find_element_by_id("upload_box")
            time.sleep(3)
            # Upload each (for i) image from directory
            upload_btn.send_keys(i)
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

                # identify specifically "filename" found in each match as this may be most useful
                soup_match_filename = soup.find_all('a', {"class": "truncate"})
                for filename in soup_match_filename:
                    record_match_filename.append([filename.get_text(strip=True)])

            # append scraped text to output dictionary for CSV export
            tin_dict['tin_text'].append([record_match_all])
            tin_dict['tineye_filename'].append([record_match_filename])
        except Exception as e:
            print(e)
    driver.quit()

    # Output the dictionary as a CSV of Tineye Scraped text
    tin_df = pd.DataFrame.from_dict(tin_dict, orient='index')
    tin_df2 = tin_df.transpose()
    tin_df2 = pd.DataFrame(tin_df2, columns=['Img_Directory', 'num_res', 'tineye_filename', 'tin_text'])

    return tin_df2
    # pd.DataFrame(tin_df2).to_csv("tineye_dict_data.csv")


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


# write img to a temp dir for processing and then remove
def write_temp_img(img_tineye_list):
    cv2.imwrite('name.jpg', img_tineye_list)
    image_path = '.'
    list_of_files = glob.glob(r'*.{}'.format('jpg'))

    for file_path in list_of_files:
        path_to_img = pathlib.Path(image_path)
        abs_path = path_to_img.absolute()
        file_name = file_path
        return abs_path, file_name


def upload_test(driver, abs_path, file_name):

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


def main(db_cred):
    driver = selenium_driver()
    for i in get_image_from_db_reverse(db_cred):
        abs_path, file_name = write_temp_img(i)
        upload_test(driver, abs_path, file_name)









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
