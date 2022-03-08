import argparse
import json
import sys
from pathlib import Path

import cchardet as chardet

ext_type_map = {
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.gif': 'image',
    '.webp': 'image',

    '.mp3': 'sound',
    '.wav': 'sound',

    '.json': 'json',

    '.fnt': 'font',

    '.pvr': 'pvr',

    '.exml': 'text',
    '.txt': 'text',

    '.ttf': 'ttf',

    '.xml': 'xml',
}


def get_type(p_suffix):
    if p_suffix in ext_type_map:
        return ext_type_map[p_suffix]
    else:
        return 'bin'


def get_encoding(p_file):
    with open(p_file, 'rb') as f:
        msg = f.read()
        result = chardet.detect(msg)['encoding']
        return result


def run(p_work, p_fgui_dir, p_clean=True):
    path_res = Path(p_work, 'resource')
    path_fgui = path_res / p_fgui_dir
    if not path_res.exists():
        print('指定目录不存在，程序退出')
        return

    path_default = path_res / 'ximi.res.json'
    default_encoding = get_encoding(str(path_default))

    if not path_default.exists():
        print('res.json不存在，程序退出')
        return

    print('找到资源路径 = ' + str(path_res.resolve()))

    str_json = path_default.read_text(encoding=default_encoding)
    obj_default = json.loads(str_json)

    del_flag = False  # default删除标识
    # 删除不存在的资源
    url_map = {}
    key_map = {}
    new_list = []
    for v in obj_default['resources']:
        path_obj = path_res / v['url']
        if path_obj.exists():
            new_list.append(v)
            url_map[v['url']] = v
            key_map[v['name']] = v
    if len(obj_default['resources']) != len(new_list):
        obj_default['resources'] = new_list
        del_flag = True

    add_flag = False  # default新增标识
    list_file = sorted(path_res.rglob('*.*'))
    for v in list_file:
        # 计算相对路径
        if v.samefile(path_default):
            continue
        if v.parent.samefile(path_fgui):  # 排除fgui的生成目录
            continue
        url = v.relative_to(path_res).as_posix()  # 计算相对路径
        if url in url_map:
            continue
        else:
            # print(url)
            name = url.replace('/', '_').replace('.', '_')
            t_type = get_type(v.suffix)
            obj = {'url': url, 'name': name, 'type': t_type}
            obj_default['resources'].append(obj)
            url_map[url] = obj
            key_map[name] = obj
            add_flag = True

    if add_flag or del_flag:
        if del_flag:
            groups = obj_default['groups']
            for v in groups:
                keys = v['keys'].split(',')
                new_keys = []
                for k in keys:
                    if k in key_map:
                        new_keys.append(k)
                if len(keys) != len(new_keys):
                    v['keys'] = ','.join(new_keys)
        str_result = json.dumps(obj_default, indent=4, ensure_ascii=False)
        # str_result = str_result.replace('    ', '\t')  # 把四个空格转换成\t
        path_default.write_text(str_result, encoding=default_encoding)
        print('{0}文件修改成功'.format(path_default.name))
    else:
        print('资源无变化，{0}无需修改'.format(path_default.name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='帮助信息')
    parser.add_argument('--work', type=str, default='', help='代码工程目录')
    parser.add_argument('--ui', type=str, default='', help='fgui文件生成的目录（相对于resource的路径）')

    args = parser.parse_args()

    if not args.work:
        print('[ERROR]请指定项目工程根目录')
        sys.exit()

    if not args.ui:
        print('[ERROR]请指定fgui文件生成的目录（相对于resource的路径）')
        sys.exit()

    work_path = args.work
    fgui_dir = args.ui

    # work_path = 'D:/work_ximi/client/trunk/clientGame'
    # fgui_dir = 'ui'
    run(work_path, fgui_dir)
