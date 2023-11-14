#	Just a quick little program to show exif data.
#
#	Because I'm doing this in the context of working with
#	orientation stuff, I'm showing extra details on Orientation.
#

import sys
import re

from PIL import Image
from PIL.ExifTags import TAGS


#############################################
#	constants
#############################################

USAGE = """
	Display exif data of a given image file.

USAGE:		show_exif filename

"""
ORIENTATION_TAG_NUM = 274


#############################################
#	begin
#############################################

if len(sys.argv) != 2:
	exit(USAGE)

filename = sys.argv[1]

# open the file
image = None
try:
    image = Image.open(filename)
except:
    exit(f'unable to open {filename}')

exif = image.getexif()
print(f'exif of {filename} is {exif}')
if exif is None:
	exif = {}

if ORIENTATION_TAG_NUM in exif:	
	orientation = exif[ORIENTATION_TAG_NUM]
	print(f'   Orientation = {orientation}')
else:
	print('   no orientation info')

# clean up
image.close()
