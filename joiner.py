#   Simply joins two image files.  The first is on top of the second.
#

import sys      # for command line arguments
from PIL import Image


############################
#   constants
#

USAGE = """
Joiner - a program to stitch together two images.

Usage:
    joiner <top_file_name> <bottom_file_name> <output_file_name> [-f]

The first file will be on top, and the second file will be put below.
The top and bottom file should be the same width (except for below).

-f      Force the files to join, even if their widths don't match.
        The final widith will be the same as the widest file, and the
        thinner file will be centered.

"""

# indicates that we should FORCE the two files to fit, even if their
# widths are different.
FORCE_PARAM = "-f"


############################
#   globals
#

# when True, force the files to join, even if the widths don't match.
force_fit = False


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
def join_files(top_file, bottom_file, out_file, force = False):

    try:
        top_image = Image.open(top_file)
        bottom_image = Image.open(bottom_file)

    except:
        print('One or more files were not image files--aborting!')
        return False

    new_width = top_image.width
    top_width_adjustment = 0        # offset to center image
    bottom_width_adjustment = 0

    # check for correct width
    if top_image.width != bottom_image.width:
        if force == False:
            print('Images do not have the same width--aborting!')
            return False

        # It's time to FORCE the issue!  hehe
        # Make sure our new width is the max width.  And set the offset
        # needed to center the less wide portion.
        if top_image.width > bottom_image.width:
            new_width = top_image.width     # yeah redundant, but makes code easier to follow
            bottom_width_adjustment = int((top_image.width - bottom_image.width) / 2)
        else:
            new_width = bottom_image.width
            top_width_adjustment = int((bottom_image.width - top_image.width) / 2)

    # new image combines heights
    out_image = Image.new('RGB', (new_width, top_image.height + bottom_image.height))

    # paste the pieces (centering, which will do nothing if the width already matches
    # the image width)

    out_image.paste(top_image, (top_width_adjustment, 0))
    out_image.paste(bottom_image, (bottom_width_adjustment, top_image.height))
    
    # out_image.paste(top_image, (top_width_adjustment, 0, 
    #                             top_image.width, top_image.height))
    # out_image.paste(bottom_image, (bottom_width_adjustment, top_image.height, 
    #                                bottom_image.width, top_image.height + bottom_image.height))

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

# Note that sys.argv[0] is always 'joiner.py' and its path, so that
# counts as the first argument.  Thus there should be 4 or 5 params.
# If there are 5 params, one must be '-f'.

# take care of the easy cases first
if len(sys.argv) < 4 or len(sys.argv) > 5:
    exit(USAGE)

if len(sys.argv) == 4:
    top = sys.argv[1]
    bottom = sys.argv[2]
    new = sys.argv[3]

# the only case left is a length of 5.  One of the params MUST be '-f'.
if len(sys.argv) == 5:
    force_fit = True
    if sys.argv[1].lower() == FORCE_PARAM:      # -f is first param (position 1)
        top = sys.argv[2]
        bottom = sys.argv[3]
        new = sys.argv[4]
    elif sys.argv[2].lower() == FORCE_PARAM:    # -f second param
        top = sys.argv[1]
        bottom = sys.argv[3]
        new = sys.argv[4]
    elif sys.argv[3].lower() == FORCE_PARAM:    # -f 3rd param
        top = sys.argv[1]
        bottom = sys.argv[2]
        new = sys.argv[4]
    elif sys.argv[4].lower() == FORCE_PARAM:    # -f is last param
        top = sys.argv[1]
        bottom = sys.argv[2]
        new = sys.argv[3]
    else:
        # couldn't find the '-f' param! aborting!
        exit(USAGE)


print(f'joining {top} to {bottom} => {new}')
result = join_files(top, bottom, new, force_fit)

if result:
    print(f'successfully joined {sys.argv[1]} to {sys.argv[2]} => {sys.argv[3]}')
