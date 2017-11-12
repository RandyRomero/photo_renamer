#!python3
# -*- coding: utf-8 -*-

# Script that rename photos by date from EXIF when it was taken

import os
import shelve
import exifread  # library to get exif data from file
import handle_logs
from send2trash import send2trash
import sys

logFile, logConsole = handle_logs.set_loggers()
handle_logs.clean_log_folder(20, logFile, logConsole)
logFile.info('Program has started')

images_with_info = []  # List of all images with their info from exif
images_to_delete = []  # list of superfluous copies to remove
name_strings = []
perm_denied_files = []


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
                    data = work_with_exif_data(tags, path_to_image, file)
                    if data != -1:
                        images_with_info.append(data)


def open_db():
    if not os.path.exists('db'):
        os.mkdir('db')
    shelve_db = shelve.open('db\\tags_db')
    shelve_db['test'] = 'database ok'
    if shelve_db['test']:
        logConsole.debug('Database ok')
        logFile.debug('Database ok')
    return shelve_db


def work_with_exif_data(exif, path_to_picture, file):

    """
    Gather info about image and make a string with it

    :param file: of file to compare with new name to avoid creating of copies of the same files
    :param exif: full exif data from current file
    :param path_to_picture: full path to picture
    :return: list where first item is path to picture and the second is string with new name for picture
    """

    def check_tag(tag, tag_type):
        """
        Function to look up for name of camera and lens in database. If it is not in db, function asks user whether
        to use name from EXIF data or give tag a new name to use it for renaming of files"

        :param tag: name of component form EXIF
        :param tag_type: tape of tag e.g. camera brand, camera model, lens brand, lens model
        :return: name to use for renaming of file
        """
        db_tag = db.get(tag)  # Check whether tag already exists in database
        if db_tag:  # If yes, use it to rename file
            return db_tag
        else:  # If not, ask user how to call it instead
            user_answer = input('Do you want ' + tag_type + ' to be named ' + tag + '? y/n: ').lower()
            logFile.info('Do you want ' + tag_type + ' to be named ' + tag + '? y/n: ' + user_answer)
            while True:
                if user_answer == 'y':
                    # Is user wants to use exact name from EXIF - save it in db and return it for renaming
                    db[tag] = tag
                    return tag
                elif user_answer == 'n':  # If user wants to use another name, let him put it in
                    sure = 'n'
                    while sure == 'n':
                        db_tag = input('Please, type new name for ' + tag_type + ' instead of ' + tag + ': ')
                        logFile.info('Please, type new name for ' + tag_type + ' instead of ' + tag + ': ' + db_tag)

                        sure = input('Are you sure you wanna use ' + db_tag + ' for ' + tag_type +
                                     ' instead of ' + tag + '? y/n: ').lower()
                        logFile.info('Are you sure you wanna use ' + db_tag + ' for ' + tag_type +
                                     ' instead of ' + tag + '? y/n: ' + sure)
                        if sure == 'y':
                            db[tag] = db_tag
                            print('Gotcha.')
                            return db_tag
                        else:
                            continue
                else:
                    print('Wrong input. You need to type y or n.')
                    continue

    def remove_repeated_words(camera_info):
        # Remove name of brand or whatever if it is mentioned more than one time

        words_object = []
        # Dedupe string
        for item in camera_info.split(' '):
            if item not in words_object:
                words_object.append(item)

        # Convert back to string from list and return
        return ' '.join(words_object)

    def check_duplicates(supposed_name, counter):
        # Function checks whether file is going to get unique name after renaming.
        # If there is more than one file with this name (usually because of burst shooting) these file should
        # be named as someName[2].jpg, someName[3].jpg and so on. Function just keeps track of every name that app
        # is going to give to every file.

        if supposed_name not in name_strings:
            name_strings.append(supposed_name)
            return supposed_name
        else:
            print('DUPLICATE')
            if counter is None:
                counter = 2
            while supposed_name + '[{}]'.format(counter) in name_strings:
                counter += 1
            final_name = supposed_name + '[{}]'.format(counter)
            name_strings.append(final_name)

        return final_name

    def binary_comparison(existing_file, original_picture_path):
        # Explanation below in message_text
        with open(existing_file, 'rb') as a:
            with open(original_picture_path, 'rb') as b:
                # logConsole.debug(existing_file)
                # logConsole.debug(original_picture_path)
                if a.read() == b.read():
                    message_text = 'There is already this photo named \'' + existing_copy + '.jpg\' in this folder.' \
                                    '\nOld copy will be transferred to trash bin.\n'
                    print(message_text)
                    logFile.info(message_text)
                    # logConsole.debug(os.path.exists(path_to_picture))
                    images_to_delete.append(original_picture_path)
                    # print(path_to_picture + ' was removed.')
                    # logFile.info(path_to_picture + ' was removed.')
                    return True
                else:
                    return False
                    # logConsole.error('I am not sure that it is possible. So will test and see')
                    # logFile.error('I am not sure that it is possible. So will test and see')
                    # db.close()
                    # sys.exit()

    original_filename = file
    one_image_with_info = []  # All info about image in list form
    date_time = str(exif.get('EXIF DateTimeOriginal', None))  # Get date when picture was shot

    if date_time == 'None':  # If there is no date and time - exit function
        print(path_to_picture + ' --- there is no EXIF data.\n')
        logFile.info(path_to_picture + ' --- there is no EXIF data.\n')
        return -1

    camera_brand = str(exif.get('Image Make')).strip()
    camera_model = str(exif.get('Image Model')).strip()
    lens_brand = str(exif.get('EXIF LensMake')).strip()
    lens_model = str(exif.get('EXIF LensModel')).strip()

    # Show raw data from exif
    print('Raw data from ' + path_to_picture)
    logFile.info('Raw data from ' + path_to_picture)
    print('DateTime: {} Camera brand: {} Camera model: {} Lens brand: {} Lens model: {}'
          .format(date_time, camera_brand, camera_model, lens_brand, lens_model))
    logFile.info('DateTime: {} Camera brand: {} Camera model: {} Lens brand: {} Lens model: {}'
                 .format(date_time, camera_brand, camera_model, lens_brand, lens_model))

    if camera_brand != 'None':
        camera_brand = check_tag(camera_brand, 'camera_brand')

    if camera_model != 'None':
        camera_model = check_tag(camera_model, 'camera_model')

    if lens_brand != 'None':
        lens_brand = check_tag(lens_brand, 'lens_brand')

    if lens_model != 'None':
        lens_model = check_tag(lens_model, 'lens_model')

    # Make string 'name_string' out of photo date, camera model etc and put it in one list with path
    # Example of name_string after loop:
    # 2015:06:13 15:20:32 Canon Canon EOS 60D 17-50mm
    name_string = ''
    for entry in [date_time, camera_brand, camera_model, lens_brand, lens_model]:
        if entry != 'None':
            name_string += entry + ' '

    # Replace not allowed characters before calling function
    name_string = remove_repeated_words(name_string.replace(':', '-').replace('/', ''))
    name_string = name_string[:-1]

    logConsole.debug(path_to_picture)
    if path_to_picture == r'C:\ya.disk\YandexDisk\Photo_2017\[01] January\2017-01-01 01-08-55 Xiaomi Redmi Note 3 Pro (2).jpg':
        logFile.debug('how this file is not on folder?')
        logConsole.debug('how this file is not on folder?')
    # logConsole.debug(os.path.join('\\'.join(path_to_picture.split('\\')[:-1]), name_string + '.jpg'))

    if (name_string + '.jpg') == original_filename:
        # File already has exactly this name
        print('New name matches actual name. This file has already been renamed.\n')
        logFile.warning('New name matches actual name. This file has already been renamed.\n')
        return -1

    # Check folder whether there is already a file with name that script wants give to picture
    if os.path.exists(os.path.join('\\'.join(path_to_picture.split('\\')[:-1]), name_string + '.jpg')):
        existing_copy = os.path.join('\\'.join(path_to_picture.split('\\')[:-1]), name_string)
        # Check if already existed files and file in process are the same files by binary comparison
        if binary_comparison(existing_copy + '.jpg', path_to_picture):
            return -1
        counter = 2
        # If they are not the same, that check maybe there is a file with [2].jpg or [3].jpg etc
        # logConsole.debug(existing_copy + '[{}].jpg'.format(counter))

        while os.path.exists(existing_copy + '[{}].jpg'.format(counter)):
            # if there is file with [counter].jpg at the end, check maybe it are exact duplicate of file on process
            logFile.debug('File \'' + existing_copy + '[{}].jpg\' already exists in this folder.'.format(counter))
            print('File \'' + existing_copy + '[{}].jpg\' already exists in this folder.'.format(counter))
            if existing_copy + '[{}].jpg'.format(counter) == path_to_picture:
                # If now it turns out existing file have the same name, skip renaming and start over with next file
                print('New name matches actual name. This file has already been renamed.\n')
                logFile.warning('New name matches actual name. This file has already been renamed.\n')
                return -1
            if binary_comparison(existing_copy + '[{}].jpg'.format(counter), path_to_picture):
                # If yes, skip this file and start over with next one
                return -1
            counter += 1

        # name_string = check_duplicates(existing_copy, counter)
        name_string = existing_copy + '[{}]'.format(counter)

    else:
        name_string = check_duplicates(name_string)

    one_image_with_info.extend([path_to_picture, name_string])

    # elif os.path.exists(os.path.join('\\'.join(path_to_picture.split('\\')[:-1]), name_string)):
    #     # Check if there is already file with this name in folder
    #     # If yes and if they are exact duplicates then remove not renamed file
    #     existing_copy = os.path.join('\\'.join(path_to_picture.split('\\')[:-1]), name_string)
    #     handle_existing_copies(existing_copy)
    # logConsole.debug(one_image_with_info[1] + '.jpg' + ' vs ' + original_filename)  # just for one test
    print('How it will be renamed: ')
    print(one_image_with_info[1] + '.jpg\n')
    logFile.info('How it will be renamed: ')
    logFile.info(one_image_with_info[1] + '.jpg\n')
    return one_image_with_info


def remove_copies():
    print('Start to remove superfluous copies.')
    logFile.info('Start to remove superfluous copies.')
    for file in images_to_delete:
        send2trash(file)
        print(file + ' was removed.')
        logFile.info(file + ' was removed.')
    print('All old copies were removed')
    logFile.info('All old copies were removed')


def rename_photos():
    for item in images_with_info:
        # Remove name of file from full path to file
        new_name = os.path.join('\\'.join(item[0].split('\\')[:-1]), item[1])

        if os.path.exists(new_name + '.jpg'):
            print('Error! File already exists')
            logFile.info('Error! File already exists\n')
        else:
            try:
                os.rename(item[0], new_name + '.jpg')
                print(new_name + '.jpg was renamed successfully.')
                logFile.info(new_name + '.jpg was renamed successfully.')
            except PermissionError:
                print(item[0] + ': ERROR: Permission denied.')
                logFile.info(item[0] + ': ERROR: Permission denied.\n')
                perm_denied_files.append(item[0])

print('Hello! This script can help you to automatically rename your photos (jpg files) from whatever name they have to'
      ' name like Date and time of creation + camera nad lens. For example: '
      '2017-09-05 09-15-27 Canon EOS 80D EF-S24mm f2.8 STM.jpg')

while True:
    path_to_look_for_photos = input('Please type in directory with your photos:\n')
    logFile.info('Please type in directory with your photos:\n')
    if os.path.exists(path_to_look_for_photos):
        print('Gotcha!')
        logFile.info('Path to look up for pictures to renames is ' + path_to_look_for_photos + '\n')
        db = open_db()
        process_files(path_to_look_for_photos)
        db.close()
        logFile.info('Database was closed successfully')
        print('There are ' + str(len(images_with_info)) + ' files to rename.')
        logFile.info('There are ' + str(len(images_with_info)) + ' files to rename.')
        print('There are ' + str(len(images_to_delete)) + ' old copies to delete.')
        logFile.info('There are ' + str(len(images_to_delete)) + ' old copies to delete.')
        break
    else:
        print('This path doesn\'t exist. Try another one')
        continue

if len(images_with_info) > 0:
    while True:
        rename_or_not = input('Do you want to rename these photos? y/n: ')
        logFile.info('Do you want to rename these photos? y/n: \n')
        if rename_or_not.lower() == 'y':
            rename_photos()
            break
        elif rename_or_not.lower() == 'n':
            print('Ciao!')
            logFile.info('Ciao!\n')
            break
        else:
            print('It is wrong input, try again.')
            logFile.info('It is wrong input, try again.\n')

if len(images_to_delete) > 0:
    while True:
        delete_or_not = input('Do you want to delete old copies? y/n: ')
        logFile.info('Do you want to delete old copies? y/n: \n')
        if delete_or_not.lower() == 'y':
            remove_copies()
            break
        elif delete_or_not.lower() == 'n':
            print('Ciao!')
            logFile.info('Ciao!\n')
            break
        else:
            print('It is wrong input, try again.')
            logFile.info('It is wrong input, try again.\n')

if len(perm_denied_files) > 0:
    print(str(len(perm_denied_files)) + ' files was skipped because OS denied permission.')
    logFile.info(str(len(perm_denied_files)) + ' files was skipped because OS denied permission.\n')
    print('There are these files: ')
    for item in perm_denied_files:
        print(item)
