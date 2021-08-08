import os
import datetime
import requests
import shutil


def make_dir(dirname):
    current_path = os.getcwd()
    path = os.path.join(current_path, dirname)
    if not os.path.exists(path):
        os.makedirs(path)


def download_images(dirname, links, name, s_type):
    #print(links)
    length = len(links)
    fmt = '%Y-%m-%d-%H-%M-%S_{name}'
    data_time = datetime.datetime.now().strftime(fmt).format(name=name)

    for index, link in enumerate(links):
        print('Downloading {0} of {1} images'.format(index + 1, length))
        response = requests.get(link, stream=True)
        save_image_to_file(response, dirname, index, name, data_time, s_type)
        del response


def save_image_to_file(image, dirname, suffix, name, datatime, s_type):
    if s_type == "main_site":
        s_type = 'main_site'
    elif s_type == 'pinterest':
        s_type = 'pinterest'
    elif s_type == 'instagram':
        s_type = 'instagram'
    elif s_type == 'twitter':
        s_type = 'twitter'
    elif s_type == 'tumblr':
        s_type = 'tumblr'
    elif s_type == 'vogueLiving_blog':
        s_type = 'vogueLiving_blog'
    elif s_type == 'vogueAust_blog':
        s_type = 'vogueAust_blog'

    with open('{dirname}/{s_type}_{suffix}_{datatime}.jpg'.format(dirname=dirname, s_type=s_type, suffix=suffix,
                                                                  datatime=datatime), 'wb') as out_file:
        shutil.copyfileobj(image.raw, out_file)
