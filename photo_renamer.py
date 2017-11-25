#!python3
# -*- coding: utf-8 -*-

"""
Written by Aleksandr Mikheev
https://github.com/RandyRomero/photo_renamer/

A little script that reads data from exif from your jpg files and rename it accordingly.
First it asks folder to look through for your jpg files. Important note: script goes through subfolders as well.
Then it reads exif info from jpg files and give you two lists to check: one is a list of files to be renamed,
second is a list of files to be deleted.
It will rename files like this "yyyy-mm-dd hh-mm-ss camerabrand cameramodel lensbrand lensmodel".
In case there are several files with the same date of shooting,
script will add [next number] to the end of the file name.
Script can also detect duplicates with other names and that's really useful sometimes.
It will offer you to remove them.

It was developed and tested under Windows 10 64 bit with Python 3.6.2.
"""

import os
import shelve
import exifread  # library to get exif data from file
import handle_logs  # separate file for setting up logging to console and log file
from send2trash import send2trash

# setting up loggers
logFile, logConsole = handle_logs.set_loggers()
handle_logs.clean_log_folder(20, logFile, logConsole)
logFile.info('Program has started')

images_with_info = []  # List of all images with their info from exif
images_to_delete = []  # list of superfluous copies to remove
name_strings = {}  # Dict where key is a final new name of a photo and values is a full path to this photo
perm_denied_files = []  # Files that script could not rename because it was locked by OS


def process_files(path_with_images):
    # Recursively search for photos and extract exif info

    image_extension = ('.jpg', '.jpeg')  # Files with only these extensions will be processed

    for root, subfolders, files in os.walk(path_with_images):
        for file in files:
            if file.lower().endswith(image_extension):
                with open(os.path.join(root, file), 'rb') as f:
                    # 'details=False' to avoid extracting superfluous data from EXIF and overflowing memory
                    tags = exifread.process_file(f, details=False)
                    path_to_image = os.path.join(root, file)
                    data = get_new_name_for_photo(tags, path_to_image, file)
                    if data != -1:
                        images_with_info.append(data)


def open_db():
    # Open database which contains information how different tags from exif rename to normal names
    # e.g 'NIKON CORPORATION' to 'Nikon' or 'chiron' to 'Mi MIx 2'
    if not os.path.exists('db'):
        os.mkdir('db')
    shelve_db = shelve.open('db\\tags_db')
    shelve_db['test'] = 'database ok'
    if shelve_db['test']:
        logConsole.debug('Database ok')
        logFile.debug('Database ok')
    return shelve_db


def get_new_name_for_photo(exif, path_to_picture, file):

    """
    Takes exif info of one page, covert it to appropriate name by the template, check if there are some duplicates

    :param file: file name to compare with new name to avoid creating copies of the same file
    :param exif: exif data from current file
    :param path_to_picture: full path to picture
    :return: list where first item is path to picture and the second is string with new name for picture OR
    returns -1 if file will be renamed
    """

    def check_tag(tag, tag_type):
        """
        Function that compare name of camera and lens in database and in EXIF data.
        If it is not in db, function asks user whether to use name from EXIF data or give tag a
        new name to use it for renaming of photo. It will then store this new name in database to use it next time.

        :param tag: name of component from EXIF
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
                    # Is user wants to use exact name from EXIF — save it in db and return it for renaming
                    db[tag] = tag
                    return tag
                elif user_answer == 'n':  # If user wants to use another name, let him key it in
                    sure = 'n'
                    while sure == 'n':
                        db_tag = input('Please, type new name for ' + tag_type + ' instead of ' + tag + ': ').strip()
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

    def remove_repeated_words(camera_info_string):
        """
        Remove name of brand or whatever if it is mentioned more than one time

        :param camera_info_string: string like "date_time camera_brand camera_model lens_brand lens_model"
        :return: string without words that are used more than once
        """

        words_array = []
        # Dedupe string
        for item in camera_info_string.split(' '):
            if item not in words_array:
                words_array.append(item)

        # Convert back to string from list and return
        return ' '.join(words_array)

    def binary_comparison(current_photo, processed_photo):
        """
        Check whether two photos are totally equal
        :param current_photo: full path to picture for which script tries to come up with a new name
        :param processed_photo: full path of picture that can be possibly a duplicate of a current photo
        :return: True or False
        """
        with open(current_photo, 'rb') as a:
            with open(processed_photo, 'rb') as b:
                if a.read() == b.read():
                    print('DUPLICATE: "{}" already exists here as "{}"'.format(current_photo, processed_photo))
                    print('You can delete this extra copy later in this program.')
                    logFile.info('DUPLICATE: "{}" already exists here as "{}"'.format(current_photo, processed_photo))
                    logFile.info('You can delete this extra copy later in this program.')
                    # That list will be used to show user files to be deleted and to send them to trash bin recursively
                    images_to_delete.append(path_to_picture)
                    return True
                else:
                    logFile.info('"{}" is not duplicate of "{}"'.format(current_photo, processed_photo))
                    return False

    def check_duplicates(supposed_name):
        """
        That was most hard function for me.
        Function checks whether file is going to get unique name after renaming.
        If there is more than one file with this name (usually because of burst shooting) these file should
        be named as someName[2].jpg, someName[3].jpg and so on. Function just keeps track of every name that app
        is going to give to every file.
        This function maybe doesn't look very elegant, but I did my best and at least it works write.

        :param supposed_name: string with name that script wants to give to a photo
        :return: it either returns new name according to existing duplicates (is any) or returns None if current photo
        ia a duplicate or has been already renamed

        """

        # Counter which increases every time there is a duplicate for current photo.
        # It will be added to the end of the photo name if it is > 1
        counter = 1

        def already_has_this_name(name):
            """
            Check whether file already has exactly this name that script wants to give it
            :param name: string with new supposed name of file
            :return: Boolean
            """

            if name.lower() == original_filename.lower():
                print('New name matches current name. This file has already been renamed.')
                logFile.info('New name matches current name. This file has already been renamed.')
                return True
            return False

        def get_new_order_name(name, name_with_counter):
            """
            Avoid giving the same names for photos that were taken during the same second
            Also avoid giving new order names to duplicates instead of ignoring them
            :param name: string with new supposed name of file
            :param name_with_counter: same name, but with counter to manage photos with same date of shooting
            :return: string with name with counter or None
            """

            nonlocal counter

            # We don't always need to use name_with_counter in this function,
            # sometimes we need to use just name everywhere
            if not name_with_counter:
                name_with_counter = name

            print('That name has already been picked up during this session.')
            logFile.info('That name has already been picked up during this session.')
            # Check whether files are duplicates
            if binary_comparison(path_to_picture, name_strings[name_with_counter]):
                return None

            # Check if it is possible to give to file a name with next order number
            # or name with this order number has been already picked up during the session
            counter += 1
            while name + '[{}]'.format(counter) in list(name_strings.keys()):
                logFile.info('New supposed name is "' + name + '[{}].jpg"'.format(counter))
                # Check if there is already the duplicate of this file
                if binary_comparison(path_to_picture, name_strings[name + '[{}]'.format(counter)]):
                    return None
                counter += 1
            logFile.info('New supposed name is "' + name + '[{}]"'.format(counter))
            return name + '[{}]'.format(counter)

        logFile.info('Supposed name is "{}.jpg"'.format(supposed_name))
        print('Checking for duplicates...')
        logFile.info('Checking for duplicates...')

        if already_has_this_name(supposed_name + '.jpg'):
            return None

        if supposed_name in list(name_strings.keys()):
            supposed_name = get_new_order_name(supposed_name, None)
            if not supposed_name:
                return None

        # Check whether file with the same new name already exists in folder (avoiding duplicates)
        if os.path.exists(os.path.join('\\'.join(path_to_picture.split('\\')[:-1]), supposed_name + '.jpg')):
            path_to_existing_copy = '\\'.join(path_to_picture.split('\\')[:-1])
            # Check if files are duplicates
            if binary_comparison(path_to_picture, os.path.join(path_to_existing_copy,  supposed_name + '.jpg')):
                return None
            else:
                # If there is file with this name but not a duplicate of already existing file
                print('There is already another file with this name.')
                logFile.warning('There is already another file with this name.')
                counter = 2
                # Try to give it new name with next order number
                while os.path.exists(os.path.join(path_to_existing_copy, supposed_name + '[{}].jpg'.format(counter))):
                    # Check if file already has this name and script doesn't need to rename it
                    if already_has_this_name(supposed_name + '[{}].jpg'.format(counter)):
                        return None
                    new_supposed_name = os.path.join(path_to_existing_copy, supposed_name + '[{}].jpg'.format(counter))
                    logFile.info('New supposed name is "' + supposed_name + '[{}].jpg"'.format(counter))
                    # To be on safe side check whether file to be renamed and file with this name that already
                    # exists are duplicates
                    if binary_comparison(path_to_picture, new_supposed_name):
                        return None
                    counter += 1

                # Second check whether supposed name has been picked up already (yes, it is 100% need second check)
                if supposed_name + '[{}]'.format(counter) in list(name_strings.keys()):
                    supposed_name = get_new_order_name(supposed_name, supposed_name + '[{}]'.format(counter))
                    if not supposed_name:
                        return None
                    logFile.info('New supposed name is "' + supposed_name + '[{}]"'.format(counter))
                    return supposed_name
                else:
                    logFile.info('New supposed name is "' + supposed_name + '[{}]"'.format(counter))
                    supposed_name = supposed_name + '[{}]'.format(counter)

        return supposed_name

    original_filename = file
    one_image_with_info = []  # All info about image in list form
    date_time = str(exif.get('EXIF DateTimeOriginal', None))  # Get date when picture was shot
    if date_time == 'None':  # If there is no date and time - exit function
        print(path_to_picture + ' --- there is no EXIF data.\n')
        logFile.info(path_to_picture + ' --- there is no EXIF data.\n')
        return -1

    # Get necessary tags from EXIF data
    camera_brand = str(exif.get('Image Make')).strip()
    camera_model = str(exif.get('Image Model')).strip()
    lens_brand = str(exif.get('EXIF LensMake')).strip()
    lens_model = str(exif.get('EXIF LensModel')).strip()

    # Show to user raw data from EXIF
    print('\nRaw data from ' + path_to_picture)
    logFile.info('')
    logFile.info('Raw data from ' + path_to_picture)
    print('DateTime: {} Camera brand: {} Camera model: {} Lens brand: {} Lens model: {}'
          .format(date_time, camera_brand, camera_model, lens_brand, lens_model))
    logFile.info('DateTime: {} Camera brand: {} Camera model: {} Lens brand: {} Lens model: {}'
                 .format(date_time, camera_brand, camera_model, lens_brand, lens_model))

    # Check if we have more appropriate name in database for every tag
    if camera_brand != 'None':
        camera_brand = check_tag(camera_brand, 'camera_brand').strip()

    if camera_model != 'None':
        camera_model = check_tag(camera_model, 'camera_model').strip()

    if lens_brand != 'None':
        lens_brand = check_tag(lens_brand, 'lens_brand').strip()

    if lens_model != 'None':
        lens_model = check_tag(lens_model, 'lens_model').strip()

    # Make string 'name_string' out of photo date, camera model etc and put it in one list with path
    # Example of name_string after loop:
    # 2015:06:13 15:20:32 Canon Canon EOS 60D 17-50mm
    name_string = ''
    for entry in [date_time, camera_brand, camera_model, lens_brand, lens_model]:
        if entry != 'None':
            name_string += entry + ' '

    # Replace not allowed characters before calling function
    name_string = remove_repeated_words(name_string.replace(':', '-').replace('/', '')).strip()

    new_name = check_duplicates(name_string)
    if new_name is not None:
        name_string = new_name
    else:
        return -1

    one_image_with_info.extend([path_to_picture, name_string])

    # Put final file name and it's full path in dictionary in order to be able to keep tracked of name that have been
    # picked up during the session and to be able to perform binary comparison to figure out duplicates
    name_strings[name_string] = path_to_picture
    print('How it will be renamed: ')
    print(one_image_with_info[1] + '.jpg\n')
    logFile.info('How it will be renamed: ')
    logFile.info(one_image_with_info[1] + '.jpg\n')
    return one_image_with_info


def remove_copies():
    """
    Function for recursive removing files from list
    :return: doesn't get or return anything
    """
    print('Start to remove superfluous copies.')
    logFile.info('Start to remove superfluous copies.')
    for file in images_to_delete:
        send2trash(file)
        print(file + ' was removed.')
        logFile.info(file + ' was removed.')
    print('All old copies were removed')
    logFile.info('All old copies were removed')


def rename_photos():
    """
    Recursively rename photos
    :return: doesn't get or return anything
    """
    for item in images_with_info:
        # Remove current name of file from full path to file and add new name to path
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
    if os.path.exists(path_to_look_for_photos) and os.path.isdir(path_to_look_for_photos):
        print('Gotcha!')
        logFile.info('Path to look up for pictures to renames is ' + path_to_look_for_photos + '\n')
        db = open_db()
        process_files(path_to_look_for_photos)
        db.close()
        logFile.info('Database was closed successfully')
        print('\nThere are ' + str(len(images_with_info)) + ' files to rename.')
        logFile.info('')
        logFile.info('There are ' + str(len(images_with_info)) + ' files to rename.')
        print('There are ' + str(len(images_to_delete)) + ' old copies to delete.')
        logFile.info('There are ' + str(len(images_to_delete)) + ' old copies to delete.')
        break
    else:
        print('This path doesn\'t exist. Try another one')
        continue

if len(images_with_info) > 0:
    while True:
        see_rename_list_or_not = input('Do you want to see list of files to be renamed? y/n: ')
        logFile.info('Do you want to see list of files to be renamed? y/n: \n')
        if see_rename_list_or_not.lower() == 'y':
            for item in images_with_info:
                print('"{}" will be renamed as "{}.jpg"'.format(item[0], item[1]))
            break
        elif see_rename_list_or_not.lower() == 'n':
            break
        else:
            print('It is wrong input, try again.')
            logFile.info('It is wrong input, try again.\n')

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
        see_list_to_delete = input('Do you want to see list of files to be deleted? y/n: ')
        logFile.info('Do you want to see list of files to be deleted? y/n: \n')
        if see_list_to_delete.lower() == 'y':
            for item in images_to_delete:
                print(item + ' will be deleted')
            break
        elif see_list_to_delete.lower() == 'n':
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