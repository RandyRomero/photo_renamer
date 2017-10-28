#!python3
# -*- coding: utf-8 -*-

# Script that rename photos by date from EXIF when it was taken

import os
import shutil
import exifread  # library to get exif data from file
from get_normal_name import get_normal_name

images_with_info = []  # List of all images with their info from exif


def process_files(path_with_images):
    # Search for photos, open them and extract exif info

    image_extension = ('.jpg', '.jpeg')

    for root, subfolders, files in os.walk(path_with_images):
        for file in files:
            if file.lower().endswith(image_extension):
                with open(os.path.join(root, file), 'rb') as f:
                    # details=False to avoid extracting superfluous data from EXIF and overflowing memory
                    tags = exifread.process_file(f, details=False)
                    path_to_image = os.path.join(root, file)
                    data = work_with_exif_data(tags, path_to_image)
                    if data:
                        images_with_info.append(data)


def work_with_exif_data(exif, path_to_picture):
    # Gather info about every image and store all in list

    def remove_repeated_words(camera_info):
        # Remove name of brand or whatever if it is mentioned more than one time

        words_object = []
        # Dedupe string
        for item in camera_info.split(' '):
            if item not in words_object:
                words_object.append(item)

        # Convert back to string from list and return
        return ' '.join(words_object)

    one_image_with_info = []  # All info about image in list form

    date_time = str(exif.get('EXIF DateTimeOriginal', None))  # Get date when picture was shot

    if date_time == 'None':  # If there is no date and time - exit function
        print(path_to_picture + ' --- there is no EXIF data.\n')
        return

    camera_brand = str(exif.get('Image Make'))
    camera_model = str(exif.get('Image Model'))
    lens_brand = str(exif.get('EXIF LensMake'))
    lens_model = str(exif.get('EXIF LensModel'))

    # Show raw data from exif
    print('Raw data from ' + path_to_picture)
    print('DateTime: {} Camera brand: {} Camera model: {} Lens brand: {} Lens model: {}'
          .format(date_time, camera_brand, camera_model, lens_brand, lens_model))

    camera_brand, camera_model, lens_brand, lens_model = get_normal_name(camera_brand, camera_model, lens_brand,
                                                                         lens_model)

    # Make string 'name_string' out of photo date, camera model etc and put it in one list with path
    # Example of name_string after loop:
    # 2015:06:13 15:20:32 Canon Canon EOS 60D 17-50mm
    name_string = ''
    for entry in [date_time, camera_brand, camera_model, lens_brand, lens_model]:
        if entry != 'None':
            name_string += entry + ' '

    # Replace not allowed characters before calling function
    name_string = remove_repeated_words(name_string.replace(':', '-').replace('/', ''))
    name_string = name_string[:-1] + '.jpg'
    one_image_with_info.extend([path_to_picture, name_string])
    print('How it will be renamed: ')
    print(one_image_with_info[1] + '\n')
    return one_image_with_info


def rename_photos():
    for item in images_with_info:
        # Remove name of file from full path to file

        new_name = os.path.join('\\'.join(item[0].split('\\')[:-1]), item[1])
        counter = 0
        while os.path.exists(new_name):
            counter += 1
            new_name = new_name[:-4] + ' {}.jpg'.format(counter)
        print(new_name)


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

while True:
    rename_or_not = input('Do you want to rename these photos? y/n: ')
    if rename_or_not.lower() == 'y':
        rename_photos()
        break
    elif rename_or_not.lower() == 'n':
        print('Ciao!')
        break
    else:
        print('It is wrong input, try again.')
