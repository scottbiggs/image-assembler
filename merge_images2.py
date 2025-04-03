#   Similar to image_assember, this tries to join an entire directory
#   of images.
#
#   But this is much simpler.  It takes as an argument a number.
#   And it assumes that the big images are consecutively broken up
#   into this many pieces.  It then assembles these pieces into
#   the big pieces again.
#
#   Not really sure what to do on an error.  Hmmm.
#

import re
import sys      # for command line arguments
import os       # allows file access

import math
from PIL import Image
from PIL import ImageOps

# from image_comparator import *



##############################
#   constants
#
USAGE = """
    merge  -- a program to try to fix munged images from bad PDF files.

USAGE:
    merge [-h] num

Where 'num' is an integer that tells how many pieces each original image has been
broken into.

    -h      indicates that the files should be stitched together horizontally
            instead of vertically

    -a      try to add one more piece to the stitching, but only if the next piece
            is less than half the height of the last normal piece.  Could be useful
            in some cases.

This will work ONLY in the current directory.  Maybe later I'll deal with
directories, but that seems unnecessary now.  But at least I'm smart enough
to only deal with image files; all other file types will be ignored.

The output files will be named 'assembled_[original_name_of_first_file]'.jpg and 
will be placed in the same directory.  

"""


# Prefix for all the assembled files.  They'll have a number attached too.
FILE_PREFIX = 'assembled_'

# to turn on verbose messages
DEBUG = False

# command param to indicate horizontal stitching
HORIZ_PARAM = '-h'

# param to indicate that we will try to figure out if another piece should be added
ADD_PIECE_PARAM = '-a'

##############################
#   globals
#
output_file_count = 0

# number of new joined files that have been created
num_joined_files = 0

# the number of pieces each original image has been broken into
num_pieces = 0

# When True, use order numbers in the assembled name from the last
# digits of the first item in the group.
#
# todo: remove this--it's no longer used (will always be true)
original_ordering = True

# When True, the pieces should be stitched together horizontally.
horizontal = False

# When True, we should try to add one more piece when stitching (if it meets our criteria)
add_piece = False

#########
#
#   Parses command line params.  Will exit program if params don't
#   make sense.
#
#   side effects:
#       horizontal      Set to True iff the HORIZ_PARAM exists
#
#       add_piece       Set to True iff ADD_PIECE_PARAM exists
#
#       num_pieces      Set to the number of pieces per image
#
def parse_params():
    global horizontal
    global add_piece
    global num_pieces

    # loop through all the params
    counter = 1
    while counter < len(sys.argv):
        this_param = sys.argv[counter]

        if DEBUG:
            print(f'counter = {counter}.  this_param = {this_param} (lowercase = {this_param.lower()})')

        if this_param.lower() == HORIZ_PARAM:
            horizontal = True
            if DEBUG:
                print('   horizonatal is set to True')

        if this_param.lower() == ADD_PIECE_PARAM:
            add_piece = True
            if DEBUG:
                print('   add_piece is set to True')

        else:
            # Must be a number.  But have we already set the number? that ain't right.
            if num_pieces != 0:
                print(f'extra parameter: {this_param}, aborting')
                exit(USAGE)

            try:
                # set num_pieces to number specified in param
                num_pieces = int(this_param)
            except:
                print(f'unable to parse {this_param} into an integer!')
                exit(USAGE)

        counter += 1


    if num_pieces <= 0:
        print(f'no (or illegal) count found!')
        exit(USAGE)


#########
#   Grabs the numerical suffix (not extension) of a filename.
#   If there is no numerical suffix, then an empty string is
#   returned.
#
#   input
#       filename        Filename with or without extension.  It may or
#                       may not end with digits.
#
def get_numerical_suffix(filename):
    if DEBUG:
        print(f'Attempting to grab numerical suffix from {filename}')

    # this regex should return any numerical stuff sitting just before a period
    return_val = re.search(r'\d+[.]{0}', filename)

    if return_val == None:
        return ''

    return return_val.group()



#########
#   Saves the given image.
#
#   input
#       img             The Image file to be saved.
#
#       name            The name to save this as (see unique_name below).
#
#       unique_name     When True (default), this will make sure that
#                       the saved file uses a unique name.
#                       False means to overwrite any file with the
#                       same name.
#
def save_image(img, name, unique_name = True):
    if unique_name:
        prefix, extension = os.path.splitext(name)
        if DEBUG:
            print(f'save_image(), prefix = {prefix}, extension = {extension}')

        current_name = f'{prefix}{extension}'
        unique_suffix = 0       # int

        # check to see if the name is used
        while os.path.exists(current_name):
            unique_suffix += 1
            current_name = f'{prefix}_{unique_suffix}{extension}'

            # give up after maxint tries.
            if unique_suffix == sys.maxsize:
                exit('Unable to find a unique name for our file. Aborting!!!')

        img.save(current_name)

    else:
       img.save(name)


#########
#   Joins the files in the given list.  The list must be ordered top
#   to bottom.
#
#   input
#       file_list       List of the files to join
#
#       optional_file   An extra file that we may add IF conditions are right.
#                       Defaults to None (no optional file possible)
#
#   returns
#       The number of files that were joined to make our final file.  This will be
#       either the length of file_list, or that number + 1 if we added the optional
#       file.
#
#   side effects
#       A new file will be created with the name {FILE_PREFIX}{output_file_count}.jpg
#
def join_files(file_list, optional_file = None):
    global output_file_count
    global add_piece

    length = len(file_list)
    if DEBUG:
        print(f'join_files(): joining {length} files from {file_list[0]} to {file_list[length - 1]}')
        print(f'join_files():    (plus possibly {optional_file})')

    original_ordering_count = get_numerical_suffix(file_list[0])

    if original_ordering:
        print(f'join_files():    and the name will be {FILE_PREFIX}{original_ordering_count}.jpg')
    else:
        print(f'join_files():    and the name will be {FILE_PREFIX}{output_file_count}.jpg')
    
    images = []
    for filename in file_list:
        # open the named image
        images.append(Image.open(filename))

    # Are we going to add an optional piece?  Check to see now.

    using_optional = False
    if optional_file != None:
        if DEBUG:
            print(f'optional_file is {optional_file}')

        # compare the heights / widths to see if the optional piece
        # meets our criteria (ie, it's less than half the size of the last piece)
        extra_image = Image.open(optional_file)
        if horizontal:
            # check horizontal
            if extra_image.width * 2 < images[len(images) - 1].width:   # it's less than half width
                using_optional = True

        else:
            #check vertical
            if extra_image.height * 2 < images[len(images) - 1].height:
                using_optional = True

    # find the width and height of the new joined image
    width = 0
    height = 0
    for image in images:
        if horizontal:
            # height is max height; width is sum of all widths
            if image.height > height:
                height = image.height
            width += image.width

        else:
            # width is max width; height is sum of heights
            if image.width > width:
                width = image.width
            height += image.height

    if using_optional:
        if horizontal:
            print('adding optional_file extra size to width')
            width += extra_image.width
        else:
            print('adding optional_file extra size to height')
            height += extra_image.height


    # let's make a new image and add in the contents of the other images
    new_image = Image.new('RGB', (width, height))

    # marker for where to paste the next image
    current_place_to_paste = 0

    for i in range(len(file_list)):
        if horizontal:
            if DEBUG:
                print(f'i = {i}, current_place_to_paste = {current_place_to_paste}')
            height_adjustment = int((height - images[i].height) / 2)    # center
            new_image.paste(images[i], (current_place_to_paste, height_adjustment))
            current_place_to_paste += images[i].width

        else:
            width_adjustment = int((width - images[i].width) / 2)   # center
            new_image.paste(images[i], (width_adjustment, current_place_to_paste))
            current_place_to_paste += images[i].height

    if using_optional:
        if horizontal:
            height_adjustment = int((height - extra_image.height) / 2)    # center
            new_image.paste(extra_image, (current_place_to_paste, height_adjustment))
        else:
            new_image.paste(extra_image, (width_adjustment, current_place_to_paste))


    # and save the result
    if original_ordering:
        save_image(new_image, f'{FILE_PREFIX}{original_ordering_count}.jpg')
    else:
        save_image(new_image, f'{FILE_PREFIX}{output_file_count}.jpg')

    output_file_count += 1

    # don't forget to close these images
    new_image.close()
    for image in images:
        image.close()
    if using_optional:
        extra_image.close()

    # return number of images merged
    if using_optional:
        if DEBUG:
            print(f'returning {length + 1}')
        return length + 1
    else:
        if DEBUG:
            print(f'returning {length}')
        return length

#########
#   The main loop: goes through all the pieces, assembling them
#   into their constituent files.
#
#   Some terminology
#
#       piece       The file (or image) that is just a piece of a bigger image.
#                   The main point of this program is assemble pieces into a full image.
#
#       piece_list  A list of all the totaly pieces that comprise all the images.
#
#       group_size  The number of pieces that the user has specified to assemble int
#                   an image.

#       group       The pieces that comprise an image.  It is exactly group_size in length
#                   and therefore does not include the "extra" piece.
#
#       group_start Index into the piece_list where the group starts.
#
#       group_end   Index into the piece_list of the last item of a group.
#
#       image       A completely assembled image.  It consists of pieces.
#
#       extra       An optional piece that may or may not be part of an image.  If it
#                   is less than half the size of the last piece in a group, it will
#                   be considered part of the image.
#
#
#   preconditions
#       parameters have been properly parsed
#
#
def build_all_pieces(pieces_per_image, piece_list, check_for_extra):
    # number of files that we have completely processed
    num_completed = 0

    # for the next group of pieces to assemble, this is the index of the first one
    group_start = 0

    # this is the LAST piece to process in the current image
    group_end = group_start + pieces_per_image - 1

    # check to make sure this is not out of bounds
    if group_end > len(piece_list) - 1:
        group_end = len(piece_list) - 1

    # index to where the extra piece should be
    extra_index = group_end + 1

    if DEBUG:
        print('build_all_pieces() start:')
        print(f'   pieces_per_image = {pieces_per_image}, piece_list length = {len(piece_list)}')
        print(f'   group_start = {group_start}, group_end = {group_end}, extra_index = {extra_index}')
        print(f'   num_completed = {num_completed}')

    # repeat as long as the start is within our range
    while group_start < len(piece_list):
        if DEBUG:
            print('   - build_all_pieces() main:')
            print(f'      group_start = {group_start}, group_end = {group_end}, extra_index = {extra_index}')
            print(f'      num_completed = {num_completed}')

        # create list of files to join by slicing piece_list
        files_to_join = piece_list[group_start : group_end + 1]

        num_pieces_joined = 0

        # add the extra index if check_for_extra is true AND extra_index is in bounds
        if check_for_extra and (extra_index < len(piece_list)):
            num_pieces_joined = join_files(files_to_join, piece_list[extra_index])

        else:
            # just a regular join
            num_pieces_joined = join_files(files_to_join)

        if DEBUG:
            print(f'      -> joined {num_pieces_joined} files')
        num_completed += 1

        # get ready for next loop
        group_start += num_pieces_joined
        group_end = group_start + pieces_per_image - 1

        # check to make sure this is not out of bounds
        if group_end > len(piece_list) - 1:
            group_end = len(piece_list) - 1

        extra_index = group_end + 1

    return num_completed


##############################
#   script begin (main)
##############################

print('merge is starting...')

parse_params()

########
# A list of all the files in the current directory
# in an array (or list?) of strings.
temp_file_list = os.listdir()
file_list = []


# Strip out the directories and non-image files
# if DEBUG:
#     print(f'stripping out directories and non-image files:')
for f in temp_file_list:
    if os.path.isfile(f):
        try:
            image = Image.open(f)

            # success! close it and add the filename to our list
            image.close()
            file_list.append(f)

        except:
            if DEBUG:
                print(f'   discarding {f}')

    
# sort the list (I assume that the images are in alphabetical order)
file_list.sort()


# this is the big call
num_joined_files = build_all_pieces(num_pieces, file_list, add_piece)

##########
#   wrapping up
#
print(f'Success!  Joined {num_joined_files} files.')


