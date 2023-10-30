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
#	This involves:
#		1.	Analyzing the images.  I'll create a database of the edges of
#			all the images.
#
#		2.	Finding fits.  Going through all the edges and finding all the
#			pieces that fit.
#
#		3.	Reassembly.  Going through the fits and creating bigger images.
#
#		4.	Start again, this time discarding the pieces that have been
#			combined, but adding the new images.
#
#		5.	Repeat until no more matches.
#
#
#	The Database
#
#		SQLite using the sqlite3 module (because it's built in!)
#
#		todo: test using this database
#

import sys      # for command line arguments
import os       # allows file access

import sqlite3  # todo

# from image_comparator import compare_edges_with_type, is_difference_within_tolerance
from image_comparator import *



##############################
#   constants
#
usage = 'todo scott, make a usage statement'


# Prefix for all the assembled files.  They'll have a number attached too.
FILE_PREFIX = 'assembled_'


##############################
#   globals
#
output_file_count = 0


##############################
#   script begin
#
print('start')

        

########
#   parse command line arguments
#
print(f'number of args is {len(sys.argv)}')

if len(sys.argv) == 2:
    path = sys.argv[1]
    os.chdir(path)
    print(f'changing directories to {path}')

if len(sys.argv) > 2:
    exit(usage)

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
    

# sort the list
file_list.sort()

# open the files and do something with 'em
print("here are the files one by one...")
for filename in file_list:
    print("\t" + filename)
##    f = open(filename, "rt")
##    print(f.read() + "\n")      # just print the contents, yawn
##    f.close()


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
    print(f'\ntop file is {file_list[i]}, i = {i}')

    match_list = [file_list[i]]     # start with the top file

    offset = 0
    j = i + 1
    while j < len(file_list):
        print(f'   starting inner loop. j = {j}, top = {file_list[i]}, bottom = {file_list[j]}')
        # dist = compare_bottom_to_top(file_list[i], file_list[j], False)
        dist = compare_edges_with_type(file_list[i], file_list[j], HUE_MASK, offset)
        print(f'      dist = {dist}')

        if dist == None:
            # exit this inner loop; we probably encountered a non-image file or images that don't match
            print(f'      Not image file or diff sizes. bottom file is {file_list[j]}, j = {j}.  Breaking..')
            break
        
        if is_difference_within_tolerance(dist):
           # This is a match!!!  Add it to our list.
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
                    print(f'      No match. bottom file is {file_list[j]}, j = {j}.  trying with offset +1')
                    offset = 1
                    continue

                case 1:
                    print(f'      No match again.  Trying with offset -1')
                    offset = -1
                    continue

                case -1:
                    print(f'      No match again.  Trying with offset +2')
                    offset = 2
                    continue

                case 2:
                    print(f'      No match again.  Trying with offset -2')
                    offset = -2
                    continue

                case _:
                    print(f'      No match after 5 tries!  Breaking..')
                    break   # no match, exit this inner loop

    #
    # if match_list is longer than 1, then we have some joining to do
    #
    match_list_len = len(match_list)
    if match_list_len > 1:
        print('   ...list detected, attempting to join files')
        join_files(match_list)

        # skip ahead
        i += 1      # todo: this is redundant with below

    else:
        print('   ...list not big enough, going back to outer loop')
        i += 1
               
        


# print(compare_bottom_to_top('Blue Climax No.54/Image-006.jpg', 'Blue Climax No.54/Image-001.jpg', False))



#######
# database setup  (TODO - maybe later)
#
"""
try:
    sqliteConnection = sqlite3.connect('mydb.db')
    cursor = sqliteConnection.cursor()

    # now try a query
    query = 'select sqlite_version();'
    cursor.execute(query)
    result = cursor.fetchall()
    print('SQLite Version is {}'.format(result))
    cursor.close()

except sqlite3.Error as error:
    print('error occurred: ', error)

finally:
    if sqliteConnection:
        sqliteConnection.close()
        print ('sqlite connection closed.')
"""


print ("\ndone.")
