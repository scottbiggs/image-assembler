#	This is a program that tries to piece together a bunch of jpg images
#	into cohesive images.
#
#	The problem:  I have lots of images stuck in pdf files.  But these images
#	have been broken up into many pieces.  When I extract the jpgs what I have
#	are hundreds of pieces instead of the nice photos that I want.
#
#	I'm hoping to use this as a program to reassemble these images into
#	a useful format.
#
#   There are a few one good things: the images are in order, the images all fit
#   from top to bottom, and matching images are the same width.
#
#   I've found that my technique works about 90% of the time.  But it fails
#   sometimes with text.  I've tried two alternate systems to make it recognize
#   text (offsets and blocks), but they don't seem to work very well.
#
#   What I did is make a second program, joiner.py.  It allows you to manually
#   join images that *should* have been joined automatically, but were mis-
#   interpreted to be different images.
#

import sys      # for command line arguments
import os       # allows file access

from image_comparator import *



##############################
#   constants
#
usage = """

    merge_images  -- a program to try to fix munged images from bad PDF files.

USAGE:
    merge_images [path]

Defaulting the current directory, this will go through all the image files and
try to match 'em up and join them back together.

The output files will be named 'assembled_###'.jpg and will be placed in the
same directory.  

NOTE:  Anything file the same name will be overwritten!!!

"""


# Prefix for all the assembled files.  They'll have a number attached too.
FILE_PREFIX = 'assembled_'

# to turn on verbose messages
DEBUG = False


##############################
#   globals
#
output_file_count = 0

# number of new joined files that have been created
num_joined_files = 0

# List of all the files that for whatever reason were never joined
# with any other file.  These could be indicators of a match that
# didn't work but should have.
unjoined_file_list = list()

##############################
#   script begin
#
print('start')

        

########
#   parse command line arguments
#
if DEBUG:
    print(f'number of args is {len(sys.argv)}')

if len(sys.argv) == 2:
    path = sys.argv[1]
    os.chdir(path)
    if DEBUG:
        print(f'changing directories to {path}')

if len(sys.argv) > 2:
    exit(usage)

if DEBUG:
    print('path defaulting to current directory')
          
########
# A list of all the files in the current directory
# in an array (or list?) of strings.
temp_file_list = os.listdir()
file_list = []

# Strip out the directories
for f in temp_file_list:
    if os.path.isfile(f):
        file_list.append(f)
    
# sort the list (I assume that the images are in alphabetical order)
file_list.sort()


#########
#   Joins the files in the given list.  The list must be ordered top
#   to bottom.
#
#   side effects
#       A new file will be created with the name {FILE_PREFIX}{output_file_count}.jpg
#
def join_files(file_list):
    global output_file_count

    length = len(file_list)
    print(f'      joining {length} files from {file_list[0]} to {file_list[length - 1]}')
    print(f'         and the name will be {FILE_PREFIX}{output_file_count}.jpg')
    
    images = []
    for filename in file_list:
        # open the named image
        images.append(Image.open(filename))

    # find the width and height of the new joined image
    width = images[0].width
    height = 0
    for image in images:
        height += image.height

    # let's make a new image and add in the contents of the other images
    new_image = Image.new('RGB', (width, height))

    current_y_to_paste = 0
    for i in range(len(file_list)):
        new_image.paste(images[i], (0, current_y_to_paste, images[i].width, current_y_to_paste + images[i].height))
        current_y_to_paste += images[i].height

    # and save the result
    new_image.save(f'{FILE_PREFIX}{output_file_count}.jpg')
    output_file_count += 1

    # don't forget to close these images
    new_image.close()
    for image in images:
        image.close()



#########
#
#   Method:
#
# Go through each file.  Does it connect with the next
# one?  If so, list 'em.  Does the next file connect with
# the 2nd one?  If so, add it to the list.  Continue adding
# to the list until there isn't a match any more.
#
# At this point, join all the pieces and make a new file.
#
# Then continue on, starting with the last file that didn't match.
i = 0
while i < len(file_list): 
    curr_top_file = file_list[i]
    if DEBUG:
        print(f'\ntop file is {file_list[i]}, i = {i}')

    match_list = [file_list[i]]     # start with the top file

    offset = 0
    j = i + 1
    while j < len(file_list):
        if DEBUG:
            print(f'   starting inner loop. j = {j}, top = {file_list[i]}, bottom = {file_list[j]}')

        # dist = compare_bottom_to_top(file_list[i], file_list[j], False)
        dist = compare_edges_with_type(file_list[i], file_list[j], HUE_MASK, offset)
        if DEBUG:
            print(f'      dist = {dist}')

        if dist == None:
            # exit this inner loop; we probably encountered a non-image file or images that don't match
            if DEBUG:
                print(f'      Not image file or diff sizes. bottom file is {file_list[j]}, j = {j}.  Breaking..')
            break
        
        if is_difference_within_tolerance(dist):
            # This is a match!!!  Add it to our list.
            if DEBUG:
                print(f'      Match! adding bottom file ({file_list[j]}) to list, j = {j}')

            match_list.append(file_list[j])
            i = j    # this increments the top image to be the current bottom image
            j += 1
            offset = 0

        else:
            # Didn't match.  Try again with an offset.  Of course we may be in the middle of
            # trying again, so figure out where we are and act accordingly.
            match offset:
                case 0:
                    if DEBUG:
                        print(f'      No match. bottom file is {file_list[j]}, j = {j}.  trying with offset +1')
                    offset = 1
                    continue

                case 1:
                    if DEBUG:
                        print(f'      No match again.  Trying with offset -1')
                    offset = -1
                    continue

                case -1:
                    if DEBUG:
                        print(f'      No match again.  Trying with offset +2')
                    offset = 2
                    continue

                case 2:
                    if DEBUG:
                        print(f'      No match again.  Trying with offset -2')
                    offset = -2
                    continue

                case _:
                    if DEBUG:
                        print(f'      No match after 5 tries!  Breaking..')
                    break   # no match, exit this inner loop

    #
    # if match_list is longer than 1, then we have some joining to do
    #
    match_list_len = len(match_list)
    if match_list_len > 1:
        if DEBUG:
            print('   ...list detected, attempting to join files')
        join_files(match_list)
        num_joined_files += 1

        # skip ahead
        i += 1      # todo: this is redundant with below

    else:
        if DEBUG:
            print('   ...list not big enough, going back to outer loop')
        unjoined_file_list.append(match_list[0])
        i += 1
               
        

##########
#   wrapping up
#
print(f'Success!  Joined {num_joined_files} files.')
if len(unjoined_file_list) > 0:
    print('Here are the files that were never joined:')
    for name in unjoined_file_list:
        print(f'   {name}')

print ("done.")
