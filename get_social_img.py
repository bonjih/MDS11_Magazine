import copy
import random
import re
import socket
import time
import unicodedata
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from save_img_to_dir import download_images, make_dir
from process_config_json import get_configs_fb, get_configs_pint, get_configs_insta, get_configs_twit
from db_manager import data_to_db_social


def selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-infobars")
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    # prefs = {"profile.default_content_setting_values.notifications": 2}
    prefs = {"credentials_enable_service": False,
             "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(executable_path=r'C:/seleniumChromeDriver/chromedriver_win32/chromedriver.exe',
                              options=options)
    return driver


def slow_scroll(driver):
    check_height = driver.execute_script("return document.body.scrollHeight;")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(
                lambda driver: driver.execute_script("return document.body.scrollHeight;") > check_height)
            check_height = driver.execute_script("return document.body.scrollHeight;")
        except TimeoutException:
            break


def check_path_exists(driver, path):
    try:
        driver.find_element_by_xpath(path)
    except NoSuchElementException:
        return True
    return False


try:
    from urlparse import urlparse
except ImportError:
    from six.moves.urllib.parse import urlparse


def phantom_noimages():
    from fake_useragent import UserAgent
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    ua = UserAgent()
    # ua.update()
    # https://stackoverflow.com/questions/29916054/change-user-agent-for-selenium-driver
    caps = DesiredCapabilities.PHANTOMJS
    caps["phantomjs.page.settings.userAgent"] = ua.random
    return webdriver.PhantomJS(service_args=["--load-images=no"], desired_capabilities=caps)


def randdelay(a, b):
    time.sleep(random.uniform(a, b))


# may need default encoding type here '.decode('utf8')'
# def u_to_s(uni):
#     return unicodedata.normalize('NFKD', uni).encode('ascii', 'ignore')


def selenium_helper_fb(login, pw, driver):
    email_elem = driver.find_element_by_css_selector("input[name='email']")
    email_elem.send_keys(login)
    password_elem = driver.find_element_by_css_selector("input[name='pass']")
    password_elem.send_keys(pw)
    password_elem.send_keys(Keys.RETURN)
    randdelay(2, 4)


def selenium_helper_pint(login, pw, driver):
    pre_login_button = '//*[@id="__PWS_ROOT__"]/div[1]/div/div/div/div[1]/div[1]/div[2]/div[2]/button'
    driver.find_element_by_xpath(pre_login_button).click()
    email_elem = driver.find_element_by_name('id')
    email_elem.send_keys(login)
    password_elem = driver.find_element_by_name('password')
    password_elem.send_keys(pw)
    password_elem.send_keys(Keys.RETURN)
    randdelay(2, 4)


def selenium_helper_insta(login, pw, driver):
    time.sleep(3)
    username_element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.NAME, "username"))
    )
    username_element.clear()
    username_element.send_keys(login)

    password_element = driver.find_element_by_name("password")
    password_element.clear()
    password_element.send_keys(pw)

    login = driver.find_elements_by_tag_name("button")[1]
    login.click()
    time.sleep(5)
    driver.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/div/div/div/div/button').click()  # not now save passowrd
    time.sleep(5)
    check_path = check_path_exists(driver,
                                   '/html/body/div[5]/div/div/div/div[3]/button[2]')
    # time.sleep(3)
    # WebDriverWait(driver, 10).until(
    #     ec.element_to_be_clickable((By.XPATH, "//button[@class='aOOlW   HoLwm ']"))).click()  # not now notifications
    # if check_path is False:
    #     driver.implicitly_wait(2)
    # WebDriverWait(driver, 10).until(
    #     ec.element_to_be_clickable((By.XPATH, "//button[@class='aOOlW   HoLwm ']"))).click()  # not now notifications
    time.sleep(3)


def selenium_helper_twit(login, pw, driver):
    email_elem = driver.find_element_by_css_selector("input[name='session[username_or_email]']")
    email_elem.send_keys(login)
    password_elem = driver.find_element_by_css_selector("input[name='session[password]']")
    password_elem.send_keys(pw)
    password_elem.send_keys(Keys.RETURN)
    randdelay(2, 4)


class Helper(object):

    def __init__(self, login, pw, driver, site_urls, site_type):
        self.driver = driver
        self.driver.get(site_urls)
        time.sleep(5)
        if site_type == 'facebook':
            selenium_helper_fb(login, pw, driver)
        elif site_type == 'pinterest':
            selenium_helper_pint(login, pw, driver)
        elif site_type == 'instagram':
            selenium_helper_insta(login, pw, driver)
        elif site_type == 'twitter':
            selenium_helper_twit(login, pw, driver)
        randdelay(2, 4)

    # kept these, functions maybe useful later, if not delete
    def get_URLs(self, urlcsv, threshold=500):
        tmp = self.read(urlcsv)
        results = []
        for t in tmp:
            tmp3 = self.run_me(t, threshold)
            results = list(set(results + tmp3))
        random.shuffle(results)
        return results

    def write(self, myfile, mylist):
        tmp = pd.DataFrame(mylist)
        tmp.to_csv(myfile, index=False, header=False)

    def read(self, myfile):
        tmp = pd.read_csv(myfile, header=None).values.tolist()
        tmp2 = []
        for i in range(0, len(tmp)):
            tmp2.append(tmp[i][0])
        return tmp2

    ######################################################

    # TODO threshold 500 and persistence 120 make sure get all images, needs to be optimised depending on scroll length
    def run_me(self, url, site_type, threshold=5, persistence=12, debug=False):
        final_results = []
        previmages = []
        tries = 0
        all_images = []

        try:
            self.driver.get(url)
            while threshold > 0:
                try:
                    results = []

                    images = self.driver.find_elements_by_tag_name("img")
                    if images == previmages:
                        tries += 1
                    else:
                        tries = 0
                    if tries > persistence:
                        if debug:
                            print("Exiting: persistence exceeded")
                        return final_results

                    if site_type == 'instagram':
                        article = WebDriverWait(self.driver, 4).until(
                            ec.presence_of_element_located((By.TAG_NAME, "article")))

                        for image in article.find_elements_by_tag_name("img"):
                            images_2 = image.get_attribute("src")
                            if image.get_attribute("src") not in all_images:
                                results.append(images_2)  # sometimes crashes here
                    else:
                        for i in images:
                            src = i.get_attribute("src")
                            results.append(src)

                    previmages = copy.copy(images)
                    final_results = list(set(final_results + results))
                    time.sleep(3)
                    dummy = self.driver.find_element_by_tag_name('a')

                    if site_type == 'twitter':
                        # TODO - need to play with scroll to get all images, Twitter behaves differently to other sites
                        slow_scroll(self.driver)
                    else:
                        slow_scroll(self.driver)
                        #dummy.send_keys(Keys.PAGE_DOWN)
                        randdelay(1, 2)
                        threshold -= 1

                except StaleElementReferenceException:
                    if debug:
                        print("StaleElementReferenceException")
                    threshold -= 1
        except (socket.error, socket.timeout):
            if debug:
                print("Socket Error")
        except KeyboardInterrupt:
            return final_results
        if debug:
            print("Exiting at end")
        return final_results


def get_url_host_name(urls_list):
    host_url = re.findall('(https?://[A-Za-z_0-9.-]+).*', str(urls_list[0]))
    return host_url


def process_site_images(magazine_name, urls_list, name_host, owners, users, pswrd, site_type, db_creds):
    global h
    host_url_list = get_url_host_name(urls_list)
    driver = selenium_driver()
    count = 0

    credit = ''
    metadata = ''
    host_urls = ''
    img_page_url = ''
    art_date = ''
    art_title = ''

    for magazine_name, urls_list, name_host, owners, users, pswrd, site_type in zip(magazine_name, urls_list, name_host,
                                                                                    owners, users, pswrd, site_type):

        if count != 0:
            urls = h.run_me(urls_list[0], site_type[0])
            dirname = 'imgs2/{}'.format(site_type[0])  # dir name needs to added to config.json
            # make_dir(dirname)
            # download_images(dirname, urls, name_host, site_type[0])
            data_to_db_social(urls, site_type[0], magazine_name, db_creds)
            # send_to_db(urls, magazine_name, owners, credit, metadata, host_urls, img_page_url, site_type, art_date,
            #            art_title, db_creds)

        elif count == 0:
            if host_url_list[0] == 'https://twitter.com':
                twitter_login = str(host_url_list[0]) + '/login'
                h = Helper(users[0], pswrd[0], driver, twitter_login, site_type[0])
                urls = h.run_me(urls_list[0], site_type[0])
                dirname = 'imgs2/{}'.format(site_type[0])  # dir name needs to added to config.json
                # make_dir(dirname)
                # download_images(dirname, urls, name_host, site_type[0])
                data_to_db_social(urls, site_type[0], magazine_name, db_creds)
                #send_to_db(urls, site_type[0], magazine_name, owners, credit, metadata, host_urls,  img_page_url,
                           #art_date, art_title, db_creds)

                count += 1

            else:
                h = Helper(users[0], pswrd[0], driver, host_url_list[0], site_type[0])
                urls = h.run_me(urls_list[0], site_type[0])
                dirname = 'imgs2/{}'.format(site_type[0])  # dir name needs to added to config.json
                # make_dir(dirname)
                # download_images(dirname, urls, name_host, site_type[0])
                data_to_db_social(urls, site_type[0], magazine_name, db_creds)
                #send_to_db(urls, magazine_name, owners, credit, metadata, host_urls, img_page_url, site_type,
                           #art_date, art_title, db_creds)
                count += 1


# for multithread
def call_facebook(site_creds, db_creds):
    magazine_name, urls_list, name_host, owners, users, pswrd, site_type = get_configs_fb(site_creds)
    process_site_images(magazine_name, urls_list, name_host, owners, users, pswrd, site_type, db_creds)


def call_pinterest(site_creds, db_creds):
    magazine_name, urls_list, name_host, owners, users, pswrd, site_type = get_configs_pint(site_creds)
    process_site_images(magazine_name, urls_list, name_host, owners, users, pswrd, site_type, db_creds)


def call_instagram(site_creds, db_creds):
    magazine_name, urls_list, name_host, owners, users, pswrd, site_type = get_configs_insta(site_creds)
    process_site_images(magazine_name, urls_list, name_host, owners, users, pswrd, site_type, db_creds)


def call_twitter(site_creds, db_creds):
    magazine_name, urls_list, name_host, owners, users, pswrd, site_type = get_configs_twit(site_creds)
    process_site_images(magazine_name, urls_list, name_host, owners, users, pswrd, site_type, db_creds)
