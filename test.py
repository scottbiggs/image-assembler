# tests Image.paste() function

import sys
from PIL import Image

#########
#	Crops from the center of the given image.
#
#	input
#		pil_img						The image to crop
#
#		crop_width, crop_height 	The new width and height of the image
#
#	returns
#		A new cropped image of pil_img.
#
def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


print(f'pasting a piece of {sys.argv[2]} into {sys.argv[1]} => {sys.argv[3]}')

image1 = Image.open(sys.argv[1])
image2 = Image.open(sys.argv[2])

out_image = image1.copy()	# make a copy of first image

# make a cropped version of the 2nd image
cropped_image = image2.crop((20, 20, 60, 60))

out_image.paste(cropped_image, (20, 20))	# paste the cropped part, offset appropriately
out_image.save(sys.argv[3])

out_image.close()
image1.close()
image2.close()

###########
# testing crop_center  -- args:  image_to_crop, width, height, out_file
#
# image = Image.open(sys.argv[1])

# new_image = crop_center(image, int(sys.argv[2]), int(sys.argv[3]))
# new_image.save(sys.argv[4])

# new_image.close()
# image.close()

print('done.')






