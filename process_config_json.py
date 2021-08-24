import pymysql


def get_configs_fb(site_creds):
    urls_list = []
    magazine_name = []
    name_host = []
    owners = []
    pswrd = []
    users = []
    site_type = []

    for key, values in site_creds.items():
        urls = values['facebook']['url'].split(" ")
        name = values['facebook']['mag_name'].split(" ")
        owner = values['facebook']['owner'].split(" ")
        password = values['facebook']['pswrd'].split(" ")
        user = values['facebook']['user'].split(" ")

        # added to distinguish between main mag site and their social sites
        sitetype = values['facebook']['s_type'].split(" ")

        for i in urls:
            urls_list.append([i])
            magazine_name.append(name)
            owners.append(owner)
            name_host.append(key)
            pswrd.append(password)
            users.append(user)
            site_type.append(sitetype)

    return magazine_name, urls_list, name_host, owners, users, pswrd, site_type


def get_configs_pint(site_creds):
    urls_list = []
    magazine_name = []
    name_host = []
    owners = []
    pswrd = []
    users = []
    site_type = []

    for key, values in site_creds.items():
        urls = values['pinterest']['url'].split(" ")
        name = values['pinterest']['mag_name'].split(" ")
        owner = values['pinterest']['owner'].split(" ")
        password = values['pinterest']['pswrd'].split(" ")
        user = values['pinterest']['user'].split(" ")

        # added to distinguish between main mag site and their social sites
        sitetype = values['pinterest']['s_type'].split(" ")

        for i in urls:
            urls_list.append([i])
            magazine_name.append(name)
            owners.append(owner)
            name_host.append(key)
            pswrd.append(password)
            users.append(user)
            site_type.append(sitetype)

    return magazine_name, urls_list, name_host, owners, users, pswrd, site_type


def get_configs_insta(site_creds):
    urls_list = []
    magazine_name = []
    name_host = []
    owners = []
    pswrd = []
    users = []
    site_type = []

    for key, values in site_creds.items():
        urls = values['instagram']['url'].split(" ")
        name = values['instagram']['mag_name'].split(" ")
        owner = values['instagram']['owner'].split(" ")
        password = values['instagram']['pswrd'].split(" ")
        user = values['instagram']['user'].split(" ")

        # added to distinguish between main mag site and their social sites
        sitetype = values['instagram']['s_type'].split(" ")

        for i in urls:
            urls_list.append([i])
            magazine_name.append(name)
            owners.append(owner)
            name_host.append(key)
            pswrd.append(password)
            users.append(user)
            site_type.append(sitetype)

    return magazine_name, urls_list, name_host, owners, users, pswrd, site_type


def get_configs_twit(site_creds):
    urls_list = []
    magazine_name = []
    name_host = []
    owners = []
    pswrd = []
    users = []
    site_type = []

    for key, values in site_creds.items():
        urls = values['twitter']['url'].split(" ")
        name = values['twitter']['mag_name'].split(" ")
        owner = values['twitter']['owner'].split(" ")
        password = values['twitter']['pswrd'].split(" ")
        user = values['twitter']['user'].split(" ")

        # added to distinguish between main mag site and their social sites
        sitetype = values['twitter']['s_type'].split(" ")

        for i in urls:
            urls_list.append([i])
            magazine_name.append(name)
            owners.append(owner)
            name_host.append(key)
            pswrd.append(password)
            users.append(user)
            site_type.append(sitetype)

    return magazine_name, urls_list, name_host, owners, users, pswrd, site_type


def get_configs_main(site_creds):
    #global db_creds  # to test connect
    urls_list = []
    magazine_name = []
    name_host = []
    owners = []
    site_type = []

    for key, values in site_creds.items():
        urls = values['main_site']['url'].split(" ")
        name = values['main_site']['mag_name'].split(" ")
        owner = values['main_site']['owner'].split(" ")

        # added to distinguish between main mag site and their social sites
        sitetype = values['main_site']['s_type'].split(" ")

        for i in urls:
            urls_list.append([i])
            magazine_name.append(name)
            owners.append(owner)
            name_host.append(key)
            site_type.append(sitetype)

    #     # db creds
    # for key, values in db_access.items():
    #     db_creds.append(values)

    return magazine_name, urls_list, name_host, owners, site_type


# def db_connect():
#
#     user = db_creds[0]
#     passwd = db_creds[1]
#     host = db_creds[2]
#     database = db_creds[3]
#     conn = pymysql.connect(user=user, passwd=passwd, host=host, database=database)
#     cursor = conn.cursor()
#     return conn, cursor
