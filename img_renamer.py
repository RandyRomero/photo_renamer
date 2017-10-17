#!python3
# -*- coding: utf-8 -*-

# Script that rename photos by date from EXIF when it was taken

import os
import shutil
import exifread

images_with_info = []  # List of all images with their info from exif


def remove_repeated_words(camera_info):
    # Remove name of brand or whatever if they mentioned moe than one time

    words_object = {}
    for item in camera_info.split(' '):  # Memorize in dictionary only one instance of every word
        if item not in words_object.keys():
            words_object[item] = item

    # Convert back to string from list and return
    return ' '.join(list(words_object.values()))


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

    def get_normal_name():
        # Convert code names to meaningful names
        nonlocal camera_brand
        nonlocal camera_model

        # Nobody cares whether Nikon is a corporation or whatever
        if camera_brand == 'NIKON CORPORATION':
            camera_brand = 'NIKON'

        if camera_model in ['G8342', 'G8341', 'G8343']:
            camera_model = 'Xperia XZ1'

        if camera_model == 'chiron':
            camera_model = 'Mi Mix 2'

    one_image_with_info = []  # All info about image in list form

    date_time = str(exif.get('EXIF DateTimeOriginal', None))  # Get date when picture was shot

    if date_time == 'None':  # If there is no date and time - exit function
        print(picture + ' --- there is no EXIF data.')
        return

    camera_brand = str(exif.get('Image Make'))
    camera_model = str(exif.get('Image Model'))
    lens_brand = str(exif.get('EXIF LensMake'))
    lens_model = str(exif.get('EXIF LensModel'))

    # Show raw data from exif
    print('Raw data from ' + picture)
    print('DateTime: {} Camera brand: {} Camera model: {} Lens brand: {} Lens model: {}'
          .format(date_time, camera_brand, camera_model, lens_brand, lens_model))

    get_normal_name()

    # Make string out of photo date, camera model etc and put it in one list with path
    name_string = ''
    for entry in [date_time, camera_brand, camera_model, lens_brand, lens_model]:
        if entry != 'None':
            name_string += entry + ' '
    name_string = remove_repeated_words(name_string.replace(':', '-').replace('/', ''))
    one_image_with_info.extend([picture, name_string])
    print('How it will be renamed: ')
    print(one_image_with_info[1] + '\n')
    images_with_info.append(one_image_with_info)


def rename_photos():
    print('Function hasn\'t been written yet')

while True:
    path_to_look_for_photos = input('Please type in directory with your photos:\n')
    if os.path.exists(path_to_look_for_photos):
        print('Gotcha!')
        process_files(path_to_look_for_photos)
        print('There are ' + str(len(images_with_info)) + ' files to rename.')
        break
    else:
        print('This path doesn\'t exist. Try another one')
        continue

# while True:
#     rename_or_not = input('Do you want to rename these photos? y/n: ')
#     if rename_or_not.lower() == 'y':
#         rename_photos()
#     elif rename_or_not.lower() == 'n':
#         print('Ciao!')
#         break
#     else:
#         print('It is wrong input, try again.')
