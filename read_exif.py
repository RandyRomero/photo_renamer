#!python3
# -*- coding: utf-8 -*-
# Utility app to check EXIF of individual file

import exifread
import os


def read_exif(file):
    with open(file, 'rb') as image:
        tags = exifread.process_file(image)
        if len(tags.keys()) < 1:
            print('The is no EXIF in this file.')
        for tag, value in tags.items():
            print(str(tag) + ' --- ' + str(value))

while True:
    file_path = input('Please type in path to photo:\n')
    if os.path.exists(file_path):
        print('Gotcha!')
        read_exif(file_path)
        break
    else:
        print('There is no such file. Try another.')
        continue
