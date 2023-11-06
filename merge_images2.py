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


import sys      # for command line arguments
import os       # allows file access

from image_comparator import *



##############################
#   constants
#
usage = """

    merge_images2  -- a second program to try to fix munged images from bad PDF files.

USAGE:
    merge_images2 num

Where 'num' is an integer that tells how many pieces each original image has been
broken into.

This will work ONLY in the current directory.  Maybe later I'll deal with
directories, but that seems unnecessary now.  But at least I'm smart enough
to only deal with image files; all other file types will be ignored.

The output files will be named 'assembled_###'.jpg and will be placed in the
same directory.  

NOTE:  Anything file the same name will be overwritten!!!

"""


# Prefix for all the assembled files.  They'll have a number attached too.
FILE_PREFIX = 'assembled_'

# to turn on verbose messages
DEBUG = True


##############################
#   globals
#
output_file_count = 0

# number of new joined files that have been created
num_joined_files = 0

# the number of pieces each original image has been broken into
num_pieces = 0


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

    # find the width and height of the new joined image (width is the max)
    width = 0
    height = 0
    for image in images:
        if image.width > width:
            width = image.width
        height += image.height


    # let's make a new image and add in the contents of the other images
    new_image = Image.new('RGB', (width, height))

    current_y_to_paste = 0
    for i in range(len(file_list)):
        width_adjustment = int((width - images[i].width) / 2)   # center
        new_image.paste(images[i], (width_adjustment, current_y_to_paste))
        current_y_to_paste += images[i].height

    # and save the result
    new_image.save(f'{FILE_PREFIX}{output_file_count}.jpg')
    output_file_count += 1

    # don't forget to close these images
    new_image.close()
    for image in images:
        image.close()


##############################
#   script begin
##############################

print('start')


########
#   parse command line arguments
#

if len(sys.argv) != 2:
    exit(usage)

num_pieces = int(sys.argv[1])

          
########
# A list of all the files in the current directory
# in an array (or list?) of strings.
temp_file_list = os.listdir()
file_list = []

# if DEBUG:
#     print(f'file_list initially contains:')
#     for filename in temp_file_list:
#         print(f'   {filename}')

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

# if DEBUG:
#     print(f'after stripping out directories and sorting, we have:')
#     for filename in file_list:
#         print(f'   {filename}')


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


# My first try was too complicated.  Just go through the file_list once.
# Just slice it up into num_pieces groups, sending those groups to
# join_files().

i = 0
while i < len(file_list):
    end_index = len(file_list)
    if i + num_pieces < end_index:
        end_index = i + num_pieces
    if DEBUG:
        print(f'   end_index = {end_index}')

    group_list = file_list[i : end_index]
    join_files(group_list)
    i += num_pieces


##########
#   wrapping up
#
print(f'Success!  Joined {num_joined_files} files.')
print ("done.")
