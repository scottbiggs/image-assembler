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

-o      Optimize stitching location.  Joiner will try to find the best
        place to stitch together the two images and stitch them at that
        location.  This is really nice if there for overlapping images. If
        no good location is found, then the edges will be joined (default).

"""

# indicates that we should FORCE the two files to fit, even if their
# widths are different.
FORCE_PARAM = '-f'

# indicates that the program should find the best place to stitch the
# two files together.
OPTIMIZE_PARAM = '-o'

# indicates that all debug messages need to be displayed
DEBUG_PARAM = '-d'

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

# when True, try to find the best place to stitch the two images together.
optimize_stitching = False

# These are the names of the files to read and write
top_filename = ""
bottom_filename = ""
new_filename = ""


############################
#   functions
############################

#########
#   Parses the params and does the global settings appropriately.
#
#   side effects:
#       top_filename        These are the input file names.
#       bottom_filename
#
#       new_filename        The name of the new file to be created
#
#       force_fit           Will be set to True only if one of the params is '-f'
#
#       optimize_stitching  Set to true only if one of the params is '-o'
#
#       debug               Will be set to True only if one of the params is '-d'
#
def parse_params():
    # Note that sys.argv[0] is always 'joiner.py' and its path, so that
    # counts as the first argument.

    global top_filename
    global bottom_filename
    global new_filename
    global force_fit
    global optimize_stitching
    global debug

    # take care of the easy cases first
    if len(sys.argv) < 4 or len(sys.argv) > 7:
        exit(USAGE)

    # no extra params--easy!
    if len(sys.argv) == 4:
        top_filename = sys.argv[1]
        bottom_filename = sys.argv[2]
        new_filename = sys.argv[3]
        return

    # loop through all the params
    counter = 1
    while counter < len(sys.argv):
        this_param = sys.argv[counter]

        if debug:
            print(f'counter = {counter}.  this_param = {this_param} (lowercase = {this_param.lower()})')

        if this_param.lower() == FORCE_PARAM:
            force_fit = True
            if debug:
                print('   force_fit is set to True')

        elif this_param.lower() == OPTIMIZE_PARAM:
            optimize_stitching = True
            if debug:
                print('   optimize_stitching is set to True')

        elif this_param.lower() == DEBUG_PARAM:
            debug = True
            if debug:
                print('   debug is set to True')

        # From here on out, this much be either an input or output filename.
        # Since they go in order, it's pretty easy to figure out which one.
        elif not top_filename:
            top_filename = this_param
            if debug:
                print(f'   top_filename set to {top_filename}')

        elif not bottom_filename:
            bottom_filename = this_param
            if debug:
                print(f'   bottom_filename = {bottom_filename}')

        elif not new_filename:
            new_filename = this_param
            if debug:
                print(f'   new_filename = {new_filename}')

        else:
            # Something fishy went on here
            if debug:
                print(f'   something fishy!  counter = {counter}')
            exit(USAGE)

        counter += 1

    #last check for completeness
    if not top_filename or not bottom_filename or not new_filename:
        exit(USAGE)


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
#   Tries to find the best place to stitch together the images.
#   This will only try the bottom third and the top third of each
#   image before giving up.
#
#   input
#       top_image, bottom_image     These are graphic images that are already
#                                   opened and verified.
#
#   returns
#       A list of two numbers [a, b].  The first number is the number of 
#       lines from the bottom of the first image that best matches.  
#       The second number is the number of lines from the top image that 
#       best matches.  If no good match was found, then [0, 0] is returned.
#       
def find_optimal_join_location(top_image, bottom_image):
    if debug:
        print('find_optimal_join_location()')


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

parse_params()

print(f'joining {top_filename} to {bottom_filename} => {new_filename}')
# result = join_files(top_filename, bottom_filename, new_filename, force_fit)

# if result:
#     print(f'successfully joined {top_filename} to {bottom_filename} => {new_filename}')

print(f'   and debug = {debug}, optimize_stitching = {optimize_stitching}, force_fit = {force_fit}')