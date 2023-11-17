#   Testing python's pillow ability to play with exif in jpgs.
#

import sys
import re

from PIL import Image
from PIL.ExifTags import TAGS
from PIL import ImageOps


ORIENTATION_TAG_NUM = 274


###################
#   Returns the part of the filename BEFORE the extension (not including
#   the dot).
#
def get_file_prefix(filename):

    return_val = re.search(r'[^\.]*', filename)
    if return_val == None:
        return ''

    return return_val.group()

#########
#   Determines if the given file has an Orientation exif attribute.
#
def has_orientation_exif(filename):
    found = False
    image = None
    try:
        image = Image.open(filename)
    except:
        # not an image, therefore no exif possible
        return False

    exif_data = image.getexif()
    if exif is None:
        # no exif at all
        image.close()
        return False

    if ORIENTATION_TAG_NUM in exif:
        found = True

    # always clean up after yourself
    image.close()

    return found


#########
#   Creates a copy of the given image with the same orientation but
#   has an exif of 1 (not transposed).  All other exif info is
#   maintained.
#
#   preconditions:
#       The file DOES INDEED HAVE AN ORIENTATION EXIF DATA!!!
#       This will probably crash if it doesn't.  Call has_orientation_exif()
#       to find out.   :)
#
#   input
#       infile      The name of the file to correct.
#
#       outfile     The name of the file to create with the transposed
#                   orientation.  If this is the same name as infile,
#                   then infile will be overwritten.
#
#       debug       When set to True, debug messages will be displayed.
#                   Defaults to False.
#
#   returns
#       True    success
#       False   error of some kind--we did our best to clean up.
#               Possibly there was simply nothing to do.
#
def correct_orientation(infile, outfile, debug = False):
    # open input file
    image1 = Image.open(infile)

    # get the exif data
    exif = image1.getexif()

    # Create new transposed image.  Side effect of this is that no
    # exif data is kept into the transposed image.
    transposed_image = ImageOps.exif_transpose(image1)

    # modify exif data to reflect that image1 has been transposed
    # TODO: test to make sure that this still works if the exif is empty
    exif[ORIENTATION_TAG_NUM] = 1

    # write new file and close it
    transposed_image.save(outfile, exif=exif)
    transposed_image.close()

    # Close input file
    image1.close()

    return True


##################################

# image = None

# # 1. open as an image
# try:
#     image = Image.open(sys.argv[1])
# except:
#     exit(f'unable to open {sys.argv[1]}')

# # 2. get exif data
# exif_data = image.getexif()
# print(f'exif of {sys.argv[1]} is {exif_data}')

# # 3. check to see if there is any exif data. If not, exit.
# if len(exif_data) == 0:
#     print('no exif data found!')
#     exit()

# # 4. check to see if there's orientation exif data. If not, exit.
# if ORIENTATION_TAG_NUM in exif_data:
#     print('found orientation data, continuing')
# else:
#     print('orientation data not found, exiting.')
#     exit()

# # 5. find the orientation
# orientation = exif_data[ORIENTATION_TAG_NUM]
# print(f'and the orientation exif is {orientation}')


# if len(sys.argv) == 3:
#     print('  - yep, 3 args.  saving...')
#     # 6. make a new image with an orientation of 1 but still displays the same
#     image2 = ImageOps.exif_transpose(image)

#     # 7. mark the exif data so that it now has orientation of 1
#     exif_data[ORIENTATION_TAG_NUM] = 1

#     # 8. copy the old exif data to this new image while saving
#     image2.save(sys.argv[2], exif=exif_data)

#     #9. close the new file
#     image2.close()

# # 10. close the original
# image.close()
# print('done.')


######################
#   testing the correct_orientation() function
#

if len(sys.argv) == 3:
    correct_orientation(sys.argv[1], sys.argv[2], True)

elif len(sys.argv) == 2:
    # correct_orientation(sys.argv[1], sys.argv[1], True)
    exit('todo: implement over-writing')

else:
    print('that is not the correct usage. try again')
