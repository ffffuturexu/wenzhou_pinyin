# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# A Wenzhouness pinyin OCR program
# Author: Weilai Xu
# 
# This program is a Wenzhouness pinyin OCR program. 
# It takes a picture of Wenzhouness pinyin text as input and outputs the text in Wenzhouness pinyin.
# Pipeline:
# 1. Input: a sentence in Wenzhouness characters, e.g. "该个男个大概廿几岁", a.k.a. "这个男的大概二十几岁" in Mandarin.
# 2. Iterate through the sentence and detect each character.
# 3. Query the character in "https://wu-chinese.com/minidict/"
# 4. Get the pinyin image of the character.
# 5. Upscale the pinyin image to a fixed size using simple nearestNeighboor interpolation.
# 6. OCR the upscaled image using easyocr.
# 7. Output: the pinyin of the character, e.g. "ke" for "该".

import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
import easyocr
import shutil
import pandas as pd
import sys, os, json
from utils.my_upscaler import *
from utils.config import *
from tool import *

def get_request_table(char):
    url = f"https://wu-chinese.com/minidict/search.php?searchkey={char}&searchlang=uentseu&category="
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to get the table for character: {char}")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find('table', attrs={'class':'results'})
    except:
        print(f"Failed to get the table for character: {char}")
        table = None
    return table

def parse_table(table, char):
    # Parse the table
    l = []
    table_rows = table.find_all('tr')
    for tr in table_rows[1:]: # Skip the header
        tds = tr.find_all('td')
        row = []
        for td in tds:
            if td.img:
                if 'colspan' in td.attrs:
                    row.append(td.img['src'])
                row.append(td.img['src'])
            else:
                row.append(td.text)
        # row = [i.text if not i.img else i.img.get('src') for i in td]
        l.append(row)

    result_df = pd.DataFrame(l, columns=['#', 'fanti', 'jianti', 'pinyin', 'shengdiao', 'beizhu'])
    # shengdiao = result_df['shengdiao'][0].split('/')[1].strip()

    # process the heteronyms
    for row in result_df.iterrows():
        img_url = base_url + row[1]['pinyin']
        img_response = requests.get(img_url, stream=True)
        img_path = f'{pinyin_img_ori_path}{char}_{row[1]["#"]}_{row[1]["shengdiao"].split("/")[1].strip()}.png'
        with open(img_path, 'wb') as out_file:
            img_response.raw.decode_content = True
            shutil.copyfileobj(img_response.raw, out_file)
        del img_response

def upscale_image(char, scale_percent=2, method="nearest"):
    img_path = f'{pinyin_img_ori_path}{char}.png'
    upscaled_path = upscale(img_path, scale_percent, method) # return the file name of the upscaled image
    return upscaled_path

def ocr_pinyin_image(upscaled_path):
    # upscaled_path = f'{pinyin_img_upscaled_path}{upscaled_name}'
    # print(upscaled_path)
    # sys.exit(0)
    reader = easyocr.Reader(['en'])
    result = reader.readtext(cv2.imdecode(np.fromfile(upscaled_path, dtype=np.uint8), 1)) # [position, pinyin, confidence]
    return result

def parse_ocr_result(char, ocr_result, shengdiao):
    pinyin = ocr_result[0][1] 
    char_unicode = char2unicode(char)
    print(f"Character: {char}, Pinyin: {pinyin}, Shengdiao: {shengdiao}, Unicode: {char_unicode}")
    if char_unicode not in wz_pinyin_dict:
        wz_pinyin_dict[char_unicode] = [f"{pinyin}{shengdiao}"]
    else:
        wz_pinyin_dict[char_unicode].append(f"{pinyin}{shengdiao}")

def upscale_and_ocr():
    for img_path in os.listdir(pinyin_img_ori_path):
        # print(f"Processing image: {img_path}")
        char = img_path.split('_')[0]
        shengdiao = img_path.split('_')[-1].split('.')[0]
        upscaled_path = upscale_image(img_path.split('.')[0])
        ocr_result = ocr_pinyin_image(upscaled_path)
        parse_ocr_result(char, ocr_result, shengdiao)

def main(input_sentence):
    char_list = "".join([w for w in input_sentence if w != " " and w not in zh_punts])
    for char in char_list[:4]:
        char_unicode = char2unicode(char)
        if char_unicode in wz_pinyin_dict:
            print(f"Unicode: {char_unicode}, Character: {char}, Pinyin: {wz_pinyin_dict[char_unicode]}, already in the dictionary. Skip.")
            continue
        print(f"Processing character: {char}")
        table = get_request_table(char)
        parse_table(table, char)
        
    # after getting all the pinyin images, upscale and OCR them
    upscale_and_ocr() 
    
    
if __name__ == "__main__":
    # Input
    with open('wz_pinyin_json.json', 'w+') as f_json:
        if f_json.read() == "":
            wz_pinyin_dict = {}
        else:
            wz_pinyin_dict = json.load(f_json)

        input_sentence = "该 个 男 个 大概 廿 几 岁 ， 米 七 下 长 ， 人 有 零儿 壮 ， 左 面 个 手 肢 肚 里 有 针 起 个 人儿 在 柢 ， 形状 好比 雕鹰 一色 。 该 个 人 身 里 随 何乜 证件 阿 冇 带 ， 警察 希望 有 晓得 个 人 及时 伉 公安 部门 联系 。"
        main(input_sentence)

        json.dump(wz_pinyin_dict, f_json)
        print("Done.")
    
    