import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

import cchardet as chardet
from openpyxl import Workbook

key_map = {}


class VoFind:
    file_path: Path = None
    start_index = 0
    end_index = 0
    find_str = ''
    # 0 Lan.str  1 Lan.rep
    type_str = ''
    is_special = False

    out_str = ''

    def get_key(self):
        key = ''
        strip_str = self.find_str.lstrip().rstrip()  # 去除左右两边的空白字符
        if self.out_str:  # 先处理替换修改过的，这里已经变成rep的形式
            obj = re.search(r'[\'\"`](.+)[\'\"`],', self.out_str)
        elif self.type_str == 'rep':
            obj = re.search(r'[\'\"`](.+)[\'\"`],', strip_str)
        elif self.type_str == 'str':
            obj = re.search(r'[\'\"`](.+)[\'\"`]', strip_str)
        else:
            obj = None
        if obj:
            key = obj.group(1)
            key_map[key] = ''
        # print('---', strip_str, key)


class VoTs:
    url = ''
    file_path: Path = None
    code_str = ''
    has_special = False
    list_find: List[VoFind] = None

    def __init__(self):
        self.list_find = []


def get_encoding(p_file):
    with open(p_file, 'rb') as f:
        msg = f.read()
        result = chardet.detect(msg)['encoding']
        return result


def run(p_work):
    path_src = Path(p_work, 'src')
    list_file = sorted(path_src.rglob('*.ts'))
    ts_count = len(list_file)
    print('共有{0}个ts文件'.format(ts_count))
    encoding_set = set()
    modify_ts_list = []
    for v in list_file:
        if v.name == 'Lan.ts':
            continue
        cur_encoding = get_encoding(str(v))
        file_str = v.read_text(encoding=cur_encoding)
        result = find_lan(file_str, 0)
        end_index = result[0]
        if end_index < 0:
            continue
        vots = VoTs()
        vots.url = str(v)
        vots.file_path = v
        vots.code_str = file_str
        len_str = len(file_str)
        pos = 0
        # print(v)
        while end_index > -1:
            # print(v, file_str[end_index])
            bk = False
            # 匹配函数内容
            for i in range(end_index, len_str):
                if file_str[i] == '(' and bk is False:
                    bk = True
                elif file_str[i] == ')' and bk is True:
                    bk = False
                elif file_str[i] == ')' and bk is False:
                    vo = VoFind()
                    vo.file_path = v
                    vo.find_str = file_str[end_index:i]
                    vo.type_str = result[1]
                    vo.start_index = end_index
                    vo.end_index = i
                    vots.list_find.append(vo)
                    pos = i

                    # 把${xxx}替换成rep那样字符串+数组的形式
                    if '${' in vo.find_str:
                        vo.is_special = True
                        vots.has_special = True
                        params = []

                        def rpl_func(ma):
                            s2 = ma.group(2)
                            params.append(s2)
                            return '{' + str(len(params) - 1) + '}'

                        strip_str = vo.find_str.lstrip().rstrip()  # 去除左右两边的空字符
                        out_str = re.sub(r'(\$){([^}]+)}', rpl_func, strip_str, flags=re.M)
                        out_str = out_str + ', [{0}]'.format(', '.join(params))
                        out_str = out_str.replace('`', '"')
                        # print(v)
                        # print(vo.find_str)
                        # print(params)
                        # print(out_str)
                        vo.out_str = out_str
                    vo.get_key()
                    break
            result = find_lan(file_str, pos)
            end_index = result[0]
        if vots.has_special:
            modify_ts_list.append(vots)
        encoding_set.add(cur_encoding)
    # print(encoding_set)
    for vts in modify_ts_list:
        for vfind in vts.list_find:
            if vfind.is_special:
                # 把 str(`xxxx${xxxx}`替换成rep("xxxx{0}", [xxxx]
                old_str = vfind.type_str + '(' + vfind.find_str
                new_str = 'rep(' + vfind.out_str
                vts.code_str = vts.code_str.replace(old_str, new_str)
        vts.file_path.write_text(vts.code_str, encoding='utf-8')
    json_str = json.dumps(key_map, indent=4, ensure_ascii=False)
    # print(json_str)
    path_json = Path(p_work, 'resource', 'lan', 'lan_cn.json')
    # print(path_json)
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json_str, encoding='utf-8')
    print('...成功生成语言配置 {0}'.format(path_json))


def find_lan(p_str, p_pos):
    # 查找出Lan.str( 或是 Lan.rep(
    pattern = re.compile(r'\WLan\.(str|rep)\(')
    end_index = -1
    type_str = ''
    obj = pattern.search(p_str, p_pos)
    if obj:
        span = obj.span()
        type_str = obj.group(1)
        end_index = span[1]
    return [end_index, type_str]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='帮助信息')
    parser.add_argument('--work', type=str, default='', help='代码工程目录')

    args = parser.parse_args()

    debug = True
    if debug:
        work_path = 'D:/work_ximi/client/trunk/clientGame'
    else:
        if not args.work:
            print('[ERROR]请指定项目工程根目录')
            sys.exit()
        work_path = args.work

    run(work_path)

    wb = Workbook()
    sheet = wb.active
    sheet['A1'] = 'key'
    sheet['B1'] = 'value'
    # 设置单元格宽度
    sheet.column_dimensions['A'].width = 50
    sheet.column_dimensions['B'].width = 50

    row = 1
    for k in key_map:
        row += 1
        sheet['A' + str(row)] = k
        sheet['B' + str(row)] = key_map[k]

    path_excel = Path('./excel/test.xlsx')
    path_excel.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path_excel)
