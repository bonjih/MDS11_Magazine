import re
from collections import OrderedDict
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import DesiredCapabilities
#from fake_useragent import UserAgent
from datetime import datetime

from process_config_json import get_configs_main
from save_img_to_dir import download_images, make_dir
from db_manager import image_data_to_db_main, image_blob_to_db

startTime = datetime.now()


# def fake_ua():
#     ua = UserAgent()
#     header = {'User-Agent': str(ua.random)}
#     return header


# for Vogue, request additional options and also edit the cdc_ to avoid 403 errors
def selenium_driver():
    #header = fake_ua()
    # option to help to only login once
    options = webdriver.ChromeOptions()
    options.add_argument(
        r'user-data-dir=C:\Users\ben.hamilton\AppData\Local\Temp\scoped_dir84904_70256885\Default')  # Path to your chrome profile - chrome://version/
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    #options.add_argument(str(header))

    # enable browser logging
    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL'}

    driver = webdriver.Chrome(executable_path=r'C:/seleniumChromeDriver/chromedriver_win32/chromedriver.exe',
                              options=options, desired_capabilities=d)

    return driver


def remove_extra_char_in_values(res_value):
    res_value = str(res_value)[1:-1]
    res_value = res_value.replace("'", "")
    res_value = res_value.replace("]", "")
    res_value = res_value.replace("[", "")
    res_value = res_value.replace(",", "")
    return res_value


def check_path_exists(path, driver):
    try:
        driver.find_element_by_xpath(path)
    except NoSuchElementException:
        return False
    return True


# get all image urls, all sites and filter
def get_all_urls(driver, host_url, mag_name, owner, s_type):
    driver.get(host_url)
    links = driver.find_elements_by_tag_name('a')
    links = [i.get_attribute('href') for i in links]
    # hard coded assumption using '\d' in regex to filter stories. All stores have appear to have numbers in the url,
    # not perfect but saves clicking through all the stories to get to the content.
    r = re.compile(r'\S+\d\S+')
    image_urls = list(filter(r.match, links))
    image_urls2 = list(OrderedDict.fromkeys(image_urls))  # remove duplications from the url page list
    get_images(driver, image_urls2, host_url, mag_name, owner, s_type)


def get_images(driver, img_page_urls, host_urls, mag_names, owners, s_type):

    for img_page_url in img_page_urls:
        image_page = requests.get(img_page_url)

        if image_page.status_code == 200:
            driver.get(img_page_url)
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')

            # get article creation date and name/title
            article_date = soup.find("span", {'class': 'article__date-created'})
            article_title = soup.find("h1", {'class': 'article__title'})

            # for some reason '.text' did not work
            art_date = []
            art_title = []
            r = re.compile(r'\>(.*?)\<')
            for article_date in re.findall(r, str(article_date)):
                art_date.append(article_date)
            for article_title in re.findall(r, str(article_title)):
                art_title.append(article_title)

            metadata = []
            credit = []
            matches_img_url = []

            temp = soup.find_all(lambda tag: tag.name == 'figure')

            for y in temp:
                if y.text is None:
                    metadata.append(None)
                else:
                    metadata.append(y.text)

                jw_video = './/div[@class="jw-video-player"]'
                a = check_path_exists(jw_video, driver)  # check if hero has video (js), if True, skip
                if a is False:
                    matches_img_url.append(y.find('source').get('data-srcset'))
                else:
                    pass

                if y.find('span') is None:
                    credit.append(None)
                else:
                    credit.append(y.find('span').text)

            image_data_to_db_main(matches_img_url, mag_names, owners, metadata, credit, host_urls, img_page_url, s_type, art_date, art_title, db_creds)
            image_blob_to_db(mag_names, s_type)

            # to save images to disk
            # dirname = 'imgs2/main_site'  # need to be added to config.json
            # make_dir(dirname)
            # download_images(dirname, matches_img_url, mag_names, s_type)


def main(site_creds, db_cred):
    global db_creds

    mag_name, urls, host_name, owners, site_type = get_configs_main(site_creds, db_cred)
    db_creds = db_cred

    driver = selenium_driver()
    a = zip(urls, owners, mag_name, site_type)  # to filter bauer from news_life_media

    for i in a:
        # temp hard code to remove vogue
        links = remove_extra_char_in_values(i[0])
        owner = remove_extra_char_in_values(i[1])
        m_name = remove_extra_char_in_values(i[2])
        s_type = remove_extra_char_in_values(i[3])

        if owner == "bauer":
            get_all_urls(driver, links, m_name, owner, s_type)
        else:
            pass

    # def call_bauer(site_creds):
    #     magazine_name, urls_list, name_host, owners, users, pswrd, site_type = get_configs_bau(site_creds, db_access)
    #     process_site_images(magazine_name, urls_list, name_host, owners, users, pswrd, site_type)

    print(datetime.now() - startTime)
