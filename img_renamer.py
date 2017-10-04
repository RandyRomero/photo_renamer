#!python3
# -*- coding: utf-8 -*-

# Script that rename photos by date from EXIF when it was taken

import os
import shutil
import exifread

image_extension = ('.jpg', '.jpeg')


def process_files(path_with_images):

    def work_with_exif_data(exif, picture):
        images_with_info = []

        date_time = exif.get('EXIF DateTimeOriginal', 0)  # Get date when picture was shot

        if date_time == 0:  # If there is no date and time - exit function
            print('There is no EXIF date')
            return

        camera_brand = str(exif.get('Image Make', 0))
        camera_model = exif.get('Image Model', 0)
        lens_brand = exif.get('EXIF LensMake', 0)
        lens_model = exif.get('EXIF LensModel', 0)
        print(type(camera_brand))

        # No body cares whether Nikon is corporation of whatever
        if str(camera_brand) == 'NIKON CORPORATION':
            camera_brand = 'NIKON'

        # If camera brand is also denoted in camera model - get rid of camera brand in camera model
        if str(camera_brand) in str(camera_model):
            camera_model = (str(camera_model).replace(str(camera_brand), ''))[1:]

        # Add entries in list if entry is not empty (contains zero in our case)
        one_image_with_info = []
        for entry in [picture, date_time, camera_brand, camera_model, lens_brand, lens_model]:
            if entry != 0:
                one_image_with_info.append(entry)
            # Add list with path to image and with image's info into one big list
            images_with_info.append(one_image_with_info)

        # Prepare every entry to be printed out
        for item in images_with_info:
            to_print = ''
            for i in item:
                to_print += str(i) + ' '
            print(to_print)

    # Search for photos, open them and extract exif info
    for root, subfolders, files in os.walk(path_with_images):
        for file in files:
            if file.lower().endswith(image_extension):
                with open(os.path.join(root, file), 'rb') as f:
                    tags = exifread.process_file(f)
                    image = os.path.join(root, file)
                    work_with_exif_data(tags, image)

    # for image in images_with_info:
    #     image_name = (image['Image_date_time'] + ' ' + image['Camera'] + ' ' + image['Lens'])
    #     image_name = image_name.replace(':', '.')
    #     image_name = image_name.replace('/', '')
    #     print(image_name)

while True:
    path_to_look_for_photos = input('Please type in directory with your photos:\n')
    if os.path.exists(path_to_look_for_photos):
        print('Gotcha!')
        process_files(path_to_look_for_photos)
        break
    else:
        print('This path doesn\'t exist. Try another one')
        continue
