#!python3
# -*- coding: utf-8 -*-

# Script that rename photos by date from EXIF when it was taken

import os
import shutil
import exifread

images_with_info = []  # List of all images with their info from exif


def process_files(path_with_images):
    # Search for photos, open them and extract exif info

    image_extension = ('.jpg', '.jpeg')

    for root, subfolders, files in os.walk(path_with_images):
        for file in files:
            if file.lower().endswith(image_extension):
                with open(os.path.join(root, file), 'rb') as f:
                    # Details=False to avoid extracting useless stuff and overflowing memory
                    tags = exifread.process_file(f, details=False)
                    image = os.path.join(root, file)
                    work_with_exif_data(tags, image)


def work_with_exif_data(exif, picture):
    # Gather info about every image and store all in list

    one_image_with_info = []  # All info about image in list form
    to_print = ''  # All info about one particular image in string format

    date_time = str(exif.get('EXIF DateTimeOriginal', None))  # Get date when picture was shot

    if date_time == 'None':  # If there is no date and time - exit function
        print(picture + ' --- there is no EXIF date.')
        return

    camera_brand = str(exif.get('Image Make', None))
    camera_model = str(exif.get('Image Model', None))
    lens_brand = str(exif.get('EXIF LensMake', None))
    lens_model = str(exif.get('EXIF LensModel', None))

    # No body cares whether Nikon is corporation of whatever
    if camera_brand == 'NIKON CORPORATION':
        camera_brand = 'NIKON'

    # If camera brand is also denoted in camera model - get rid of camera brand in camera model
    if camera_brand in camera_model:
        camera_model = (camera_model.replace(camera_brand, ''))[1:]

    # Add entries in list if entry is not empty (contains zero in our case)
    for entry in [picture, date_time, camera_brand, camera_model, lens_brand, lens_model]:
        if entry != 'None':
            one_image_with_info.append(entry)
    # Add list with path to image and with image's info into one big list
    images_with_info.append(one_image_with_info)

    # Prepare every entry to be printed out
    for item in one_image_with_info:
        to_print += item + ' '
        to_print = to_print.replace(':', '-')
        to_print = to_print.replace('/', '')
    print(to_print)


def rename_photos():
    print('haha lol kek')

while True:
    path_to_look_for_photos = input('Please type in directory with your photos:\n')
    if os.path.exists(path_to_look_for_photos):
        print('Gotcha!')
        process_files(path_to_look_for_photos)
        break
    else:
        print('This path doesn\'t exist. Try another one')
        continue

while True:
    rename_or_not = input('Do you want to rename these photos? y/n: ')
    if rename_or_not.lower() == 'y':
        rename_photos()
    elif rename_or_not.lower() == 'n':
        print('Ciao!')
        break
    else:
        print('It is wrong input, try again.')