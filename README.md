# photo_renamer
Written by Aleksandr Mikheev
https://github.com/RandyRomero/photo_renamer/

A little script that reads data from exif from your jpg files and rename it accodringly. 

First it asks folder to look through for your jpg files. Important note: script goes through subfolders as well. 

Than it reads exif info from jpg files and give you two lists to check: one is a list of files to be renamed, second is a list of files to be deleted.

It will rename files like this "yyyy-mm-dd hh-mm-ss camerabrand cameramodel lensbrand lensmodel". 
In case there are several files with the same date of shooting, script will add [next number] to the end of the file name.
Script can also detect duplicates with other names and that's really usefull sometimes. It will offer you to remove them.

If case there is no useful exif data in photo script will add "(no data)" to its name. And won't process files
with this mark then. 


It was developed and tested under Windows 10 64 bit with Python 3.6.2.
