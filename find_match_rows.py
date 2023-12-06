#   Finds the rows within two images that best match.
#
#   O(n^2) as it does a line-by-line comparison between the
#   two files.  But command line params can greatly reduce this
#   to O(n).
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
find_match_rows - a program to figure out which rows within two
image files that best match.  The match number returned means
how good a match was found.  The lower the better match (0 = perfect).

find_match_rows <image1> <image2> [row] [-d]

[row]   The optional [row] param will only compare that row in the first
        file to all the rows in the second file.  Must come AFTER the two
        image file names.

-d      Turn on debug statements.  May appear anywhere.

NOTE: the two images need to be the same width.  Maybe I'll work
    on that later.

NOTE2: this assumes that the images are already in the appropriate
    orientation.  Yes, I'm lazy--no orientation correcting is done here.

"""

DEBUG_PARAM = '-d'


############################
#   globals
#

debug = False

top_image_filename = None

bottom_image_filename = None

# When this is non-negative, indicates that ONLY this row in the
# top image should be used.
master_row = -1


############################
#   functions
############################

#########
#   Parses the params and does the global settings appropriately.
#
#   preconditions & side effects
#
#       top_image_filename      These are the input file names.  Should be
#       bottom_image_filename   'None' when called.
#
#       master_row              If the param exists, it'll be changed to
#                               the row number specified.  Should be '-1'
#                               when called.
#
def parse_params():
    # Note that sys.argv[0] is always 'joiner.py' and its path, so that
    # counts as the first argument.

    global debug
    global top_image_filename
    global bottom_image_filename
    global master_row

    # loop through the args
    for arg in sys.argv:

        if arg == sys.argv[0]:      # skip the first arg--it's always the name of the script
            continue

        if arg.lower() == DEBUG_PARAM:
            debug = True

        elif top_image_filename == None:
            top_image_filename = arg

        elif bottom_image_filename == None:
            bottom_image_filename = arg

        elif master_row == -1:
            try:
                master_row = int(arg)

            except:
                print(f'Unable to parse arg: {arg}. Aborting!')
                exit(USAGE)

        else:
            exit(USAGE)


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


#########################################################
#   begin
#########################################################

parse_params()

# open images
top_image = None
bottom_image = None

try:
    top_image = Image.open(top_image_filename)
    bottom_image = Image.open(bottom_image_filename)
except:
    print('Unable to open images!')
    exit(USAGE)

if top_image.width != bottom_image.width:
    print('Images need to be the same width.  Aborting!!!')
    exit()


best_match = sys.maxsize        # the best match distance
best_top_row = 0
best_bottom_row = 0
top_row_start = 0
top_row_end = top_image.height

# This makes the loop happen only on the 1 master row
# (if it's specified).
if master_row != -1:
    top_row_start = master_row
    top_row_end = master_row + 1

# the maps are needed for find_difference_between_two_rows()
top_image_map = top_image.load()
bottom_image_map = bottom_image.load()


# O(n^2)
for i in range(top_row_start, top_image.height):
    for j in range(0, bottom_image.height):
        current_match = find_difference_between_two_rows(
                top_image_map, i, top_image.width,
                bottom_image_map, j, bottom_image.width,
            )

    if current_match < best_match:
        best_match = current_match
        best_top_row = i
        best_bottom_row = j
        if debug:
            print(f'...Found better match: {current_match} top row = {best_top_row}, bottom row = {best_bottom_row}')

print(f'Best match: {current_match} top row = {best_top_row}, bottom row = {best_bottom_row}')

top_image.close()
bottom_image.close()

