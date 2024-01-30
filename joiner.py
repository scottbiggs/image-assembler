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
    joiner <file1_name> <file2_name> +[file?_name] [-h] [-f] [-s]|[-S <num>] [-o out_file] [-d]

Joins files vertically or horizontally (using the -h options).  File1 will be on top 
(or left-most), file2 will be next, file3 will be after that, and so on for as many files
as you want to join.

The default new filename will the name of the first file, a dash (minus sign), and the name of
the last file.  To specify the output file, use the -o option.

The top and bottom file should be the same width (unless -f option is used).

-h      Join horizontally instead of vertically.  The first file will
        be on the left, the second file will be on the right, etc.

-f      Force the files to join, even if their widths (heights if -h is used) 
        don't match.  The final width (height) will be the same as the 
        widest (tallest) file, and the thinner (shorter) file will be centered.

-s      Optimize stitching location.  Joiner will try to find the best
        place to stitch together the two images and stitch them at that
        location.  This is really nice if there for overlapping images. If
        no good location is found, then the edges will be joined (default).

-S      Optimize stiching location, but check this percentage amount.
        15 will check the first fifteen percent, 25 will check a fourth,
        and so on.  The default is 33 (or a third).

-o      Use to specify the output filename.

-d      Print debug info.

"""

# command line param that indicates the files should be joined horizontally
# instead of vertically
JOIN_HORIZ = '-h'

# indicates that we should FORCE the two files to fit, even if their
# widths are different.
FORCE_PARAM = '-f'

# indicates that the program should find the best place to stitch the
# two files together.
OPTIMIZE_PARAM = '-s'

# Check for the best place, but also tell how much of the file to
# test.  This is a number that means percent, so 25 will check 25%.
OPTIMIZE_PARAM_WITH_PERCENT = '-S'

# Indicates that the following param is the output name for the new file
# (instead of using the default).
OUTPUT_PARAM = '-o'

# The percentage of the entire portion of the images that is checked
# if we're trying to find an optimal place to stitch together.
# 33 means that we'll only check 33% of the images.
DEFAULT_OPTIMIZE_AREA = 33

# The distance between two pixel colors beyond which we'll call them
# 'different'.  This is used when checking if two pixels are similar.
# The lower the number the more similar.
DEFAULT_SIMILAR_PIXEL_THRESHOLD = 18

# indicates that all debug messages need to be displayed
DEBUG_PARAM = '-d'

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

# when True, use a horizontal instead of vertical joining
join_horizonatally = False

# when True, force the files to join, even if the widths don't match.
force_fit = False

debug = False

# when True, try to find the best place to stitch the two images together.
optimize_stitching = False

# The percent of the bottom file to check for optimal stitching location.
optimize_area = DEFAULT_OPTIMIZE_AREA

# List of the names of the input files in order
filenames = []

# name of the new output file
new_filename = ""


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
#       optimize_stitching  Set to true only if one of the params is '-o'
#
#       debug               Will be set to True only if one of the params is '-d'
#
#       optimize_area       Will be set if the params specify.
#
def parse_params():
    # Note that sys.argv[0] is always 'joiner.py' and its path, so that
    # counts as the first argument.

    global filenames
    global new_filename
    global join_horizonatally
    global force_fit
    global optimize_stitching
    global debug
    global optimize_area

    # loop through all the params
    counter = 1
    while counter < len(sys.argv):
        this_param = sys.argv[counter]

        if debug:
            print(f'counter = {counter}.  this_param = {this_param} (lowercase = {this_param.lower()})')

        if this_param.lower() == JOIN_HORIZ:
            join_horizonatally = True
            if debug:
                print('   join_horizonatally is set to True')

        elif this_param.lower() == FORCE_PARAM:
            force_fit = True
            if debug:
                print('   force_fit is set to True')

        elif this_param == OPTIMIZE_PARAM:
            optimize_stitching = True
            if debug:
                print('   optimize_stitching is set to True')

        elif this_param == OPTIMIZE_PARAM_WITH_PERCENT:
            optimize_stitching = True
            counter += 1

            # now get the number for the percent to check
            this_param = sys.argv[counter]
            try:
                optimize_area = int(this_param)
            except:
                if debug:
                    print(f'Error when trying to read the stitching amount! (what is {this_param}???)')
                exit(USAGE)

            if debug:
                print(f'   optimize_stitching is True, percent = {optimize_area}')

        elif this_param.lower() == DEBUG_PARAM:
            debug = True
            if debug:
                print('   debug is set to True')

        elif this_param.lower() == OUTPUT_PARAM:
            counter += 1
            new_filename = sys.argv[counter]
            if debug:
                print(f'   new output name: {new_filename}')

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
        print(f'   optimize_stitching = {optimize_stitching}')
        print(f'   optimize_area = {optimize_area}')


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

    new_output_file = start_name_prefix + '-' + end_name_prefix + '.jpg'
    if debug:
        print(f'   new_output_file = {new_output_file}')
    return new_output_file


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
#   Finds the luminescence of a pixel (which should be RGB).
#
def get_luminescence(pixel):
    return (0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2])


#########
#   Finds how similar the pixels are (in luminescence).  The higher the
#   number, the less similar.  0 means exact same luminescence.
#
def get_similarity(pix1, pix2):
    return abs(get_luminescence(pix1) - get_luminescence(pix2))


#########
#   Finds the color distance bewteen two pixels.
#   Uses pythagorean method.
#
def get_distance_between_pixels(pix1, pix2):
    return math.sqrt(
                     ((pix1[0] - pix2[0]) ** 2)
                     + ((pix1[1] - pix2[1]) ** 2)
                     + ((pix1[2] - pix2[2]) ** 2)
                    )

#########
#   Determines if the two given pixels are similar via the supplied
#   threshold.
#
def is_similar(pix1, pix2, threshold = DEFAULT_SIMILAR_PIXEL_THRESHOLD):
    return get_similarity(pix1, pix2) < threshold


#########
#   Returns the difference between the given rows of two images.
#   Just a simple Hue comparison.
#
#   input
#       image_map1  Reference to the first image map.
#       row1        The row in the first image to compare.
#       row1_width  Width of this row in pixels.
#
#       image_map2  Reference to 2nd image map.
#       row2        The row in the second image to compare.
#       row2_width  Width of row.
#
#       force       If True, then force the comparison, even if the images
#                   are different widths.  This means centering the smaller
#                   image within the larger and comparing thusly.
#
#   returns
#       0 = perfect match
#       otherwise the bigger the worse the match
#       None means error (either not a graphics file or different widths)
#
def find_difference_between_two_rows(image_map1, row1, row1_width, 
                                     image_map2, row2, row2_width,
                                     force = False):

    # the running total of the distances
    distance_sum = 0.0
    
    # Run this section when not forcing or the odd force case where
    # both are the same width.
    if (not force) or (row1_width == row2_width):
        # check widths error (error when NOT forcing)
        if row1_width != row2_width:
            return None

        # This is the easy one: go through each pixel and compare

        for i in range(0, row1_width):
            # get the pixels at the point in the row
            pixel1 = image_map1[i, row1]
            pixel2 = image_map2[i, row2]

            # The distance between the two pixels is the square root of
            # the differences of the color planes.
            dist = get_distance_between_pixels(pixel1, pixel2)
            distance_sum += dist

        # return the average per pixel
        return distance_sum / row1_width


    else:
        if row1_width < row2_width:
            # Loop through row1.
            # But we need to find where to start in row2
            row2_start = int((row2_width - row1_width) / 2)
            for i in range(0, row1_width):
                pixel1 = image_map1[i, row1]
                pixel2 = image_map2[i + row2_start, row2]

                dist = get_distance_between_pixels(pixel1, pixel2)
                distance_sum += dist

            return distance_sum / row1_width

        else:
            # Row 2 is shorter.  Figure out where to start row 1 to
            # match row 2.
            row1_start = int((row1_width - row2_width) / 2)
            for i in range(0, row2_width):
                x1 = i + row1_start
                y1 = row1

                x2 = i
                y2 = row2

                # print(f'x1, y1 = [{x1}, {y1}], x2, y2 = [{x2}, {y2}]')
                pixel1 = image_map1[i + row1_start, row1]
                pixel2 = image_map2[i, row2]

                dist = get_distance_between_pixels(pixel1, pixel2)
                # print(f'--dist = {dist}')
                distance_sum += dist

            return distance_sum / row2_width


#########
#   Tries to find the best place to stitch together the images.
#   This will only try the bottom third and the top third of each
#   image before giving up.
#
#   preconditions
#       optimize_area               The part of the bottom to check.
#
#   input
#       top_image, bottom_image     These are graphic images that are already
#                                   opened and verified.
#
#       force           When True, force the files to fit, even if the
#                       widths are different.
#
#       NO...see below!!!
#   returns
#       A list of two numbers [a, b].  The first number is the number of 
#       lines from the bottom of the first image that best matches.  
#       The second number is the number of lines from the top image that 
#       best matches.  If no good match was found, then [0, 0] is returned.
#
#   returns
#       The number of the line in the bottom file that best matches the
#       bottom row of the top file.  0 is the default (if no threshold
#       is met).
#       
def find_optimal_join_location(top_image, bottom_image, force):

    # the maps are needed for find_difference_between_two_rows()
    top_image_map = top_image.load()
    bottom_image_map = bottom_image.load()

    # figure out how many lines we're inspecting in each image
    top_image_num_lines_to_inspect = round((optimize_area / 100) * top_image.height)
    bottom_image_num_lines_to_inspect = round((optimize_area / 100) * bottom_image.height)

    # Make a range for the rows of the bottom image to compare with the bottom
    # row of the top image.
    bottom_range = range(0, bottom_image_num_lines_to_inspect + 1)


    # These are the lines that match the best so far.  These are described
    # from the bottom of the top and the top of the bottom (where they would
    # join if they were perfectly aligned).
    top_file_best_line = top_image.height - 1
    bottom_file_best_line = 0

    # The value of the best match so far.  The lower the better.
    current_best_match = sys.maxsize


    # See what the bottom of the top image matches within the bottom image
    # inspection area.
    for i in bottom_range:
        diff = find_difference_between_two_rows(top_image_map, top_image.height - 1, top_image.width,
                                                bottom_image_map, i, bottom_image.width,
                                                force)
        if debug:
            print(f'find_optimal(), i = {i}, diff = {diff}')
        if diff < current_best_match:
            bottom_file_best_line = i
            current_best_match = diff
            if debug:
                print(f'   (i = {i}): found better match ({current_best_match}): bottom file line = {bottom_file_best_line}]')

    # if debug:
    #     print(f'Best match is {current_best_match} for top line: {top_file_best_line}, bottom line: {bottom_file_best_line}')

    # return [top_file_best_line, bottom_file_best_line]

    # if this line is exactly the same, skip it.
    if current_best_match < (SAME_PIXEL_THRESHOLD * max(top_image.width, bottom_image.width)):
        bottom_file_best_line += 1

    if debug:
        print(f'Best match for bottom of the top file is: bottom file line: {bottom_file_best_line}')
    return bottom_file_best_line


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
#       A name unique to the current directory.  If non can be found
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
#   Joins two files vertically.  This is the default.
#
#   params
#       images_list         List of images to join
#       out_file            filename for the new output file
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
# def join_files_vertically(top_image, bottom_image, out_file, force = False):
def join_files_vertically(images_list, out_file, force = False):

    if debug:
        print(f'joining files vertically, force = {force}')

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
        if force == False:
            print('Images do not have the same width--aborting!')
            return False

        # It's time to FORCE the issue!  hehe
        # Make sure the new width is the widest width.  And set the 
        # offsets needed to center the less wide pieces.
        for i in range(len(images_list)):
            this_width = images_list[i].width
            width_adjustment_list[i] = int((widest - this_width) / 2)

            if debug:
                print(f'image[{i}] with width {this_width} has adjustement of {width_adjustment_list[i]}')


        # # It's time to FORCE the issue!  hehe
        # # Make sure our new width is the max width.  And set the offset
        # # needed to center the less wide portion.
        # if top_image.width > bottom_image.width:
        #     new_width = top_image.width     # yeah redundant, but makes code easier to follow
        #     bottom_width_adjustment = int((top_image.width - bottom_image.width) / 2)
        # else:
        #     new_width = bottom_image.width
        #     top_width_adjustment = int((bottom_image.width - top_image.width) / 2)

        # if debug:
        #     print(f'top_width_adjustment = {top_width_adjustment}')
        #     print(f'bottom_width_adjustment = {bottom_width_adjustment}')



    # stich_row = 0  -------- no longer optimizing join location

    # figure out height of output image
    out_image_height = 0
    for image in images_list:
        out_image_height += image.height


    # # do we need to optimize the joining location?  ----------- no longer doing this
    # if optimize_stitching:
    #     stich_row = find_optimal_join_location(top_image, bottom_image, force)

    #     # skip this optimal row--it's probably a repeat.  TODO: test this hypothesis extensively!
    #     out_image_height -= stich_row

    # new image combines heights
    out_image = Image.new('RGB', (widest, out_image_height))


    # # Figure out what part of the bottom to paste in.  This is the whole    ------------- no longer doing this
    # # of the bottom image if there is no optimized stitching.  If the stitching
    # # is optimized, then it's the stitch_row to the end of the bottom image.
    # used_bottom_part = bottom_image.crop((0,
    #                                       stich_row,
    #                                       bottom_image.width,
    #                                       bottom_image.height - 1
    #                                      ))
    # if debug:
        # print(f'cropping bottom image: ({bottom_width_adjustment}, {stich_row}, {bottom_image.width}, {bottom_image.height - 1})')


    # paste the pieces (centering, which will do nothing if the width already matches
    # the image width)
    paste_line = 0
    for i in range(len(images_list)):
        out_image.paste(images_list[i], (width_adjustment_list[i], paste_line))
        paste_line += images_list[i].height

    # out_image.paste(top_image, (top_width_adjustment, 0))
    # out_image.paste(used_bottom_part, (bottom_width_adjustment, top_image.height))


    # and save result and clean up
    out_image.save(out_file)
    out_image.close()

    return True


#########
#   Joins two files horizontally.
#
#   params
#       left_image          Image for the left file
#       right_image         Image for the right file
#       out_file            filename for the new output file.
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
def join_files_horizontally(left_image, right_image, out_file, force = False):

    if debug:
        print(f'joining files horizontally, force = {force}')

    new_height = left_image.height
    left_height_adjustment = 0          # offset to center the image
    right_height_adjustment = 0

    # check for correct height
    if left_image.height != right_image.height:
        if force == False:
            print('Images do not have the same height--aborting!!')
            return False

        # It's time to Force the issue :)
        # Make sure the new height is the max of the two.   
        # And set the offset needed to center the less tall portion. 
        if left_image.height > right_image.height:
            new_height = left_image.height
            right_height_adjustment = int((left_image.height - right_image.height) / 2)
        else:
            new_height = right_image.height
            left_height_adjustment = int((right_image.height - left_image.height) / 2)

        if debug:
            print(f'left_height_adjustment = {left_height_adjustment}')
            print(f'right_height_adjustment = {right_height_adjustment}')

    stich_row = 0
    out_image_width = left_image.width + right_image.width

    # optimize joining location?
    if optimize_stitching:
        exit('TODO: optimize stitching for horizontal joining!!!  Sorry.')

        # stich_row = find_optimal_join_location(top_image, bottom_image, force)

        # # skip this optimal row--it's probably a repeat.  TODO: test this hypothesis extensively!
        # out_image_height -= stich_row

    out_image = Image.new('RGB', (out_image_width, new_height))

    # paste the pieces (centering, which will do nothing if the images have
    # the same height).

    out_image.paste(left_image, (0, left_height_adjustment))
    out_image.paste(right_image, (left_image.width, right_height_adjustment))

    # and save and cleanup
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
def join_files(infile_list, out_file, force = False):

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
        return_val = join_files_horizontally(in_image_list, out_file, force)
    else:
        return_val = join_files_vertically(in_image_list, out_file, force)

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

result = join_files(filenames, new_filename, force_fit)

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

# optimal_loc = find_optimal_join_location(top_image, bottom_image)
# print(f'optimal location is {optimal_loc}')

# # clean up
# if top_image != None:
#     top_image.close()
# if bottom_image != None:
#     bottom_image.close()

# print('done')

