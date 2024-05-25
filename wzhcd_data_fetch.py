

# A Wenzhouness parallel corpus fetcher from Wenzhouhua Cidian (《温州话辞典》)
# Author: Weilai Xu

# [Authorised licence needed]

import requests
import os, json, sys
from data.wzhcd_test import response_dict
from utils.config import *
from tool import *
from urllib.parse import unquote, urlencode
import base64
import time
import random
import zhconv
import logging

logging.basicConfig(
    filename='wzhcd_data_fetch.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

logger = logging.getLogger()


def get_target_value(key, dic, tmp_list):
    """
    :param key: 目标key值
    :param dic: JSON数据
    :param tmp_list: 用于存储获取的数据
    :return: list
    """
    if not isinstance(dic, dict) or not isinstance(tmp_list, list):  # 对传入数据进行格式校验
        return 'argv[1] not an dict or argv[-1] not an list '

    if key in dic.keys():
        tmp_list.append(dic[key])  # 传入数据存在则存入tmp_list

    for value in dic.values():  # 传入数据不符合则对其value值进行遍历
        if isinstance(value, dict):
            get_target_value(key, value, tmp_list)  # 传入数据的value值是字典，则直接调用自身
        elif isinstance(value, (list, tuple)):
            _get_value(key, value, tmp_list)  # 传入数据的value值是列表或者元组，则调用_get_value


    return tmp_list

def _get_value(key, val, tmp_list):
    for val_ in val:
        if isinstance(val_, dict):  # 列表中的元素是字典，则调用get_target_value
            get_target_value(key, val_, tmp_list)
        elif isinstance(val_, (list, tuple)):  # 列表中的元素是列表或者元组，则调用自身
            _get_value(key, val_, tmp_list)

    return tmp_list

def download_audio(audio_url, save_path):
    print(audio_url)

    folder = '/'.join(save_path.split('/')[:-1])[1:]
    print(f'folder is: {folder}')
    if not os.path.exists(folder):
        os.makedirs(folder)

    audio_res = requests.get(f"https://wzh.wzlib.cn/{audio_url}", stream=True)
    with open(save_path[1:], 'wb') as f:
        f.write(audio_res.content)
        f.flush()

def process_senses_list(sense_result_list, replaced_word): # key: JsonContent
    if len(sense_result_list) == 0:
        return
    
    processed = []
    for i in sense_result_list:
        for entry in i:
            if entry["AudioUrl"] == "":
                continue
            content = entry["Content"].replace('～', replaced_word) # the content includes ~ symbol, which needs to be replaced by the actual word
            print(f'content is: {content}')
            processed.append(f'{content}\t{entry["AudioUrl"][1:]}\n') # remove the first /
            # download_audio(entry["AudioUrl"], entry["AudioUrl"])

    return processed

def process_entry_list(entry_result_list):
    if len(entry_result_list) == 0:
        return
    
    processed = []
    for sense_entry in entry_result_list:
        for entry_dict in sense_entry:
            entry_name = entry_dict['EntryName']
            for entry in entry_dict['JsonContent']:
                if entry["AudioUrl"] == "":
                    continue
                content = entry["Content"].replace('～', entry_name)
                print(f'content is: {content}')
                processed.append(f'{content}\t{entry["AudioUrl"][1:]}\n')
                # download_audio(entry["AudioUrl"], entry["AudioUrl"])         

    return processed

def fetch_more_entry(WordHeadCode):
    url = "https://wzh.wzlib.cn/HttpApi/DbWord/GetEntry"
    data = {
        "WordHeadCode": WordHeadCode
    }

    response = requests.post(url, data=data)
    if response.status_code != 200:
        logger.error(f'Error: {response.status_code}')
        return
    
    response_dict = response.json()

    MoreEntry_list = [response_dict['Data']]
    parallel = process_entry_list(MoreEntry_list)

    return parallel, response_dict["Data"]

def fetch_wzhcd_data(wordName):
    url = "https://wzh.wzlib.cn/HttpApi/DbWord/GetWordDetail"
    data = {
        "userID": UserID[0],
        "wordName": wordName,
    }

    response = requests.post(url, data=data)
    if response.status_code != 200:
        logger.error(f'Error: {response.status_code}')
        return

    response_dict = response.json()
    if response_dict['Result'] == False:
        logger.error(f'Error: {response_dict["Info"]}, Word: {wordName}')
        return

    SensesDetail_list = get_target_value("SensesDetail", response_dict, []) 
    SensesDetail_dict = {"SensesDetail": SensesDetail_list}
    JsonContent_dict = get_target_value("JsonContent", SensesDetail_dict, [])
    # print(f'json content: {JsonContent_dict}')
    parallel = process_senses_list(JsonContent_dict, replaced_word=wordName) # the replaced word is the wordName

    # EntryDetail_list = get_target_value("EntryDetail", response_dict, [])
    # # print(f'entry detail list: {EntryDetail_list}')
    # parallel += process_entry_list(EntryDetail_list)

    # if ShowMoreBtn is True, fetch more entries
    WordHeadDetail = response_dict["Data"]["WordHeadDetail"]
    for entry_dict in WordHeadDetail:
        if entry_dict["ShowMoreBtn"] == True:
            WordHeadCode = entry_dict["WordHeadCode"]
            print(f'WordHeadCode: {WordHeadCode}')
            more_parallel, more_entry_dict = fetch_more_entry(WordHeadCode)
            if more_parallel is not None:
                parallel += more_parallel
        else:
            EntryDetail_list = get_target_value("EntryDetail", entry_dict, [])
            parallel += process_entry_list(EntryDetail_list)
            more_entry_dict = None

    return parallel, response_dict["Data"], more_entry_dict # (text, audio_url) pairs

if __name__ == '__main__':

    # wordName_list = ["一", "黄", "狗", "𬷕"]
    # wordName_list = ["狗", "𬷕"]
    # wordName_list = ["一", "狗"]

    with open('wenzhounese.character_04.dict_zhs.yaml', 'r', encoding='utf-8') as fr:
        wordName_list = [line.split('\t')[0] for line in fr.readlines()[21:] if line[0] != '#']

    parallel_list = []
    worddict_list = []
    entrydict_list = []
    for wordName in wordName_list[:10]:
        # print(wordName)
        logger.info(f'Processing word: {wordName} | {char2unicode(wordName)}')

        parallel, word_dict, entry_dict = fetch_wzhcd_data(wordName)
        if parallel is not None:
            parallel_list += parallel
        if word_dict is not None:
            worddict_list.append(word_dict)
        if entry_dict is not None: 
            entrydict_list.append(entry_dict)
        pause_time = random.randint(1, 5) 
        time.sleep(pause_time)
    
    with open('wzhcd_corpus_6', 'w', encoding='utf-8') as f:
        f.writelines(parallel_list)
        logger.info(f'the number of parallel sentences: {len(parallel_list)}')
    
    with open('data/original_dict/wzhcd_worddict.json', 'w', encoding='utf-8') as f, open('data/original_dict/wzhcd_entrydict.json', 'w', encoding='utf-8') as f2:
        json.dump(worddict_list, f, ensure_ascii=False)
        json.dump(entrydict_list, f2, ensure_ascii=False)

