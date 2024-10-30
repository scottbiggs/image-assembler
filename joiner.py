#   Simply joins two image files.  The first is on top of the second.
#

import os
import math
import sys      # for command line arguments
from PIL import Image
from PIL import ImageOps


############################
#   constants
#

USAGE = """
Joiner - a program to stitch together two images.

Usage:
    joiner <file1_name> <file2_name> +[file?_name] [-v] [-ov <integer>] [-off <integer>] [-o out_file] [-debug]

Joins files vertically or horizontally or vertically (using the -v options).  File1 will be
left-most (or top), file2 will be next, file3 will be after that, and so on for as many files
as you want to join.

The default new filename will the name of the first file, a dash (minus sign), and the name of
the last file.  To specify the output file, use the -o option.

The top and bottom file should be the same width (unless -f option is used).

-v      Join vertically instead of horizontally.  The first file will
        be on top, the second file will be on the below that, etc.

-d      Don't force the files to join if their heights (widths if -v is used) 
        don't match.  The final height (width) will be the same as the 
        tallest (widest) file, and the shorter (thinner) file will be centered.

-o      Use to specify the output filename. Will overwrite if name already exists.

-ov     Specify the number of pixels that the images overlap with this.

-off    Change the offset from center by this amount.  Use to re-align images that were
        poorly cropped to begin with.  Can be positive or negative.

-debug  Print debug info.

"""

# command line param that indicates the files should be joined horizontally
# instead of vertically
JOIN_VERT = '-v'

# indicates that we should NOT force the two files to fit, even if their
# widths are different.
DONT_FORCE_PARAM = '-d'

# Indicates that the following param is the output name for the new file
# (instead of using the default).
OUTPUT_PARAM = '-o'

# Indicates that the following is an integer that specifies how many pixels
# overlap in the images.
OVERLAP_PARAM = '-ov'

# Indicates that the following param is an integer to specify how many pixels
# to offset from center.
OFFSET_PARAM = '-off'

# indicates that all debug messages need to be displayed
DEBUG_PARAM = '-debug'

# dictionary key for Orientation in exif data
ORIENTATION_TAG_NUM = 274

# names for temp files which will be deleted in the process
UNIQUE_SEED = 'wosi37cxi.jpg'

# If the average difference between two lines is less than this, then it's
# probably the same line and should be skipped when joining the two files.
# NOTE: this is the threshold PER PIXEL, not an entire line.
SAME_PIXEL_THRESHOLD = 0.04


############################
#   globals
#

# when True, use a horizontal (false means vertical joining)
join_horizonatally = True

# when True, force the files to join, even if the widths don't match.
force_fit = True

debug = False

# List of the names of the input files in order
filenames = []

# name of the new output file
new_filename = ""

# The number of pixels to offset the second (or successive) images.
offset_pixels = 0

# The number of pixels that overlap between successive images
overlap_pixels = 0


############################
#   functions
############################

#########
#   Parses the params and does the global settings appropriately.
#
#   side effects:
#       NOTE: If this detects odd params, this will also exit the program.
#
#       filenames[]         An array of the input file names will be created.
#
#       new_filename        The name of the new file to be created
#
#       join_horizonatally  Will be set to True iff one of the params is '-h'
#
#       force_fit           Will be set to True only if one of the params is '-f'
#
#       debug               Will be set to True only if one of the params is '-d'
#
def parse_params():
    # Note that sys.argv[0] is always 'joiner.py' and its path, so that
    # counts as the first argument.

    global filenames
    global new_filename
    global join_horizonatally
    global force_fit
    global debug
    global offset_pixels
    global overlap_pixels


    # loop through all the params
    counter = 1
    while counter < len(sys.argv):
        this_param = sys.argv[counter]

        if debug:
            print(f'counter = {counter}.  this_param = {this_param} (lowercase = {this_param.lower()})')

        if this_param.lower() == JOIN_VERT:
            join_horizonatally = False
            if debug:
                print('   join_horizonatally is set to False')

        elif this_param.lower() == DONT_FORCE_PARAM:
            force_fit = False
            if debug:
                print('   force_fit is set to False')

        elif this_param.lower() == DEBUG_PARAM:
            debug = True
            if debug:
                print('   debug is set to True')

        elif this_param.lower() == OUTPUT_PARAM:
            counter += 1
            new_filename = sys.argv[counter]
            if debug:
                print(f'   new output name: {new_filename}')

        elif this_param.lower() == OFFSET_PARAM:
            counter += 1
            offset_pixels = int(sys.argv[counter])
            if debug:
                print(f'   offset: {offset_pixels}')

        elif this_param.lower() == OVERLAP_PARAM:
            counter += 1
            overlap_pixels = int(sys.argv[counter])
            if debug:
                print(f'   overlap: {overlap_pixels}')

        # From here on out these are input filenames.
        # Since they go in order, it's pretty easy to figure out which one.
        else:
            filenames.append(this_param)
            if debug:
                print(f'   input filename {this_param} added to list as element {len(filenames)}')

        counter += 1

    #last check for completeness
    if len(filenames) < 2:
        print("Hmmm, can't seem to find enough input files.  Try again. ")
        exit(USAGE)

    if debug:
        print('parse_params() results:')
        print(f'   filenames = {filenames}')
        print(f'   new_filename = {new_filename}')
        print(f'   join horiz = {join_horizonatally}')
        print(f'   force fit = {force_fit}')


#########
#   Finds the suffix in a filename.  If there is no extension, then this
#   returns the entire string.
#
#   examples:
#       myfun.txt  =>  myfun
#       bad.filename.jpg  => bad.filename
#       foo  =>  foo
#
def get_file_prefix(filename):
    outfile = filename

    dot_index = filename.rfind('.')     # returns -1 if no '.' found
    if dot_index != -1:
        # continue only if no extension found
        outfile = filename[:dot_index]

    return outfile


#########
#   If new_filename is empty, this generates it based on the list of
#   input files.
#
#   preconditions
#       filenames[]         Holds the names of the input files.
#   
#       new_filename        May be empty or already hold an output name.
#
#   returns
#       The correct new output name.  If new_filename is already used, then
#       it will be unchanged.
#    
def create_output_filename():
    global new_filename
    global filenames

    if len(new_filename) != 0:
        # already contains a string--use it as the output file name
        return new_filename

    start_name_prefix = get_file_prefix(filenames[0])
    end_name_prefix = get_file_prefix(filenames[-1])   # python way of getting last element in list

    new_output_file = start_name_prefix + ' - ' + end_name_prefix + '.jpg'
    if debug:
        print(f'   new_output_file = {new_output_file}')
    return get_unique_name(new_output_file)     # make sure we don't overwrite some file


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
#   Crops from the center of the given image.  If the crop dimensions are
#   bigger than the given image, the new image will have black borders.
#
#   input
#       pil_img                     The image to crop
#
#       crop_width, crop_height     The new width and height of the image
#
#   returns
#       A new cropped image of pil_img.
#
def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


#########
#   Finds a unique filename--or at least one that doesn't exist in the current
#   directory.
#
#   input
#       seed        The first filename to try.  May have an extension.
#
#   returns
#       A name unique to the current directory.  If none can be found
#       then None is returned (rather unlikely!).
#
def get_unique_name(seed):
    # split up the seed filename into parts
    prefix, extension = os.path.splitext(seed)
    if debug:
        print(f'get_unique_name(), prefix = {prefix}, extension = {extension}')

    current_name = f'{prefix}{extension}'
    unique_suffix = 0       # int

    # check to see if the name is used
    while os.path.exists(current_name):
        unique_suffix += 1
        current_name = f'{prefix}_{unique_suffix}{extension}'

        # give up after maxint tries.
        if unique_suffix == sys.maxsize:
            print('Unable to find a unique name for our file!!!')
            return None

    return current_name


#########
#   Joins two files vertically.
#
#   params
#       images_list         List of images to join
#       out_file            filename for the new output file
#       overlap             number of pixels to overlap the images
#       offset              number of pixels to force the 2nd image to move (positive
#                               moves right) when joining. 0 means no offset
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
def join_files_vertically(images_list, out_file, overlap, offset, force = False):

    if debug:
        print(f'joining files vertically, outfile = {out_file}, overlap = {overlap}, offset = {offset}, force = {force}')

    # width to use if we're not Forcing
    first_width = images_list[0].width    
    widest = first_width
    narrowest = first_width

    # create width adjustment list for each image
    width_adjustment_list = [0] * len(images_list)  # python way of creating a list of zeros


    # Check for correct width--all files.  While we're at it,
    # figure out the narrowest and widest width.
    for image in images_list:
        if image.width != first_width:
            if force == False:
                print('Images do not have the same width--aborting!')
                return False

            if image.width < narrowest:
                narrowest = image.width
            elif image.width > widest:
                widest = image.width

    if narrowest != widest:
        if force == False:          # todo: does this ever happen?
            print('Images do not have the same width--aborting!')
            return False

        # It's time to FORCE the issue!  hehe
        # Make sure the new width is the widest width.  And set the 
        # offsets needed to center the less wide pieces.
        for i in range(len(images_list)):
            this_width = images_list[i].width
            width_adjustment_list[i] = int((widest - this_width) / 2)

            if debug:
                print(f'image[{i}] with width {this_width} has adjustment of {width_adjustment_list[i]}')


    # figure out height of output image
    out_image_height = 0
    for image in images_list:
        out_image_height += image.height - overlap

    # new image combines heights
    out_image = Image.new('RGB', (widest, out_image_height))

    # Paste the pieces (centering, which will do nothing if the width already matches
    # the image width) together. Don't forget the offset!
    paste_line = 0
    for i in range(len(images_list)):
        if i == 1:
            # only the 2nd and later images can have an offset and overlap
            out_image.paste(images_list[i], (width_adjustment_list[i] + offset, paste_line - overlap))
        else:
            out_image.paste(images_list[i], (width_adjustment_list[i], paste_line))
            
        paste_line += images_list[i].height - overlap

    # Save result and clean up
    out_image.save(out_file)
    out_image.close()

    return True


#########
#   Joins two files horizontally.
#
#   params
#       images_list         list of images to join
#       out_file            filename for the new output file
#       overlap             number of pixels to overlap the images
#       offset              number of pixels to force the 2nd image to move (positive
#                               moves down) when joining. 0 means no offset
#       force               force the files together, even if the heights don't match
#
#   side effects
#       A new file will be created with the given output file name.  If it already
#       exists, then it will be overwritten.
#
#   returns
#       True    - file created successfully
#       False   - problem (probably the two input files are different heights)
#
def join_files_horizontally(images_list, out_file, overlap, offset, force = False):

    if debug:
        print(f'joining files horizontally, outfile = {out_file}, overlap = {overlap}, offset = {offset}, force = {force}')

    # height to use if we're not forcing
    first_height = images_list[0].height
    tallest = first_height
    shortest = first_height

    # create height adjustment list for each image to join
    height_adjustment_list = [0] * len(images_list)

    # check for correct height--all files.  And while we're at it
    # figure out the tallest and shortest heights.
    for image in images_list:
        if image.height != first_height:
            if force == False:
                print('Images do not have the same height--aborting!!')
                return False

            if image.height < shortest:
                shortest = image.height
            elif image.height > tallest:
                tallest = image.height

    # see if there are height descrepencies.
    if shortest != tallest:
        if force == False:      # todo: shouldn't this never happen?
            print('Images do not have the same height--aborting!!')
            return False

        # It's time to Force the issue :)
        # Make sure the new height is the tallest of the inputs.   
        # And set the offsets needed to center the less tall pieces.
        for i in range(len(images_list)):
            this_height = images_list[i].height
            height_adjustment_list[i] = int((tallest - this_height) / 2)

            if debug:
                print(f'image[{i}] with height {this_height} has adjustment of {height_adjustment_list[i]}')


    # figure out width of output image
    out_image_width = 0
    for image in images_list:
        out_image_width += image.width - overlap

    # new image combines widths
    out_image = Image.new('RGB', (out_image_width, tallest))

    # Paste the pieces (centering, which will do nothing if the height already
    # matches the image height) together.  Don't forget to add the offset!
    paste_line = 0
    for i in range(len(images_list)):
        if i >= 1:
            # only do the 2nd, 3rd, etc images with an offset (and overlap)!
            out_image.paste(images_list[i], (paste_line - overlap, height_adjustment_list[i] + offset))
        else:
            out_image.paste(images_list[i], (paste_line, height_adjustment_list[i]))

        paste_line += images_list[i].width - overlap

    # save and clean up
    out_image.save(out_file)
    out_image.close()

    return True


#########
#   Joins two files into one.  The output will have the top file immediately
#   above the bottom file.  If the files are different widths, then this
#   does nothing.
#
#   params
#       in_file_list        list of files to join (in order)
#       out_file            filename for the new output file.
#       offset              number of pixels to offset the 2nd file (default is 0)
#       force               force the files together, even if the widths don't match
#
#   preconditions
#       join_horizonatally  If this is true, initiate a horizontal joining of
#                           the files.
#
#   side effects
#       A new file will be created with the given output file name.  If it already
#       exists, then it will be overwritten.
#
#   returns
#       True    - file created successfully
#       False   - problem (probably the two input files are different widths)
#
def join_files(infile_list, out_file, offset, force = False):

    tmp_name_list = []
    name_to_delete_list = []

    # First things first: check to see if these files need to have
    # their orientation corrected.  If they do, correct it and add
    # the new temporary filename to the list of input files.  If it
    # doesn't, simply add the original name to the input file list.
    for infile_name in infile_list:
        if get_orientation_exif_filename(infile_name) > 1:
            tmp_filename = get_unique_name(UNIQUE_SEED)
            correct_orientation(infile_name, tmp_filename)            
            tmp_name_list.append(tmp_filename)
            name_to_delete_list.append(tmp_filename)        

            if debug:
                print(f'orientation corrected for {infile_name}')

        else:
            tmp_name_list.append(infile_name)


    # create image list
    in_image_list = []
    for filename in tmp_name_list:
        try:
            image = Image.open(filename)
            in_image_list.append(image)

        except:
            print(f'{filename} is not an image file--aborting!')
            # try to clean up the temp files
            for tmp_file in name_to_delete_list:
                os.remove(tmp_file)
            return False


    # Now we have our list of Images to join, finally!  Let's do it.
    return_val = False

    if join_horizonatally:
        return_val = join_files_horizontally(in_image_list, out_file, overlap_pixels, offset_pixels, force)
    else:
        return_val = join_files_vertically(in_image_list, out_file, overlap_pixels, offset_pixels, force)

    for image in in_image_list:
        image.close()

    # remove tmp files
    for tmp_file in name_to_delete_list:
        os.remove(tmp_file)

    return return_val


#########################################################
#   begin
#########################################################

parse_params()
new_filename = create_output_filename()

print(f'joining: {filenames} => {new_filename}')

result = join_files(filenames, new_filename, offset_pixels, force_fit)

if result:
    print(f'successfully joined {filenames} => {new_filename}')

###################
# testing

# top_image = None
# bottom_image = None

# try:
#     top_image = Image.open(top_filename)
#     print(f'opened {top_filename}')

#     bottom_image = Image.open(bottom_filename)
#     print(f'opened {bottom_filename}')

# except:
#     exit('unable to open a file!')

# # clean up
# if top_image != None:
#     top_image.close()
# if bottom_image != None:
#     bottom_image.close()

# print('done')

