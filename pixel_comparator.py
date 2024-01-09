#   Compares the difference between two pixels.
#   Does this in lots of different ways.
#
#   This is primarily an academic exercise.  Comparing pixels
#   individually is a real waste of time.
#

import os
import math
import sys      # for command line arguments
from PIL import Image
from PIL import ImageOps


USAGE = """
    Finds the difference between two pixels.
"""


#########
#   Gets the red part of an RGB pixel (which seems to be most
#   of the ones I see).
#
def get_red(pix):
    return pix[0]

def get_green(pix):
    return pix[1]

def get_blue(pix):
    return pix[2]

#########
#   Returns the luminescence difference between two pixels.
#   Assumes that luminescence is the first value (which is rarely
#   the case).
#
def get_luminescence_pixel_distance(pix1, pix2):
    return abs(pix1[0] - pix2[0])


#########
#   Returns the average color of a pixel.  This is the average
#   value of the first, second, and third color value (rgb or lsv).
def get_average_pixel_color(pix):
    sum_colors = pix[0] + pix[1] + pix[2]
    return float(sum_colors) / 3.0


#########
#   Finds the color distance bewteen two pixels.
#   Uses pythagorean method.
#
#   Note that this does not distinguish whether the pixels
#   are RGB, HSL, or XYZ.  It simply finds the distance
#   between the three axis and returns it.
#
def pythagorean_pixel_distance(pix1, pix2):
    return math.sqrt(
                     ((pix1[0] - pix2[0]) ** 2)
                     + ((pix1[1] - pix2[1]) ** 2)
                     + ((pix1[2] - pix2[2]) ** 2)
                    )


#########
#   Returns the distance between the averages of the two pixels.
#
def average_pixel_distance(pix1, pix2):
    return abs(get_average_color(pix1) - get_average_color(pix2))

#########
#   Gets the average color between two pixels.
#
def get_average_color_two_pixels(pix1, pix2):
    return (get_average_pixel_color(pix1) + get_average_pixel_color(pix2)) / 2.0


#########
#   Gets the average of any of the three components (probably red, green, 
#   blue).  Nice to be used as part of figuring out the average color of
#   a block.
#
#   input
#       x, y            The location of the pixel at the center of the block
#
#       component       Should be 0, 1, or 2.  This corresponds to Red, Green,
#                       or Blue (rgb).  If the images uses a different system
#                       the corresponding value should still be 0, 1, or 2.
#
#       radius          The number of pixels out from the given pixel to 
#                       define the block.  This number includes the given
#                       pixel itself, so a radius of 1 is just that one pixel,
#                       no real block at all.  A radius of 2 will be all the
#                       surrounding pixels.  And etc.
#       image_map       The image map that holds the block of pixels
#
#       width, height   Dimensions of the map
#
#   returns
#       The average component value of all the pixels in the block.
#
def get_block_component(x, y, component, radius, image_map, width, height):
#    print(f'get_block_component({x}, {y}, {component}, {radius}, ..., {width}, {height})')

    # Find looping areas that don't go out of bounds
    # Note that the end of the loops WILL BE OUT OF BOUNDS.
    # This is because the range function goes from the start to
    # just before the end.
    x_start = max(0, x - (radius - 1))  
    x_end = min(width, x + radius)      # there's no -1 here because the range stops BEFORE this number
    y_start = max(0, y - (radius - 1))
    y_end = min(height, y + radius)

#    print(f'x_start = {x_start}, x_end = {x_end}, y_start = {y_start}, y_end = {y_end}')

    block_sum = 0.0
    block_counter = 0

    # Go through the pixels in the block and add up the component values
    for i in range(x_start, x_end):
        for j in range(y_start, y_end):
            block_sum += image_map[i, j][component]
            block_counter += 1

    return block_sum / float(block_counter)

#########
#   Finds the average color of the pixels in a block.
#
#   todo:   make this more efficient (just one loop rather than 
#           calling get_block_component() 3 times).
#
#   input
#       x, y            The location of the pixel at the center of the block
#
#       radius          The number of pixels out from the given pixel to 
#                       define the block.  This number includes the given
#                       pixel itself, so a radius of 1 is just that one pixel,
#                       no real block at all.  A radius of 2 will be all the
#                       surrounding pixels.  And etc.
#       image_map       The image map that holds the block of pixels
#
#       width, height   Dimensions of the map
#
#   returns
#       An rgb tuple with the average color of the block.
#
def get_block_color(x, y, radius, image_map, width, height):
#    print(f'get_block_color({x}, {y}, {radius}, ..., {width}, {height})')
    red = get_block_component(x, y, 0, radius, image_map, width, height)
    green = get_block_component(x, y, 1, radius, image_map, width, height)
    blue = get_block_component(x, y, 2, radius, image_map, width, height)
    return red, green, blue
            
            
            


#########
#   Rather than comparing just a pixel, this compares the pixels and all the
#   surrounding pixels too.  An average value is placed on this block, which
#   will then be compared to an average value on the corresponding block.
#
#   input
#       image_map1, x1, y1      The location of the first pixel and its image map
#       width1, height1         and dimensions.
#
#       image_map2, x2, y2      The location of the second pixel and its image map
#       width2, height2         and dimensions.
#
#       radius      The number of pixels out from the given pixel to 
#                   define the block.  This number includes the given
#                   pixel itself, so a radius of 1 is just that one pixel,
#                   no real block at all.  A radius of 2 will be all the
#                   surrounding pixels.  And etc.
#
#       block_first     There are two ways to do block comparisons: 
#                           1. Find the average of a block and then 
#                              compare those blocks.
#                           2. Average all the distances of the pixels
#                              within a given block.
#                       This tells which technique to use.  block_first (#1)
#                       is the default.
#               todo: determine if these are indeed different mathematically.
#
#       threshold   If you want to say that certain small distances don't
#                   matter (useful for noisy stuff), specify this.  Any
#                   distance below this threshold will be considered 0.
#
#       use_pythagorus, use_luminescence    Only one can be true. Pythagorus is default.
#
#   returns
#       The distance between the block averages.  
#       0 for a perfect match.
#       -1 on error.
#
def block_average_distance(image_map1, x1, y1, width1, height1,
                           image_map2, x2, y2, width2, height2,
                           radius,
                           block_first = True,
                           threshold = 0.0,
                           use_pythagorus = True, use_luminescence = False):

    if use_pythagorus and use_luminescence:
        print('Error! I cannot do both pythagorean AND luminescence distance in block_average_distance()!')
        return -1

    if (not use_pythagorus) and (not use_luminescence):
        print('Error! You have to choose a comparison type (either pythagorean or luminescence).')
        return -1

    # the averages for each block
    block_average1 = 0.0
    block_average2 = 0.0

    dist = 0.0

    # Find looping areas that don't go out of bounds
    # Note that the end of the loops WILL BE OUT OF BOUNDS.
    # This is because the range function goes from the start to
    # just before the end.
    x1_start = max(0, x1 - (radius - 1))
    x1_end = min(width1, x1 + (radius - 1))
    y1_start = max(0, y1 - (radius - 1))
    y1_end = min(height1, y1 + (radius - 1))

    x2_start = max(0, x2 - (radius - 1))
    x2_end = min(width2, x2 + (radius - 1))
    y2_start = max(0, y2 - (radius - 1))
    y2_end = min(height2, y2 + (radius - 1))


    if block_first:
        sum = 0.0
        block_counter = 0

        # Find the average of the block for the first image.
        for i in range(x1_start, x1_end):
            for j in range(y1_start, y2_end):
                if (x1 == i) and (y1 == j):
                    continue        # don't bother checking against the original

                if use_pythagorus:
                    sum += pythagorean_pixel_distance(image_map1[x1, y1], image_map1[i, j])
                elif use_luminescence:
                    sum += get_luminescence_pixel_distance(image_map1[x1, y1], image_map1[i, j])
                else:
                    # This should never happen, but it makes the code more readable.
                    print('Error: No distance technique available!')
                    return -1

                block_counter += 1


        block_average1 = sum / float(block_counter)

    else:
        exit("todo: implement alternative to block_first in block_average_distance()!")


    if use_pythagorus:
        exit('todo - use_pythagorus')
    if use_luminescence:
        exit('todo - use_luminescence')


def compare_pixels(image_map1, x1, y1,
                   image_map2, x2, y2,
                   use_pythagorus = True,
                   use_luminescence = True):
    exit('todo: compare using the various methods here, combining and averaging if necessary.')


########################################
#   begin
########################################

# open the image and image map supplied as the first argument
test_image = Image.open(sys.argv[1])
test_image_map = test_image.load()

print(f'block color 41, 40 r=1:  {get_block_color(41, 40, 1, test_image_map, test_image.width, test_image.height)}')
