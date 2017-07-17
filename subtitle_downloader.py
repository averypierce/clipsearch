#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Name      : subtitle downloader
# Purpose   : One step subtitle download
#
# Authors   : manoj m j, arun shivaram p, Valentin Vetter, niroyb
# Edited by : Valentin Vetter
# Created   :
# Copyright : (c) www.manojmj.com
# Licence   : GPL v3
#-------------------------------------------------------------------------------

import hashlib
import os
import shutil 
import sys
import logging
import requests,time,re,zipfile
from bs4 import BeautifulSoup
PY_VERSION = sys.version_info[0]
if PY_VERSION == 2:
    import urllib2
if PY_VERSION == 3:
    import urllib.request

def get_hash(file_path):
    read_size = 64 * 1024
    with open(file_path, 'rb') as f:
        data = f.read(read_size)
        f.seek(-read_size, os.SEEK_END)
        data += f.read(read_size)
    return hashlib.md5(data).hexdigest()

def sub_fetcher(file_path):
    # Put the code in a try catch block in order to continue for other video files, if it fails during execution
    try:
        #Skip this file if it is not a video
        root, extension = os.path.splitext(file_path)
        if extension not in [".avi", ".mp4", ".mkv", ".mpg", ".mpeg", ".mov", ".rm", ".vob", ".wmv", ".flv", ".3gp",".3g2"]:
            return False

        headers = {'User-Agent': 'SubDB/1.0 (subtitle-downloader/1.0; http://github.com/manojmj92/subtitle-downloader)'}
        url = "http://api.thesubdb.com/?action=download&hash=" + get_hash(file_path) + "&language=en"
        if PY_VERSION == 3:
            req = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(req).read()

        print("Subtitle Downloaded for",file_path)
        srt = response
        try:                    
            srt = srt.decode()
        except:     
            try:
                srt = srt.decode(encoding='latin-1')
            except:
                pass

        return srt

    except:
        print("Could not find sub for",file_path)
        pass  
