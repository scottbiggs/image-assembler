# tutorial for using Pillow (PIL updated to python 3)
# from https://www.youtube.com/watch?v=5QR-dG68eNE
#

from PIL import Image
from colormath.color_objects import LabColor, HSLColor
from colormath.color_conversions import convert_color

############
#basic technique:
#
image = Image.open('image_tutorial/strawberry.jpg')

# show the picture using the default viewer
# image.show()

############
# alternative way to open an image and display it
# (a more pythony technique with better scoping)
#

# with Image.open('image_tutorial/strawberry.jpg') as image:
#     image.show()


############
# create a brand new image
#
# with Image.new('RGBA', (400, 300)) as image:  # (color scheme, width & height)
#    image.show()           # display image
#    image.save('test.png')  # saving is super easy (extension is essential)!


# for fun, find the color value of the top right pixel
pixelMap = image.load()
myFavePixel = pixelMap[image.width - 1, 0]
print('top right pixel = ', myFavePixel)
labcolor = LabColor(myFavePixel[0], myFavePixel[1], myFavePixel[2])
#print('  but in hsl space it is ', convert_color(labcolor, HSLColor))

hslcolor = convert_color(labcolor, HSLColor)
print('  hsl -->', hslcolor)
print('  just hue -->', hslcolor.hsl_h)









