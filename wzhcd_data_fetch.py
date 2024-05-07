# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# A Wenzhouness parallel corpus fetcher from Wenzhouhua Cidian
# Author: Weilai Xu

# [Authorised licence needed]

import requests
import os, json, sys
# from data.wzhcd_test import response_dict


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

def process_list(result_list):
    if len(result_list) == 0:
        return
    
    processed = []
    for i in result_list:
        for entry in i:
            if entry["AudioUrl"] == "":
                continue
            print(f'content is: {entry["Content"]}')
            processed.append(f'{entry["Content"]}\t{entry["AudioUrl"]}\n') # the content includes ~ symbol, which needs to be replaced by the actual word
            download_audio(entry["AudioUrl"], entry["AudioUrl"])

    return processed

if __name__ == '__main__':
    url = "https://wzh.wzlib.cn/HttpApi/DbWord/GetWordDetail"
    wordName = "一"
    headers = {
        "userID": "4e1515e588504361837e57829f5cb6cc",
        "wordName": wordName,
    }

    response = requests.post(url, headers=headers)

    response_dict = response.json()

    temp_list = []
    target_key = "JsonContent"

    result_list = get_target_value(target_key, response_dict, temp_list)
    print(f'length of result_list: {len(result_list)}')

    parallel = process_list(result_list)
    with open('wzhcd_corpus', 'a', encoding='utf-8') as f:
        f.writelines(parallel)

