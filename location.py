# -*- coding:utf-8 -*-
import re

import requests

from mercator import mercator_to_lnglat


def get_uid(city):
    url = "http://map.baidu.com/?newmap=1&biz=1&from=webmap&da_par=direct&pcevaname=pc4.1&qt=s&wd=%s&nn=0&ie=utf-8" % city
    req = requests.get(url)
    data = req.json()
    uid = data.get('content').get('uid')
    return uid


def get_boundaries(city):
    '''
    获取区域左下角、右上角坐标及边界坐标
    :param city:行政区划名称
    :return:{
                "corner": {
                    "lower_left_corner": {
                        "lat": 20.123355,
                        "lng": 109.642194
                    },
                    "upper_right_corner": {
                        "lat": 25.522669,
                        "lng": 117.366654
                    }
                },
                "boundary": [
                    {
                        "lat": 24.175532,
                        "lng": 116.99678
                    },
                    ...
                ]
            }
    '''
    uid = get_uid(city)
    url = 'http://map.baidu.com/?newmap=1&reqflag=pcmap&biz=1&from=webmap&da_par=direct&pcevaname=pc4.1&qt=ext&num=1000&l=10&uid=%s&tn=B_NORMAL_MAP&nn=0&ie=utf-8' % uid
    boundaries = {}
    req = requests.get(url)
    data = req.json()
    content = data.get('content')
    if content:
        geo = content['geo']
        location = geo.split('|')
        corners = location[1].split(';')
        corner = {}
        corner['lower_left_corner'] = mercator_to_lnglat(
            {'lng': float(corners[0].split(',')[0]), 'lat': float(corners[0].split(',')[1])})
        corner['upper_right_corner'] = mercator_to_lnglat(
            {'lng': float(corners[1].split(',')[0]), 'lat': float(corners[1].split(',')[1])})

        boundary = re.split('[,;]', location[2].strip(';'))
        points = []
        for i in range(0, len(boundary) - 2, 2):
            point = mercator_to_lnglat({'lng': float(boundary[i]), 'lat': float(boundary[i + 1])})
            points.append(point)

        boundaries['corner'] = corner
        boundaries['boundary'] = points

        return boundaries


def isInBound(point, boundary):
    '''
    判断点是否在多边形内部
    :param point:点坐标
    :param boundary:多边形边界坐标
    :return:boolean
    '''
    result = False
    for i in range(len(boundary) - 1):
        if i == len(boundary) - 1:
            j = 0
        else:
            j = i + 1
        if (boundary[i]['lat'] > point['lat']) != (boundary[j]['lat'] > point['lat']):
            if point['lng'] < ((boundary[j]['lng'] - boundary[i]['lng']) * (point['lat'] - boundary[i]['lat']) / (
                        boundary[j]['lat'] - boundary[i]['lat']) + boundary[i]['lng']):
                result = not result
    return result


if __name__ == '__main__':
    boundaries = get_boundaries(u'广东省')
    boundary = boundaries['boundary']
    print boundaries
    point = {'lat': 22.597639, 'lng': 114.043115}
    print isInBound(point, boundary)
