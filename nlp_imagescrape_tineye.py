import spacy
import numpy as np
import pandas as pd
from prettytable import PrettyTable
import re
import string

from db_manager import add_nlp_reverse_search_results


def caption_pathways():
    # Define pathways and load captions
    # caption_input_path = '.'
    # caption_output_path = '.'
    header_list = ["Item_num", "Img_ID", "num_res", "tineye_filename", "tin_text"]
    dataset = pd.read_csv("tineye_dict_data - tineye_dict_data.csv", names=header_list)
    dataset = pd.DataFrame(dataset)
    return dataset


def get_URL_results(dataset, num_set):
    # remove images with no results
    pos = []
    num = 0

    for count in range(0, num_set):
        if dataset.num_res[count] == '[None]':
            pos = np.append(pos, count)
            num = num + 1

    pos_num_set = len(pos)
    for count2 in range(0, pos_num_set):
        counter = int(pos[count2])
        dataset = dataset.drop([counter])
    new_num_set = len(dataset)

    return (dataset, new_num_set)


# def tidy_up_URL1(dataset1, new_num_set):
#     # shorten url address for jpg
#     dataset1 = pd.DataFrame(dataset1)
#     dataset1 = dataset1.reset_index(drop=True)
#     for count in range(1, new_num_set):
#         a_string = (dataset1.Img_ID[count])
#         split_string = (a_string.split(".", 1))
#         substring = split_string
#         dataset1.Img_ID[count] = substring[0]
#
#     return dataset1
#
#
# def tidy_up_URL2(dataset2, new_num_set):
#     # shorten url address for jpg
#     dataset2a = pd.DataFrame(dataset2)
#     for count in range(1, new_num_set):
#         a_string = (dataset2.Img_ID[count])
#         print(a_string)
#         split_string = (a_string.split("a/", 1))
#         substring = split_string
#         dataset2.Img_ID[count] = substring[1]
#
#     return dataset2
#
#
# def tidy_up_num_res1(dataset3, new_num_set):
#     # shorten url address for jpg
#     dataset3 = pd.DataFrame(dataset3)
#     for count in range(1, new_num_set):
#         a_string = (dataset3.num_res[count])
#         split_string = (a_string.split(" r", 1))
#         print(split_string)
#         substring = split_string
#         dataset3.num_res[count] = substring[0]
#
#     return dataset3
#
#
# def tidy_up_num_res2(dataset4, new_num_set):
#     # shorten url address for jpg
#     dataset4 = pd.DataFrame(dataset4)
#     for count in range(1, new_num_set):
#         a_string = (dataset4.num_res[count])
#         split_string = (a_string.split("' ", 1))
#         substring = split_string
#         dataset4.num_res[count] = (substring[1])
#
#     dataset4 = pd.DataFrame(dataset4).astype(str)
#     dataset4.drop([0])
#
#     return dataset4


def select_info(substring_text):
    # identify names in sliced captions and store with associated URL
    nlp = spacy.load("en_core_web_sm")
    table = PrettyTable(['Text', 'Lemma', 'POS', 'Tag', 'Dep', 'Shape', 'is alpha', 'is stop'])
    credit = []

    doc = nlp(substring_text)

    for token in doc:
        l = (token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
             token.shape_, token.is_alpha, token.is_stop)
        table.add_row(l)

        if token.pos_ == 'PROPN':
            credit.append(token.text)

    return (credit)



def listToString(s):
    # initialize an empty string
    str1 = " "

    # return string
    return (str1.join(s))



def get_artist_artwork(info):
    a_string = info
    pos = []
    O = []
    num = 0
    new = []
    my_punct = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '.',
                '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_',
                '`', '{', '|', '}', '~', '»', '«', '“', '”', "-"]
    num_splits = sum(map(lambda x: ',' in x, a_string))
    num_splits_plus1 = num_splits + 1
    split_string = (a_string.split(",", num_splits))

    for count in range(0, num_splits_plus1):
        substring = split_string[count]
        punct_pattern = re.compile("[" + re.escape("".join(my_punct)) + "]")
        text = re.sub(punct_pattern, " ", substring)
        art_name = select_info(text)
        if O == [] and art_name != []:
            O.append(art_name)
        elif O != [] and art_name != []:
            for counter in range(0, len(art_name)):
                for counter2 in range(0, len(O)):
                    if art_name[counter] != O[counter2]:
                        new.append(art_name[counter])
        O.append(new)

    for count in range(1, len(O)):
        O = O + O[count]
        details = list(dict.fromkeys(O[0]))

    art_name = (listToString(details))
    return art_name


def get_artist_art(dataset5, new_num_set):
    # shorten url address for jpg
    dataset5 = pd.DataFrame(dataset5)
    dataset5 = pd.DataFrame(dataset5).assign(Art_details='')
    for count in range(1, new_num_set):
        # for count in range(1, 6):
        info = dataset5.tineye_filename[count]
        art_name = get_artist_artwork(info)
        dataset5.Art_details[count] = art_name

    return dataset5


def tidy_up_all(dataset6):
    dataset6 = dataset6[['Img_ID', 'Art_details']]
    for count in range(1, len(dataset6)):
        if dataset6.Art_details[count] == '':
            dataset6.Art_details[count] = 'unknown'
    return (dataset6)


def results(dataset7):
    # Write results to file
    dataset7.to_csv('NLP_file2.csv')
    return ()


if __name__ == "__main__":
    dataset = caption_pathways()
    num_set = len(dataset)
    dataset1, new_num_set = get_URL_results(dataset, num_set)
    #dataset2 = tidy_up_URL1(dataset1, new_num_set)
    dataset3 = tidy_up_URL2(dataset1, new_num_set)
    # dataset4 = tidy_up_num_res1(dataset3, new_num_set)
    # dataset5 = tidy_up_num_res2(dataset4, new_num_set)
    # dataset6 = get_artist_art(dataset5, new_num_set)
    # dataset7 = tidy_up_all(dataset6)
    #results(dataset7)
    # add_nlp_reverse_search_results(db_creds)

# def main(db_creds):
