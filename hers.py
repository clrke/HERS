import pylab as pl
import sys
import Image, ImageChops, ImageOps
import math
import numpy

from sklearn import datasets, svm, metrics

digits = datasets.load_digits()

classifier = svm.SVC(gamma=0.001)

train_image = open('train_image.csr', 'r')
train_data = open('train_data.csr', 'r')

new_images = []
new_data = []

for line in train_image:	
	new_images = new_images + [map(int, line.split(' '))]
	
for line in train_data:
	new_data = new_data + [line.rstrip('\n')]

train_image.close();
train_data.close();

classifier.fit(new_images, new_data)
		
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
	
	
predicted = classifier.predict(images)
print predicted

for i in range(len(images)):
	numpy_image = numpy.ndarray([8, 8], 'float')

	for j in range(64):
		numpy_image[j/8, j%8] = images[i][j]

	pl.subplot(1, len(images)+1, i+1)
	pl.axis('off')
	pl.imshow(numpy_image, cmap=pl.cm.gray_r, interpolation='nearest')
	pl.title('%s' % predicted[i])

def number(x):
	if x == '1' or x == '2' or x == '3' or x == '4' or x == '5' or x == '6' or x == '7' or x == '8' or x == '9' or x == '0':
		return True
	return False
	
def normalize(symbols):
	normalized = []
	
	symbol = ''
	for i in range(len(symbols)):
		if number(symbols[i]):
			symbol = symbol + symbols[i]
		else:
			if len(symbol) > 0:
				normalized = normalized + [symbol]
				symbol = ''
			normalized = normalized + [symbols[i]]

	if len(symbol) > 0:
		normalized = normalized + [symbol]
		
	return normalized

class Parse:
	def __init__(self, value, i):
		self.value = value	
		self.i = i
	
def parse0(symbols, i): # parses n or ( n )
	if symbols[i] == '(':
		i = i + 1
		parse = parse3(symbols, i)
		
		if symbols[i + parse.i] == ')':
			return Parse(parse.value, parse.i + 2)
	else:
		return Parse(float(symbols[i]), 1)
	
def parse1(symbols, i): # parses sqrt n or n ^ n
	if symbols[i] == 'sqrt':
		i = i + 1
		parse = parse1(symbols, i)
		return Parse(math.sqrt(parse.value), parse.i + 1)
		
	else:
		parse = parse0(symbols, i)

		if parse.i+i < len(symbols):
			if symbols[parse.i + i] == '^':
				parse.i = parse.i + 1
				parse_ = parse1(symbols, parse.i + i)
				return Parse(parse.value ** parse_.value, parse_.i + parse.i)
			
	return Parse(parse.value, parse.i)
	
def parse2(symbols, i): # parses n x n or n / n
	parse = parse1(symbols, i)
	
	if parse.i+i < len(symbols):
		if symbols[parse.i + i] == '*':
			parse.i = parse.i + 1
			parse_ = parse2(symbols, parse.i + i)
			return Parse(parse.value * parse_.value, parse_.i + parse.i)
		if symbols[parse.i + i] == '/':
			parse.i = parse.i + 1
			parse_ = parse2(symbols, parse.i + i)
			return Parse(parse.value / parse_.value, parse_.i + parse.i)
			
	return Parse(parse.value, parse.i)
	
def parse3(symbols, i): # parses n + n or n - n
	parse = parse2(symbols, i)
	
	if parse.i+i < len(symbols):
		if symbols[parse.i+i] == '+':
			parse.i = parse.i + 1
			parse_ = parse3(symbols, parse.i + i)
			return Parse(parse.value + parse_.value, parse_.i + parse.i)
		if symbols[parse.i+i] == '-':
			parse.i = parse.i + 1
			parse_ = parse3(symbols, parse.i + i)
			return Parse(parse.value - parse_.value, parse_.i + parse.i)
	return Parse(parse.value, parse.i)
			
def solve(symbols):
	return parse3(symbols, 0)

try:	
	predicted = normalize(predicted)
	print predicted
	answer = solve(predicted)
	if answer.i != len(predicted):
		raise
	print '=', answer.value
except:
	answer = Parse('?', 0)
	print '=', answer.value
	
pl.subplot(1, len(images)+1, len(images)+1)
pl.axis('off')
pl.title('= %s' % answer.value)
	
pl.show()