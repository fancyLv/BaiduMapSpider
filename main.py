# -*- coding:utf-8 -*-
import sqlite3
import traceback
from functools import partial
from multiprocessing import Pool, cpu_count

import requests

from location import isInBound, get_boundaries


def get_task_list(corner, delta_y=0.05, delta_x=0.05):
    '''
    将大矩形区域划分为长delta_x,宽为delta_y的小矩形
    :param corner:
    :param delta_y:
    :param delta_x:
    :return:
    '''
    task_list = []
    j = 0
    while True:
        loc1_y = float(corner['lower_left_corner']['lat']) + j * delta_y
        if loc1_y >= float(corner['upper_right_corner']['lat']):
            break
        if float(corner['lower_left_corner']['lat']) + (j + 1) * delta_y > float(corner['upper_right_corner']['lat']):
            loc2_y = float(corner['upper_right_corner']['lat'])
        else:
            loc2_y = float(corner['lower_left_corner']['lat']) + (j + 1) * delta_y
        i = 0
        while True:
            loc1_x = float(corner['lower_left_corner']['lng']) + i * delta_x
            if loc1_x >= float(corner['upper_right_corner']['lng']):
                break
            if float(corner['lower_left_corner']['lng']) + (i + 1) * delta_x > float(
                    corner['upper_right_corner']['lng']):
                loc2_x = float(corner['upper_right_corner']['lng'])
            else:
                loc2_x = float(corner['lower_left_corner']['lng']) + (i + 1) * delta_x
            bounds = (loc1_y, loc1_x, loc2_y, loc2_x)
            task_list.append(bounds)
            i += 1
        j += 1
    return task_list


def get_data(bounds, keyword, boundary):
    # 矩形区域检索
    params = {
        "ak": "xxxxxxxxxxxxx", # 填写秘钥
        "bounds": "%f,%f,%f,%f" % tuple(bounds),
        "output": "json",
        "page_num": 0,
        "page_size": 20,
        "query": keyword
    }
    url = "http://api.map.baidu.com/place/v2/search"
    while True:
        req = requests.get(url, params=params)
        req.encoding = "utf-8"
        if not req.text:
            continue
        json_data = req.json()
        results = json_data.get('results')
        if results:
            data = []
            for result in results:
                name = result.get('name')
                location = result.get('location')
                if location:
                    lat = location.get('lat')
                    lng = location.get('lng')
                    point = {'lat': lat, 'lng': lng}
                else:
                    continue
                address = result.get('address')
                telephone = result.get('telephone', '')
                uid = result.get('uid')
                print name
                # 保存区域内检索结果
                if isInBound(point, boundary):
                    data.append((name, address, telephone, lng, lat, uid, keyword))
            if data:
                save_data(data)
            params['page_num'] += 1
        else:
            break


def create_db():
    try:
        with sqlite3.connect('Map.db') as conn:
            print("Opened database successfully")
            sql = """CREATE TABLE IF NOT EXISTS baidumap
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name NTEXT NOT NULL,
                       address NTEXT,
                       telephone TEXT,
                       longitude REAL,
                       latitude REAL,
                       uid TEXT,
                       keyword NTEXT);
                    """
            conn.execute(sql)
            print("create table successfully")
    except sqlite3.Error as e:
        print "sqlite3 Error:", e
        traceback.print_exc()


def save_data(data):
    try:
        with sqlite3.connect('Map.db') as conn:
            sql = "INSERT INTO baidumap (name, address, telephone, longitude, latitude, uid, keyword) VALUES (?,?,?,?,?,?,?)"
            conn.executemany(sql, data)
            conn.commit()
    except sqlite3.Error as e:
        print "sqlite3 Error:", e
        traceback.print_exc()


def main(keyword, city, delta_y=0.05, delta_x=0.05):
    create_db()
    boundaries = get_boundaries(city)
    corner = boundaries['corner']
    boundary = boundaries['boundary']
    task_list = get_task_list(corner, delta_y, delta_x)
    task_func = partial(get_data, keyword=keyword, boundary=boundary)
    pool = Pool(cpu_count())
    pool.map(task_func, task_list)


if __name__ == '__main__':
    main(u'美食', u'广东省')
