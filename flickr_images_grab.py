#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Phil Adams http://philadams.net

Grab photos from Flickr for a set of keywords.  Considers only those photos
with a CC non-commercial license, or more relaxed license (license ids 1,2,4,5
at https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html)

See README.md for details.
"""

from __future__ import print_function
import sys
import time
import json
import os
import glob
from pprint import pprint

import times
import requests
import flickr_api

import ipdb as pdb
from bansi import *

config = json.load(open('./config.json'))

TAG = 'philMeta'
API_KEY = config['flickr_api_key']
API_SECRET = config['flickr_api_secret']
REST_ENDPOINT = 'https://api.flickr.com/services/rest/'
SEARCHES_DIR = './search'
IMG_URL = 'http://farm%s.staticflickr.com/%s/%s_%s_z.jpg'
IMG_FNAME = './images/%s/%s-%s.jpg'  # query/id-query.jpg
IMG_URL_S = 'http://farm%s.staticflickr.com/%s/%s_%s_q.jpg'
IMG_FNAME_S = './images/%s/%s_square-%s.jpg'  # query/id-query.jpg
IMG_DIR = './images/%s'  # query
TMP_DIR = './tmp'
TMP_FILE = TMP_DIR + "/" + str(os.getpid()) + ".tmp"
DATA_DIR = './data'
DATA_ALL_FNAME = './data/%s.json'  # query
DATA_FNAME = './images/%s/%s-%s-data.json'  # query/id-query-data.json
EXIF_FNAME = './images/%s/%s-%s-exif.json'  # query/id-query-exif.json
NOW = times.now()
TZ = 'America/New_York'
YMD = times.format(NOW, TZ, fmt='%Y-%m-%d')
flickr_api.set_keys(api_key=API_KEY, api_secret=API_SECRET)
args = None # No args yet

def unjsonpify(jsonp):
    return jsonp[14:-1]  # totally hacky strip off jsonp func

def save_image(url, fname):
    r = requests.get(url, stream=True)
    with open(TMP_FILE, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
    os.rename(TMP_FILE, fname)     # Put tmp in place

def get_existing_exif(meta, photo):
    fname = EXIF_FNAME % (meta['query'], photo['id'], meta['query'])
    print(" Checking cached:", fname)
    if os.path.isfile(fname):      # Already have file
        with open(fname) as f: s = f.read()
    else:                          # No, must download again
        print(red, "Re-retrieving exif: ", fname, rst, sep="")
        s = get_photo_exif_str(photo)
        with open(TMP_FILE, "w") as f:
            f.write(s)
            #json.dump(s, f) # For storing json's as strings
        os.rename(TMP_FILE, fname) # Put tmp file in place
        #time.sleep(0.05)
    s = json.loads(s)
    return s

def get_existing_info(meta, photo):
    fname = DATA_FNAME % (meta['query'], photo['id'], meta['query'])
    print(" Checking cached:", fname)
    if os.path.isfile(fname):      # Already have file
        with open(fname) as f: s = f.read()
    else:                          # No, must download again
        print(red, "Re-retrieving info: ", fname, rst, sep="")
        s = get_photo_info_str(photo)
        with open(TMP_FILE, "w") as f:
            f.write(s)
            #json.dump(s, f) # For storing json's as strings
        os.rename(TMP_FILE, fname) # Put tmp download in place
        #time.sleep(0.05)
    s = json.loads(s)
    return s

def get_photo_info_str(photo):
    params = {'api_key': API_KEY,
              'photo_id': photo['id'],
              'secret': photo['secret'],
              'method': 'flickr.photos.getInfo',
              'format': 'json'}
    response = requests.get(REST_ENDPOINT, params=params)
    return unjsonpify(response.text)

def get_photo_exif_str(photo):
    params = {'api_key': API_KEY,
              'photo_id': photo['id'],
              'secret': photo['secret'],
              'method': 'flickr.photos.getExif',
              'format': 'json'}
    response = requests.get(REST_ENDPOINT, params=params)
    return unjsonpify(response.text)

def download_search(results):
    meta = results[TAG]
    photos_data = []
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.isdir(TMP_DIR):
        os.makedirs(TMP_DIR)
    if not os.path.isdir(IMG_DIR % meta['query']):
        os.makedirs(IMG_DIR % meta['query'])
    for i, photo in enumerate(results['photos']['photo']):
        sys.stdout.write('\rProcessing photo %s%d/%d%s (%s%s%s) (id: %s) ' %
                         (
                           whi,
                          i + 1,
                          len(results['photos']['photo']),
                           rst,
                           yel,
                          meta['query'],
                           rst,
                          photo['id']))
        sys.stdout.flush()
        exif = get_existing_exif(meta, photo)
        if not exif['stat'] == u'ok':
            print(" EXIF FAIL. Status: ", exif['stat'])
            continue
        exif_items = exif['photo']['exif']
        if args.focallength:
            try:
                [foo[u'clean'][u'_content'] \
                    for foo in exif_items \
                        if foo[u'tag'] == u'FocalLength'][0]
            except:
                print(" exif['photo']['exif'] missing entry with tag == FocalLength")
                print("  or that json dict is missing ['clean']['_content']")
                if args.verbose: print(exif)
                continue
        info = get_existing_info(meta, photo)

        if args.unifieddata: photos_data.append(info['photo'])

        img_url = IMG_URL % (photo['farm'],
                             photo['server'],
                             photo['id'],
                             photo['secret'])
        img_url_s = IMG_URL_S % (photo['farm'],
                                 photo['server'],
                                 photo['id'],
                                 photo['secret'])
        img_fname = IMG_FNAME % (meta['query'], photo['id'], meta['query'])
        if os.path.isfile(img_fname):      # Already have file
            pass
        else:
            #img_fname_s = IMG_FNAME_S % (meta['query'], photo['id'], meta['query'])
            print("Downloading {}".format(img_url))
            save_image(img_url, img_fname)
            if args.res_square:
                save_image(img_url_s, img_fname_s)
            #time.sleep(0.15)
    if args.unifieddata:
        with open(DATA_ALL_FNAME % meta['query'], 'w') as f:
            json.dump(photos_data, f)


def download_searches(filenames):
    for fname in filenames:
        with open(fname) as f:
            download_search(json.load(f))
            print('')
    print('done')


def search(query='pain'):
    if not os.path.isdir(SEARCHES_DIR):
        os.makedirs(SEARCHES_DIR)
    params = {'api_key': API_KEY,
              'safe_search': '1',  # safest
              'media': 'photos',  # just photos
              'content_type': '1',  # just photos
              'privacy_filter': '1',  # public photos
              #'license': '1,2,4,5',  # see README.md
              'license': '0,1,2,4,5,6,7,8,9,10',  # see README.md
              'per_page': '4000',  # max=500
              'sort': 'relevance',
              'method': 'flickr.photos.search',
              'format': 'json'}
    query_dict = {'text': query}
    clean_query = query.replace(' ', '-')
    fname = './search/search.%s.%s.json' % (clean_query, YMD)
    response = requests.get(REST_ENDPOINT,
                            params=dict(params, **query_dict))
    with open(fname, 'w') as f:
        data = json.loads(unjsonpify(response.text))
        data[TAG] = {}
        data[TAG]['query'] = clean_query
        data[TAG]['when'] = YMD
        f.write(json.dumps(data))


def keywords_search(args, keywords):
    for i, keyword in enumerate(keywords):
        sys.stdout.write('\rrunning keyword search... %d/%d (%s)' %
                         (i + 1, len(keywords), keyword))
        sys.stdout.flush()
        search(keyword)
        time.sleep(1)
    print('\ndone')

if __name__ == '__main__':
    import argparse

    # populate and parse command line options
    desc = 'Grab photos from Flickr.'
    parser = argparse.ArgumentParser(description=desc)
    #parser.add_argument('infile', nargs='?', default=sys.stdin,
    #                    type=argparse.FileType('rU'),
    #                    help='input file (.csv)')
    parser.add_argument('-s', '--search', dest='search', action='store_true')
    parser.add_argument('-d', '--download', dest='download',
                        action='store_true')
    parser.add_argument('-fl', '--focallength', dest='focallength', \
        action='store_true', help="Require EXIF FocalLength tag or don't download")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
        help="Verbose. Currently only one level of verbosity.")
    parser.add_argument('-ud', '--unifieddata', dest='unifieddata', \
        action='store_true', \
        help="Store a unified file of all photo info in {}".format(DATA_DIR))
    parser.add_argument('-rs', '--square', dest='res_square',
        action='store_true',
        help="Also retrieve square resolution file")
    args = parser.parse_args()

    if args.search:
        keywords = []
        with open('keywords.txt') as f:
            keywords = [e.strip() for e in f.readlines()]
        keywords_search(args, keywords)
    elif args.download:
        searches = glob.glob('./search/search.*.json')
        download_searches(searches)
    else:
        pprint(config)
        print(parser.print_help())

# vim:et
