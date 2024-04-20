# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

def char2unicode(char):
    return char.encode('unicode_escape').decode()

def unicode2char(unicode):
    return unicode.encode().decode('unicode_escape')

def json2txt(json_file, txt_file):
    with open(json_file, 'r') as f_json, open(txt_file, 'w+', encoding='utf-8') as f_table:
        pinyin_dict = json.load(f_json)
        for char_unicode in pinyin_dict:
            char = unicode2char(char_unicode)
            # print(f'{char_unicode}\t{", ".join(pinyin_dict[char_unicode])} # {char}')
            f_table.write(f'{char_unicode}: {", ".join(pinyin_dict[char_unicode])}\t# {char}\n')


if __name__ == "__main__":
    json2txt('wz_pinyin_json.json', 'wz_pinyin_table.txt')
    print("Done.")