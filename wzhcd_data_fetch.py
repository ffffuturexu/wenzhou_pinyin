

# A Wenzhouness parallel corpus fetcher from Wenzhouhua Cidian
# Author: Weilai Xu

# [Authorised licence needed]

import requests
import os, json, sys
from data.wzhcd_test import response_dict
from urllib.parse import unquote, urlencode
import base64


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

if __name__ == '__main__':
    wordName = "黄"
    print(wordName)
    url = "https://wzh.wzlib.cn/HttpApi/DbWord/GetWordDetail"
    data = {
        "userID": "4e1515e588504361837e57829f5cb6cc",
        "wordName": wordName,
    }

    response = requests.post(url, data=data)

    response_dict = response.json()

    SensesDetail_list = get_target_value("SensesDetail", response_dict, []) 
    SensesDetail_dict = {"SensesDetail": SensesDetail_list}
    JsonContent_dict = get_target_value("JsonContent", SensesDetail_dict, [])
    # print(f'json content: {JsonContent_dict}')
    parallel = process_senses_list(JsonContent_dict, replaced_word=wordName) # the replaced word is the wordName

    EntryDetail_list = get_target_value("EntryDetail", response_dict, [])
    # print(f'entry detail list: {EntryDetail_list}')
    parallel += process_entry_list(EntryDetail_list)

    with open('wzhcd_corpus', 'w', encoding='utf-8') as f:
        f.writelines(parallel)

