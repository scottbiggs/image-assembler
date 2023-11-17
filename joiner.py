#   Simply joins two image files.  The first is on top of the second.
#

import os
from time import sleep
import sys      # for command line arguments
from PIL import Image
from PIL import ImageOps


############################
#   constants
#

USAGE = """
Joiner - a program to stitch together two images.

Usage:
    joiner <top_file_name> <bottom_file_name> <output_file_name> [-f]

The first file will be on top, and the second file will be put below.
The top and bottom file should be the same width (except for below).

-f      Force the files to join, even if their widths don't match.
        The final widith will be the same as the widest file, and the
        thinner file will be centered.

"""

# indicates that we should FORCE the two files to fit, even if their
# widths are different.
FORCE_PARAM = "-f"

# dictionary key for Orientation in exif data
ORIENTATION_TAG_NUM = 274

# names for temp files which will be deleted in the process
TMP_FILE1 = 'jjjseeefffiisllbbblesjeo2982850039283jfoiesjeeqznwosi37.jpg'
TMP_FILE2 = 'sjfowwekkkeeeskskslavllelsjpelliseeingwjw228fh29837fh2fhslkskf.jpg'

############################
#   globals
#

# when True, force the files to join, even if the widths don't match.
force_fit = False

debug = False


############################
#   functions
############################

#########
#   Determines if the given Image has an Orientation exif attribute.
#
#   input
#       image       An Image (from PIL) that has already been loaded.
#
#   returns
#       0       - No orientation data found (could even be a non-image file!)
#       [1..9]  - The orientation of the file.  Note that 1 means that the
#                 image is not rotated at all.
#                 see:  https://jdhao.github.io/2019/07/31/image_rotation_exif_info/#exif-orientation-flag
#
def get_orientation_exif(image):
    orientation = 0
    exif_data = image.getexif()

    if exif_data is None:
        # no exif at all
        return orientation

    if ORIENTATION_TAG_NUM in exif_data:
        orientation = exif_data[ORIENTATION_TAG_NUM]
    return orientation


#########
#   Determines if the given file has an Orientation exif attribute.
#
#   input
#       filename    The name of the file to check
#
#   returns
#       0       - No orientation data found (could even be a non-image file!)
#       [1..9]  - The orientation of the file.  Note that 1 means that the
#                 image is not rotated at all.
#                 see:  https://jdhao.github.io/2019/07/31/image_rotation_exif_info/#exif-orientation-flag
#
def get_orientation_exif_filename(filename):
    orientation = 0
    image = None
    try:
        image = Image.open(filename)
    except:
        # not an image, therefore no exif possible
        return orientation

    orientation = get_orientation_exif(image)

    image.close()
    return orientation


#########
#   Creates a copy of the given image with the same orientation but
#   has an exif of 1 (not transposed).  All other exif info is
#   maintained.
#
#   preconditions:
#       The file DOES INDEED HAVE AN ORIENTATION EXIF DATA!!!
#       This will probably crash if it doesn't.  Call get_orientation_exif()
#       or get_orientation_filename() to find out.   :)
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
    exif_data = image1.getexif()

    # Create new transposed image.  Side effect of this is that no
    # exif data is kept into the transposed image.
    transposed_image = ImageOps.exif_transpose(image1)

    # modify exif data to reflect that image1 has been transposed
    # TODO: test to make sure that this still works if the exif is empty
    exif_data[ORIENTATION_TAG_NUM] = 1

    # write new file and close it
    transposed_image.save(outfile, exif = exif_data)
    transposed_image.close()

    # Close input file
    image1.close()

    return True


#########
#   Joins two files into one.  The output will have the top file immediately
#   above the bottom file.  If the files are different widths, then this
#   does nothing.
#
#   params
#       top_file            filename for the file on top
#       bottom_file         filename for the bottom file
#       out_file            filename for the new output file.
#       force               force the files together, even if the widths don't match
#
#   side effects
#       A new file will be created with the given output file name.  If it already
#       exists, then it will be overwritten.
#
#   returns
#       True    - file created successfully
#       False   - problem (probably the two input files are different widths)
#
def join_files(top_file, bottom_file, out_file, force = False):

    use_tmp1 = False
    use_tmp2 = False

    # First things first: check to see if these files need to have
    # their orientation corrected.
    if get_orientation_exif_filename(top_file) > 1:
        correct_orientation(top_file, TMP_FILE1)
        use_tmp1 = True
        if debug:
            print(f'orientation corrected for {top_file}')

    if get_orientation_exif_filename(bottom_file) > 1:
        correct_orientation(bottom_file, TMP_FILE2)
        use_tmp2 = True
        if debug:
            print(f'orientation corrected for {bottom_file}')

    try:
        if use_tmp1:
            top_image = Image.open(TMP_FILE1)
        else:
            top_image = Image.open(top_file)

        if use_tmp2:
            bottom_image = Image.open(TMP_FILE2)
        else:
            bottom_image = Image.open(bottom_file)

    except:
        print('One or more files were not image files--aborting!')
        # try to clean up
        if use_tmp1 and os.path.isfile(TMP_FILE1):
            os.remove(TMP_FILE1)
        
        if use_tmp2 and os.path.isfile(TMP_FILE2):
            os.remove(TMP_FILE2)

        return False

    new_width = top_image.width
    top_width_adjustment = 0        # offset to center image
    bottom_width_adjustment = 0

    # check for correct width
    if top_image.width != bottom_image.width:
        if force == False:
            print('Images do not have the same width--aborting!')
            return False

        # It's time to FORCE the issue!  hehe
        # Make sure our new width is the max width.  And set the offset
        # needed to center the less wide portion.
        if top_image.width > bottom_image.width:
            new_width = top_image.width     # yeah redundant, but makes code easier to follow
            bottom_width_adjustment = int((top_image.width - bottom_image.width) / 2)
        else:
            new_width = bottom_image.width
            top_width_adjustment = int((bottom_image.width - top_image.width) / 2)

    # new image combines heights
    out_image = Image.new('RGB', (new_width, top_image.height + bottom_image.height))

    # paste the pieces (centering, which will do nothing if the width already matches
    # the image width)

    out_image.paste(top_image, (top_width_adjustment, 0))
    out_image.paste(bottom_image, (bottom_width_adjustment, top_image.height))
    
    # out_image.paste(top_image, (top_width_adjustment, 0, 
    #                             top_image.width, top_image.height))
    # out_image.paste(bottom_image, (bottom_width_adjustment, top_image.height, 
    #                                bottom_image.width, top_image.height + bottom_image.height))

    # and save result
    out_image.save(out_file)

    # clean up
    out_image.close()
    bottom_image.close()
    top_image.close()

    if use_tmp1:
        os.remove(TMP_FILE1)        
    if use_tmp2:
        os.remove(TMP_FILE2)

    return True


#########################################################
#   begin
#########################################################

# Note that sys.argv[0] is always 'joiner.py' and its path, so that
# counts as the first argument.  Thus there should be 4 or 5 params.
# If there are 5 params, one must be '-f'.

# take care of the easy cases first
if len(sys.argv) < 4 or len(sys.argv) > 5:
    exit(USAGE)

if len(sys.argv) == 4:
    top = sys.argv[1]
    bottom = sys.argv[2]
    new = sys.argv[3]

# the only case left is a length of 5.  One of the params MUST be '-f'.
if len(sys.argv) == 5:
    force_fit = True
    if sys.argv[1].lower() == FORCE_PARAM:      # -f is first param (position 1)
        top = sys.argv[2]
        bottom = sys.argv[3]
        new = sys.argv[4]
    elif sys.argv[2].lower() == FORCE_PARAM:    # -f second param
        top = sys.argv[1]
        bottom = sys.argv[3]
        new = sys.argv[4]
    elif sys.argv[3].lower() == FORCE_PARAM:    # -f 3rd param
        top = sys.argv[1]
        bottom = sys.argv[2]
        new = sys.argv[4]
    elif sys.argv[4].lower() == FORCE_PARAM:    # -f is last param
        top = sys.argv[1]
        bottom = sys.argv[2]
        new = sys.argv[3]
    else:
        # couldn't find the '-f' param! aborting!
        exit(USAGE)


print(f'joining {top} to {bottom} => {new}')
result = join_files(top, bottom, new, force_fit)

if result:
    print(f'successfully joined {sys.argv[1]} to {sys.argv[2]} => {sys.argv[3]}')

