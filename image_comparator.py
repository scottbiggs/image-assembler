#   Handles manipulation of image data.
#

import math
from PIL import Image
from colormath.color_objects import LabColor, HSLColor      # takes a while
from colormath.color_conversions import convert_color       # takes a while too


####################
#   constants
####################

# Masks for RGB
RED_MASK = 0x10000
GREEN_MASK = 0x20000
BLUE_MASK = 0x40000

# Masks for HSL
HUE_MASK = 0x1
SATURATION_MASK = 0x2
LIGHT_MASK = 0x4

TOLERANCE = 12.0

####################
#   globals
####################

debug = False


####################
#   Determines if the given difference is small enough to consider
#   that the files should be connected.  While this is just a small
#   function, it's provided here as it makes sense for this module
#   to make this determination instead of something calling this
#   that doesn't have an inkling about graphics.
#
def is_difference_within_tolerance(difference):
    # Here is the fudge constant.  10 looks good for now.
    if (difference < TOLERANCE):
        return True
    else:
        return False


"""
####################
#   Compares the bottom of the first file with the top of the
#   second file and returns a value corresponding with how much
#   they differ.  A value of 0 is a perfect match.  Only cares
#   about the HUE of the colors.
#
#   returns None on error
#
def compare_edges_hue(file1, file2, debug):
    if debug:
        print(f'compare_edges ( {file1}, {file2} )')

    try:
        image1 = Image.open(file1)
        image2 = Image.open(file2)

    except:
        print('One or more files were not image files--aborting!')
        return
    
    # make sure that these have the same widths
    width = image1.width
    if (width != image2.width):
        print(f'compare_bottom_to_top( {file1}, {file2} ) Error!  Not same width!')
        return

    # this is the number for the bottom row of the file1
    bottom = image1.height - 1

    map1 = image1.load()
    map2 = image2.load()

    hue_distance_sum = 0.0

    # Loop through all the pixels in the two maps, keeping track of the
    # total difference between the H value (absolute) of all the corres-
    # ponding pixels.
    for x in range(width):
        # get the two pixels
        pixel1 = map1[x, bottom]
        pixel2 = map2[x, 0]

        # convert to HSL
        labcolor = LabColor(pixel1[0], pixel1[1], pixel1[2])
        pixel_hsl_1 = convert_color(labcolor, HSLColor)
        labcolor = LabColor(pixel2[0], pixel2[1], pixel2[2])
        pixel_hsl_2 = convert_color(labcolor, HSLColor)

        # increase the distance
        hue_distance_sum += abs(pixel_hsl_1.hsl_h - pixel_hsl_2.hsl_h)

    # done with images
    image2.close()
    image1.close()

    # average out the difference
    if (debug):
        print(f'   -> width = {width}')
        print(f'   -> total HUE distance = {hue_distance_sum}')
        print(f'   -> average HUE distance = {hue_distance_sum / width}')
    return hue_distance_sum / width
"""

"""
####################
#   Compares the bottom of the first file with the top of the
#   second file and returns a value corresponding with how much
#   they differ.  A value of 0 is a perfect match.
#
#   This version takes all the RGB values into account.
#
def compare_edges_rgb(file1, file2):
    print(f'comparing bottom (RGB) of {file1} to top of {file2}...')
    image1 = Image.open(file1)
    image2 = Image.open(file2)
    
    # make sure that these have the same widths
    width = image1.width
    if (width != image2.width):
        print(f'compare_bottom_to_top( {file1}, {file2} ) Error!  Not same width!')
        return

    # this is the number for the bottom row of the file1
    bottom = image1.height - 1

    map1 = image1.load()
    map2 = image2.load()

    distance_sum = 0.0

    # Loop through all the pixels in the two maps, keeping track of the
    # total color difference between of all the corresponding pixels.
    for x in range(width):
        # get the two pixels
        pixel1 = map1[x, bottom]
        pixel2 = map2[x, 0]

        # The distance between the two pixels is the square root of
        # the differences of the color planes.
        dist = (pixel1[0] - pixel2[0]) ** 2
        dist += (pixel1[1] - pixel2[1]) ** 2
        dist += (pixel1[2] - pixel2[2]) ** 2
        dist = math.sqrt(dist)        

        # increase the distance
        distance_sum += dist

    # done with images
    image2.close()
    image1.close()

    distance_ave = distance_sum / width

    # average out the difference
    if debug:
        print(f'   -> total distance = {distance_sum}')
        print(f'   -> width = {width}')
        print(f'   -> average = {distance_ave}')
    
    return distance_ave
"""

####################
#   Finds the average color within the given block.
#   Just the average, nothing fancy.
#
#   params
#       image_map       Reference to the image data.
#
#       image_width     Number of pixels wide this image is (both top & bottom
#                       should be the same!).
#
#       defining_pixel  The pixel that defines the block (see the comment
#                       detailing blocks in compare_edges_using_blocks() function).
#
#       block_size      The number of pixels along the edge of a block.
#
#       top_image       Boolean, when True this image is a top image and 
#                       the defining pixel is on the bottom.  If False this
#                       is the bottom image and the defining pixel is on its
#                       top row.
#
#       compare_type    This tells us what sort of color value we want averaged.
#                       See compare_edges_with_type() for a complete description.
#
#           NOTE: this is ignored for now (TODO: implement this fully).  Only
#               HUE is averaged.
#
#   returns
#       The average color of that region.  It'll be in the format of a
#       color tripple.
#       None if error.
#
def find_average_color_in_block(image_map, image_width, defining_pixel, block_size, top_image, compare_type):
    if debug:
        print(f'find_average_color_in_block( {image_map}, {image_width}, {defining_pixel}, {block_size}, {top_image}, {compare_type} )')

    color_sum = 0.0
    columns_used = 0    # the total number of columns that have 
                        # been examined in this block (not all will
                        # be used if we're on the right edge).

    # check to make sure even the first pixel is in range
    if defining_pixel[0] >= image_width:
        print(f'defining pixel out of range, aborting! image_width = {image_width}, defining_pixel = {defining_pixel}')
        return

    for i in range(block_size):
        if debug:
            print(f'i = {i}')

        pixel_x = defining_pixel[0] + i
        pixel_y = 0

        if pixel_x >= image_width:
            if debug:
                print(f'   trying to go too far right!  i = {i}, pixel_x = {pixel_x}, width = {image_width}, block_size = {block_size}')
            break       # We've reached the edge--discontinue

        columns_used += 1

        
        for j in range(block_size):
            if debug:
                print(f'   j = {j}')

            if top_image:
                pixel_y = defining_pixel[1] - j
            else:
                pixel_y = defining_pixel[1] + j

            if debug:
                print(f'      finding color at {pixel_x}, {pixel_y}')
            pixel_color = image_map[pixel_x, pixel_y]

            if debug:
                print(f'      pixel at {pixel_x}, {pixel_y} => {pixel_color}')

            color_sum += pixel_color[0]     # just the HUE for now
            if debug:
                print(f'      color_sum = {color_sum}')

    color_ave = color_sum / (columns_used * block_size)
    if debug:
        print(f'average color [ {color_sum} / ( {columns_used} / {block_size} ) ] -> {color_ave}')

    return color_ave


####################
#   Instead of comparing just pixels, this compares blocks.
#
#   param
#       block_size      The length of a square block in pixels.
#                       So a block_size of 3 will make a 3x3 square
#                       block.
#
def compare_edges_using_blocks(file1, file2, block_size, compare_type = HUE_MASK):
    if debug:
        print(f'compare_edges_using_blocks( {file1}, {file2}, {block_size} )')

    try:
        image1 = Image.open(file1)
        image2 = Image.open(file2)

    except:
        if debug:
            print('One or more files were not image files--aborting!')
        return

    # make sure that these have the same widths
    width = image1.width
    if (width != image2.width):
        if debug:
            print(f'compare_edges_using_blocks( {file1}, {file2}, {block_size} ) Error!  Not same width!')
        return

    # this is the number for the bottom row of the file1
    bottom = image1.height - 1

    map1 = image1.load()
    map2 = image2.load()

    # the running total of the distances
    distance_sum = 0.0

    # not sure this is needed for this function
    skipped_pixels = 0

    # just doing HUE for now (TODO: make this work for any aspect)
    #
    # Loop through all the pixels in the two maps, keeping track of the total
    # color difference between all the corresponding pixels.
    for x in range(width):
        # Get the two pixels -- don't forget to take the offset into account!
        # And we'll ignore out of range pixels.
        pixel1 = map1[x, bottom]
        pixel2 = map2[x, 0]   # here the offset is applied

        #
        # Find the average color of the box for this pixel. Time to define
        # a block:
        #       For the top image (image1), the block's lower left pixel is
        #       the one we just got.
        #
        #   0 0 0   
        #   0 0 0
        #   x 0 0   <- a 3x3 block defined by the pixel at x
        #
        #
        #       The bottom image uses the top left pixel as its defining
        #       point.    
        #
        #   x 0 0   <- defined by pixel at x
        #   0 0 0
        #   0 0 0
        #
        # When the pattern reaches the right side of the images where pixels
        # don't exist, those blocks will simply be skipped.
        #

        block_color1 = find_average_color_in_block(map1, image1.width, pixel1, block_size, True, compare_type)
        block_color2 = find_average_color_in_block(map2, image1.width, pixel2, block_size, False, compare_type)

        # check for errors -- probably bad data from here on out!!!
        if (block_color1 == None) or (block_color2 == None):
            print(f'error determining block color! skipping this loop')
            skipped_pixels += 1
            continue

        if type(block_color1) is tuple:
            # todo: handle full-on colors
            print('Whoops, not handling full on tuples for block colors yet!!!')
            break

            """
            # The distance between the two blocks is the square root of
            # the differences of the color planes.
            dist = 0.0

            if compare_type & HUE_MASK:
                dist += (block_color1[0] - block_color2[0]) ** 2

            if compare_type & SATURATION_MASK:
                dist += (block_color1[1] - block_color2[1]) ** 2

            if compare_type & LIGHT_MASK:
                dist += (block_color1[2] - block_color2[2]) ** 2

            # the actual distance between the two pixel colors
            dist = math.sqrt(dist)    
            """

        else:
            dist = abs(block_color1 - block_color2)

        # increase the distance
        distance_sum += dist

    # done with images
    image2.close()
    image1.close()

    distance_ave = distance_sum / (width - skipped_pixels)

    if debug:
        print(f'compare_edges_using_blocks() -> distance_sum = {distance_sum}, average = {distance_ave}')

    return distance_ave


####################
#   A more generic version of compare.  You specify the file that should
#   sit on top, the one beneath it, and the compare_type.
#
#   params
#       compare_type - a bit-wise thing.  But it MUST be either
#           HSL or RGB, not both.
#
#           bit 0 - hue             0x00000???
#           bit 1 - saturation
#           bit 2 - light
#
#           bit 4 - red             0x0???0000
#           bit 5 - green
#           bit 6 - blue
#
#       This means that this must be [0..7] for HSL or something
#       much bigger for RGB.
#
#       offset      Shift this many pixels instead of comparing the same pixels.
#                   This could be useful if the image is askew by a pixel or
#                   two.  Positive is shift left, negative is shift right.
#                   Defaults to 0 (no shift)
#
#   returns
#       0 = perfect match
#       otherwise the bigger the worse the match
#       None mean error (either not a graphics file or different widths)
#
def compare_edges_with_type(file1, file2, compare_type, offset = 0):
    if debug:
        print(f'compare_top_to_bottom( {file1}, {file2}, {compare_type}, {offset})')

    try:
        image1 = Image.open(file1)
        image2 = Image.open(file2)

    except:
        if debug:
            print('One or more files were not image files--aborting!')
        return
    
    # make sure that these have the same widths
    width = image1.width
    if (width != image2.width):
        if debug:
            print(f'compare_edges_with_type( {file1}, {file2} ) Error!  Not same width!')
        return

    # this is the number for the bottom row of the file1
    bottom = image1.height - 1

    map1 = image1.load()
    map2 = image2.load()

    # the running total of the distances
    distance_sum = 0.0
        
    # for keeping track of pixels that may be skipped because of offsets
    skipped_pixels = 0
    offset_x = 0

    # are we doing HSL or RGB
    if compare_type < 8:
        # HSL
        # Loop through all the pixels in the two maps, keeping track of the total
        # color difference between all the corresponding pixels.
        for x in range(width):
            # Get the two pixels -- don't forget to take the offset into account!
            # And we'll ignore out of range pixels.
            offset_x = x + offset
            if offset_x in range(0, width):
                pixel1 = map1[x, bottom]
                pixel2 = map2[offset_x, 0]   # here the offset is applied
            else:
                skipped_pixels += 1
                continue

            # The distance between the two pixels is the square root of
            # the differences of the color planes.
            dist = 0.0
            if compare_type & HUE_MASK:
                dist += (pixel1[0] - pixel2[0]) ** 2

            if compare_type & SATURATION_MASK:
                dist += (pixel1[1] - pixel2[1]) ** 2

            if compare_type & LIGHT_MASK:
                dist += (pixel1[2] - pixel2[2]) ** 2

            # the actual distance between the two pixel colors
            dist = math.sqrt(dist)    

            # increase the distance
            distance_sum += dist

    else:
        # RGB        
        # same technique as HSL
        for x in range(width):
            # get the two pixels
            offset_x = x + offset
            if offset_x in range(0, width):
                pixel1 = map1[x, bottom]
                pixel2 = map2[offset_x, 0]   # here the offset is applied
            else:
                skipped_pixels += 1
                continue

            # The distance between the two pixels is the square root of
            # the differences of the color planes.
            dist = 0.0
            if compare_type & RED_MASK:
                dist += (pixel1[0] - pixel2[0]) ** 2

            if compare_type & GREEN_MASK:
                dist += (pixel1[1] - pixel2[1]) ** 2

            if compare_type & BLUE_MASK:
                dist += (pixel1[2] - pixel2[2]) ** 2

            # the actual distance between the two pixel colors
            dist = math.sqrt(dist)    

            # increase the distance
            distance_sum += dist

    # done with images
    image2.close()
    image1.close()

    distance_ave = distance_sum / (width - skipped_pixels)

    # average out the difference
    if debug:
        print(f'   -> total distance = {distance_sum}')
        print(f'   -> width = {width}')
        print(f'   -> average = {distance_ave}')

    return distance_ave
    


####################
#
def compare_pixel_groups(file1, file2, group_size, comp_type):
    print('compare_pixel_groups TODO')

    
#######################################
# TESTING!!
#######################################

"""
no_connect_regular = compare_edges_using_blocks('Image-257.jpg', 'Image-258.jpg', HUE_MASK)
no_connect_size_2 = compare_edges_using_blocks('Image-257.jpg', 'Image-258.jpg', 2)
no_connect_size_3 = compare_edges_using_blocks('Image-257.jpg', 'Image-258.jpg', 3)
no_connect_size_4 = compare_edges_using_blocks('Image-257.jpg', 'Image-258.jpg', 4)

good_regular = compare_edges_with_type('Image-259.jpg', 'Image-260.jpg', HUE_MASK)
good_block_size_2 = compare_edges_using_blocks('Image-259.jpg', 'Image-260.jpg', 2)
good_block_size_3 = compare_edges_using_blocks('Image-259.jpg', 'Image-260.jpg', 3)
good_block_size_4 = compare_edges_using_blocks('Image-259.jpg', 'Image-260.jpg', 4)

bad_regular = compare_edges_with_type('Image-260.jpg', 'Image-261.jpg', HUE_MASK)
bad_block_size_2 = compare_edges_using_blocks('Image-260.jpg', 'Image-261.jpg', 2)
bad_block_size_3 = compare_edges_using_blocks('Image-260.jpg', 'Image-261.jpg', 3)
bad_block_size_4 = compare_edges_using_blocks('Image-260.jpg', 'Image-261.jpg', 4)

print('\nresults:')
print(f'regular:  no connect = {no_connect_regular}, good = {good_regular}, bad = {bad_regular}')
print(f'block size 2:  no connect = {no_connect_size_2}, good = {good_block_size_2}, bad = {bad_block_size_2}')
print(f'block size 3:  no connect = {no_connect_size_3}, good = {good_block_size_3}, bad = {bad_block_size_3}')
print(f'block size 4:  no connect = {no_connect_size_4}, good = {good_block_size_4}, bad = {bad_block_size_4}')
"""

# compare_edges_using_blocks('small1.png', 'small2.png', 2)

"""
image = Image.open("small2.png")
map = image.load()
ave = 0
#ave = find_average_color_in_block(map, 8, (0, 0), 2, False, HUE_MASK)
#ave += find_average_color_in_block(map, 8, (1, 0), 2, False, HUE_MASK)
ave += find_average_color_in_block(map, 8, (7, 0), 4, True, HUE_MASK)
#print(f'average of averages = {ave / 3}')
"""


"""
print(f'red -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", RED_MASK)}\n')
print(f'green -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", GREEN_MASK)}\n')
print(f'blue -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", BLUE_MASK)}\n')
print(f'red & green -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", RED_MASK | GREEN_MASK)}\n')
print(f'red & blue -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", RED_MASK | BLUE_MASK)}\n')
print(f'green & blue -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", GREEN_MASK | BLUE_MASK)}\n')
print(f'rgb -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", RED_MASK | GREEN_MASK | BLUE_MASK)}\n')

print(f'hue -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", HUE_MASK)}\n')
print(f'saturation -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", SATURATION_MASK)}\n')
print(f'light -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", LIGHT_MASK)}\n')
print(f'hue & saturation -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", HUE_MASK | SATURATION_MASK)}\n')
print(f'hue & light -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", HUE_MASK | LIGHT_MASK)}\n')
print(f'saturation & light -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", SATURATION_MASK | LIGHT_MASK)}\n')
print(f'hsl -> {compare_edges_with_type("Image-000.jpg", "Image-001.jpg", HUE_MASK | SATURATION_MASK | LIGHT_MASK)}\n')
"""



