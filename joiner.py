#   Simply joins two image files.  The first is on top of the second.
#

import sys      # for command line arguments
from PIL import Image


############################
#   constants
#

usage = """
Joiner - a program to stitch together two images.

Usage:
    joiner <top_file_name> <bottom_file_name> <output_file_name>

The first file will be on top, and the second file will be put below.
The top and bottom file MUST be the same width!

"""


############################
#   functions
#

#########
#   Joins two files into one.  The output will have the top file immediately
#   above the bottom file.  If the files are different widths, then this
#   does nothing.
#
#   params
#       top_file            filename for the file on top
#       bottom_file         filename for the bottom file
#       out_file            filename for the new output file.
#
#   side effects
#       A new file will be created with the given output file name.  If it already
#       exists, then it will be overwritten.
#
#   returns
#       True    - file created successfully
#       False   - problem (probably the two input files are different widths)
#
def join_files(top_file, bottom_file, out_file):

    try:
        top_image = Image.open(top_file)
        bottom_image = Image.open(bottom_file)

    except:
        print('One or more files were not image files--aborting!')
        return False

    # check for correct width
    if top_image.width != bottom_image.width:
        print('Images do not have the same width--aborting!')
        return False

    # new image combines heights
    out_image = Image.new('RGB', (top_image.width, top_image.height + bottom_image.height))

    # paste the pieces
    out_image.paste(top_image, (0, 0, top_image.width, top_image.height))
    out_image.paste(bottom_image, (0, top_image.height, bottom_image.width, top_image.height + bottom_image.height))

    # and save result
    out_image.save(out_file)

    # clean up
    out_image.close()
    bottom_image.close()
    top_image.close()
    return True


#########################################################
#   begin
#########################################################

if len(sys.argv) != 4:
    exit(usage)

top = sys.argv[1]
bottom = sys.argv[2]
new = sys.argv[3]

print(f'joining {top} to {bottom} => {new}')
result = join_files(top, bottom, new)

if result:
    print(f'successfully joined {sys.argv[1]} to {sys.argv[2]} => {sys.argv[3]}')
else:
    print(f'Error trying to join {sys.argv[1]} to {sys.argv[2]}!')
