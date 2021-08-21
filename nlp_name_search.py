import spacy
import numpy as np
import pandas as pd
from prettytable import PrettyTable

from db_manager import get_nlp_data, data_to_db_nlp


def tidy_up_caption(dataset):
    # remove images with no captions
    pos = []
    num = 0

    for count in range(0, len(dataset)):
        # print(count)
        dataset.Caption[count] = str(dataset.Caption[count])
        if dataset.Caption[count] == 'nan':
            # print('yes')
            pos = np.append(pos, count)
            num = num + 1

    for count2 in range(0, len(pos)):
        counter = int(pos[count2])
        # print(counter)
        dataset = dataset.drop([counter])

        # shorten url address for jpg
    for count in range(0, len(dataset)):
        a_string = (dataset.iloc[count]['URL'])
        split_string = (a_string.split("?", 1))
        substring = split_string
        # print(substring[0])
        dataset.URL[count] = substring[0]

    return dataset


def contains_word(s, w):
    # search for specified words in a string
    return (' ' + w + ' ') in (' ' + s + ' ')


def inspect_caption(dataset):
    for count in range(0, len(dataset)):
        a_string = (dataset.iloc[count]['Caption'])
        if contains_word(a_string, 'Photographer:') or contains_word(a_string, 'Photography:') or contains_word(
                a_string, 'Photo:') or contains_word(a_string, 'Artwork') or contains_word(a_string,
                                                                                           'etchings') or contains_word(
            a_string, 'Painting'):
            count = count + 0
        else:
            dataset.iloc[count]['Caption'] = "unknown"
    return dataset


def slice_caption(dataset):
    # slice the string after specified word
    L = []
    M = []

    for count in range(0, len(dataset)):
        a_string = (dataset.iloc[count]['Caption'])
        a_URL = (dataset.iloc[count]['URL'])
        if contains_word(a_string, 'Photography:'):
            split_string = (a_string.split("Photography:", 1))
            substring = split_string[-1]
            L.append(split_string[-1])
            M.append(a_URL)
        elif contains_word(a_string, 'Photographer:'):
            split_string = (a_string.split("Photographer:", 1))
            substring = split_string[-1]
            L.append(substring)
            M.append(a_URL)
        elif contains_word(a_string, 'Photo:'):
            split_string = (a_string.split("Photo:", 1))
            substring = split_string[-1]
            L.append(substring)
            M.append(a_URL)
        elif contains_word(a_string, 'Artwork'):
            split_string = (a_string.split("Artwork", 1))
            substring = split_string[-1]
            L.append(substring)
            M.append(a_URL)
        elif contains_word(a_string, 'etchings'):
            split_string = (a_string.split("etchings", 1))
            substring = split_string[-1]
            L.append(substring)
            M.append(a_URL)
        elif contains_word(a_string, 'painting'):
            split_string = (a_string.split("painting", 1))
            substring = split_string[-1]
            L.append(substring)
            M.append(a_URL)
        elif contains_word(a_string, 'artwotks'):
            split_string = (a_string.split("artworks", 1))
            substring = split_string[-1]
            L.append(substring)
            M.append(a_URL)
        else:
            count = count + 0

    df1 = pd.DataFrame(L, columns=['Caption'])
    df2 = pd.DataFrame(M, columns=['URL'])
    df = df1.join(df2)
    return df


def get_names(df):
    # identify names in sliced captions and store with associated URL
    nlp = spacy.load("en_core_web_sm")
    table = PrettyTable(['Text', 'Lemma', 'POS', 'Tag', 'Dep', 'Shape', 'is alpha', 'is stop'])
    credit = []
    N = []
    O = []
    P = []
    counter = 0

    for count in range(0, len(df)):

        # for count in range(0,3):
        caption = (df.iloc[count]['Caption'])

        url = (df.iloc[count]['URL'])
        N.append(url)
        doc = nlp(caption)

        for token in doc:
            l = (token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
                 token.shape_, token.is_alpha, token.is_stop)
            table.add_row(l)
            if token.pos_ == 'PROPN':
                credit.append(token.text)

        O.append(credit[counter])
        counter = counter + 1
        P.append(credit[counter])
        #counter = len(credit)

    df3 = pd.DataFrame(N, columns=['URL'])
    df4 = pd.DataFrame(O, columns=['First Name'])
    df5 = pd.DataFrame(P, columns=['Surname'])
    df6 = df3.join(df4).join(df5)
    return df6


def main(db_creds):
    dataset1 = get_nlp_data(db_creds)
    dataset2 = tidy_up_caption(dataset1)
    dataset3 = inspect_caption(dataset2)
    df_slice_caption = slice_caption(dataset3)
    data = get_names(df_slice_caption)  # only returns 29 rows due to hard code
    fname = []
    lname = []

    for index, row in data.iterrows():
        fname.append(row['First Name'])
        lname.append(row['Surname'])

    data_to_db_nlp(fname, lname, db_creds)
