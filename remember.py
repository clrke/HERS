import Image, ImageChops, ImageOps
import sys

image = Image.open(sys.argv[1])
data = sys.argv[2]

def trim(im):
	bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
	diff = ImageChops.difference(im, bg)
	diff = ImageChops.add(diff, diff, 2.0, -100)
	bbox = diff.getbbox();
	
	s = max([bbox[2]-bbox[0], bbox[3]-bbox[1]])
	center = [(bbox[2]+bbox[0])/2, (bbox[3]+bbox[1])/2]
	
	bbox = [center[0]-s/2, center[1]-s/2, center[0]+s/2, center[1]+s/2]
	
	if bbox:
		
		if im.mode == 'RGBA':
			r,g,b,a = im.split()
			im = Image.merge('RGB', (r,g,b))
			
		im = ImageOps.invert(im)
		crop = im.crop(bbox)
		
		return ImageOps.invert(crop)
	else: return im

def symbols_in(image):
	symbols = []
	
	cut = []
	
	pixels = 0
	
	for i in range(image.size[0]):
		whitespace = True
		for j in range(image.size[1]):
			if image.getpixel((i, j)) != (255, 255, 255):
				whitespace = False
				break
		
		if whitespace:
			if pixels > 0:
				cut = cut + [i]
				pixels = 0
		else:
			pixels = pixels + 1
	
	if pixels > 0:
		cut = cut + [i]
		pixels = 0
		
	x = 0
	
	for i in range(len(cut)):
		image = ImageOps.invert(image)
		crop = image.crop([x, 0, cut[i], image.size[1]])
		image = ImageOps.invert(image)
		x = cut[i]
		symbols = symbols + [ImageOps.invert(crop)]
		
	return symbols
	
im1 = (Image.open(sys.argv[1]))
im1 = im1.convert('RGB')

images = []
for symbol in symbols_in(im1):
	symbol = trim(symbol)
	symbol = symbol.resize([8,8], Image.BILINEAR)

	image = []
	for i in range(len(symbol.getdata())):
		value = symbol.getdata()[i]
		ave = 255 - (value[0] + value[1] + value[2])/3 
		image = image + [(16*ave)/255]
	images = images + [image]

train_image = open('train_image.csr', 'a')
train_data = open('train_data.csr', 'a')

for image_data in images:
	for i in range(len(image_data)-1):
		train_image.write(str(image_data[i]) + ' ')
	train_image.write(str(image_data[len(image_data)-1]))
	train_image.write('\n')

	train_data.write(str(data))
	train_data.write('\n')

train_image.close()
train_data.close()