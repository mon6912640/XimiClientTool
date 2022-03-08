import re
from pathlib import Path

import cchardet as chardet
from typing import List


class VoFind:
    file_path: Path = None
    start_index = 0
    end_index = 0
    find_str = ''
    # 0 Lan.str  1 Lan.rep
    type_str = ''


class VoTs:
    key = ''
    file_pat: Path = None
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
    vo_list = []
    for v in list_file:
        cur_encoding = get_encoding(str(v))
        file_str = v.read_text(encoding=cur_encoding)
        result = find_lan(file_str, 0)
        end_index = result[0]
        if end_index < 0:
            continue
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
                    vo_list.append(vo)
                    pos = i
                    if vo.find_str[0] == '`':
                        print(v, '\n', vo.find_str)
                    break
            result = find_lan(file_str, pos)
            end_index = result[0]
        encoding_set.add(cur_encoding)
    print(encoding_set)


def find_lan(p_str, p_pos):
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
    work_path = 'D:/work_ximi/client/trunk/clientGame'
    run(work_path)
