#! python3
# title: greyify
# author: Johannes Katzer
# Copyright 2019, Johannes Katzer
"""
	This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
    der GNU General Public License, wie von der Free Software Foundation,
    Version 3 der Lizenz oder (nach Ihrer Wahl) jeder neueren
    veröffentlichten Version, weiter verteilen und/oder modifizieren.

    Dieses Programm wird in der Hoffnung bereitgestellt, dass es nützlich sein wird, jedoch
    OHNE JEDE GEWÄHR,; sogar ohne die implizite
    Gewähr der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
    Siehe die GNU General Public License für weitere Einzelheiten.

    Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
    Programm erhalten haben. Wenn nicht, siehe <https://www.gnu.org/licenses/>.
"""

import tkinter as tk
from tkinter import filedialog as FileDialogTk
from tkinter import messagebox as MsgBoxTk
from PIL import ImageTk, Image
import os



class ImageProcessor():

	GREY_SHADES = [ [[(0, 0, 0), (0, 0, 0)], [(0, 0, 0), (0, 0, 0)]],
					[[(0, 0, 0), (0, 0, 0)], [(255, 255, 255), (0, 0, 0)]], 
					[[(0, 0, 0), (255, 255, 255)], [(255, 255, 255), (0, 0, 0)]],
					[[(0, 0, 0), (255, 255, 255)], [(255, 255, 255), (255, 255, 255)]],
					[[(255, 255, 255), (255, 255, 255)], [(255, 255, 255), (255, 255, 255)]] ]

	def __init__(self):
		pass


	def do_resizing(self, img, max_size):
		x, y = img.getbbox()[2:]			# calculate scaling factor
		max_x, max_y = max_size
		if x/y >= max_x/max_y:
			k = max_x/x
		else:
			k = max_y/y
		new_size = (int(k*x), int(k*y))	
		img = img.resize(new_size)		
		return img, new_size


	def do_processing(self, path, max_size):		
		original_img = Image.open(path)				
		img = original_img.copy() 		# save for later use...
		img, new_size = self.do_resizing(img, max_size)	# resize 
		#img.thumbnail(self.image_size)		# decrease pixel amount for better performance and .copy()	
		return original_img, img, new_size


	def do_color_inversion(self, img):
		img = img.copy()
		data = list(img.getdata())
		inverted_data = []
		for c in data:
			inverted_color = tuple([int(255-c[i]) for i in range(3)])	# Invert each band of RGB
			inverted_data.append(inverted_color)
		img.putdata(inverted_data)
		return img


	def analyze_image_data(self, data):
		""" Calculates the average brightness of a list of colors. 
		"""
		L = len(data)
		Bright = [sum([int(c[i]) for i in range(3)]) for c in data]
		avg_brightness = round( 4 * (sum(Bright) / (3*255*L)) )
		return avg_brightness


	def do_greyify(self, img):
		""" Convert a colored image into shades of gray. 
		"""
		img = img.copy()
		w, h = img.getbbox()[2:] 			# w, h = img.width(), img.height()
		data = list(img.getdata()) 		# A flat list of the pixels RGB code.
		img_data_feed = list(img.getdata())
		new_data_feed = []
		y = 0
		while y < (h//2):
			L = [img_data_feed[2*y*w + x] for x in range(w)]
			M = [img_data_feed[(2*y+1)*w + x] for x in range(w)]	# Unpack two lines of pixels at a time.
			L_new, M_new = [], []
			while L:
				p, q = L.pop(0), L.pop(0)
				s, t = M.pop(0), M.pop(0)
				b = self.analyze_image_data([p, q, s, t])
				L_new += self.GREY_SHADES[b][0]
				M_new += self.GREY_SHADES[b][1]
			y += 1
			new_data_feed += L_new + M_new			# And generate a flat list again!

		img.putdata(new_data_feed)
		return img



class App():

	def __init__(self, img_path="ExampleImage/pic1.jpg"):

		self.IP = ImageProcessor()

		# The image to be displayed...
		self.current_path = os.getcwd()
		self.image_path = img_path
		self.original_image = None
		self.image_size = None
		self.raw_image = None
		self.image = None
		self.max_image_size = (800, 600) 	# set by user via "Edit..."

		# View		
		self.requested_image_size = None
		self.img_frame = None		
		self.window = self.init_gui()
		self.window.mainloop()


	def init_gui(self, img_zoom=0.2):
		""" Initialize the tinker interface.
		"""
		window = tk.Tk("Greyify - Put grey shades on images.")

		self.requested_image_size = tk.StringVar()

		menu_bar = tk.Menu(master=window)
		window.config(menu=menu_bar)
		file_menu = tk.Menu(master=menu_bar)
		file_menu.add_command(label="Open", command=self.process_image_file)
		file_menu.add_command(label="Save as", command=self.save_image)
		menu_bar.add_cascade(label="File", menu=file_menu)
		edit_menu = tk.Menu(master=menu_bar)
		edit_menu.add_command(label="Reload", command=self.reload_image)
		edit_menu.add_command(label="Invert colors", command=self.invert_colors)
		edit_menu.add_command(label="Greyify", command=self.greyify)
		size_sub_menu = tk.Menu(master=edit_menu)
		size_sub_menu.add_radiobutton(label="800:600", variable=self.requested_image_size, command=self.update_max_image_size)
		size_sub_menu.add_radiobutton(label="1024:756", variable=self.requested_image_size, command=self.update_max_image_size)
		size_sub_menu.add_radiobutton(label="1920:1080", variable=self.requested_image_size, command=self.update_max_image_size)
		edit_menu.add_cascade(label="Size", menu=size_sub_menu)
		menu_bar.add_cascade(label="Edit", menu=edit_menu)
		about_menu = tk.Menu(master=menu_bar)
		about_menu.add_command(label="Help", command=self.popup_help)
		about_menu.add_command(label="License", command=self.popup_license)
		menu_bar.add_cascade(label="About", menu=about_menu)

		greyify_btn = tk.Button(master=window, command=self.greyify, font=("Arial", 14), text="Greyify")
		reload_btn = tk.Button(master=window, command=self.reload_image, font=("Arial", 14), text="Reload")
		#random_btn = tk.Button(master=window, command=self.show_random_img, font=("Arial", 14), text="random")
		next_btn = tk.Button(master=window, command=self.on_next_btn, font=("Arial", 14), text="Next")
		previous_btn = tk.Button(master=window, command=self.on_previous_btn, font=("Arial", 14), text="Previous")
		
		self.raw_image = self.process_image_file(file=self.image_path)
		self.img_frame = tk.Label(master=window)
		self.update_img()
		
		self.img_frame.grid(column=0, row=0, columnspan=5)				# position on / write to screen
		greyify_btn.grid(column=2, row=1)
		reload_btn.grid(column=2, row=2)
		#random_btn.pack()
		next_btn.grid(column=3, row=2, sticky="W")
		previous_btn.grid(column=1, row=2, sticky="E")
		return window


	def update_max_image_size(self):
		size_str = self.requested_image_size.get()
		size = tuple([int(x) for x in size_str.split(":")])
		self.max_image_size = size
		self.raw_image, self.image_size = self.IP.do_resizing(self.raw_image, self.max_image_size)
		self.update_img()


	def process_image_file(self, file=""):
		if file:
			self.image_path = file
		else:
			filename =  FileDialogTk.askopenfilename(initialdir=self.current_path, title="Select file",filetypes=(("jpeg files","*.jpg"),("all files","*.*")))
			if filename:
				self.image_path = filename		
		self.original_image, img, self.size  = self.IP.do_processing(self.image_path, self.max_image_size)	
		return img


	def next_image(self, direction=1):
		current_path = "/".join(self.image_path.split("/")[:-1])
		current_image = self.image_path.split("/")[-1].lower()
		L = [x.lower() for x in os.listdir(current_path)]
		file_name, file_ending = current_image.split(".")[0], current_image.split(".")[1]
		try:
			i = L.index(current_image)
		except KeyError:
			print("File not found: Cannot find the image.")
		self.image_path = current_path + "/" + L[(i+direction) % len(L)]
		self.current_path = current_path
		self.reload_image()


	def on_next_btn(self):
		self.next_image()


	def on_previous_btn(self):
		self.next_image(-1)


	def update_img(self):
		""" Generates a Tk Image from self.raw_image and wraps it into self.img_frame.
		"""
		self.image = ImageTk.PhotoImage(self.raw_image)
		self.img_frame.configure(image=self.image)


	def save_image(self):
		""" Opens a filedialog and saves the currently displayed image. 
		"""
		path = FileDialogTk.asksaveasfilename()
		if path:
			self.raw_image.save(path)
			return True
		return False


	def reload_image(self):
		#self.raw_image = self.original_image
		self.raw_image = self.process_image_file(self.image_path)
		self.update_img()


	def invert_colors(self):		
		self.raw_image = self.IP.do_color_inversion(self.raw_image)
		self.update_img()


	def greyify(self):			
		self.raw_image = self.IP.do_greyify(self.raw_image)	
		self.update_img()


	def popup_license(self):
		license_text = "Copyright 2019, Johannes Katzer \n\n" +\
							"This program is free software: you can redistribute it and/or modify " +\
						    "it under the terms of the GNU General Public License as published by " +\
						    "the Free Software Foundation, either version 3 of the License, or " +\
						    "(at your option) any later version. \n" +\
						    "This program is distributed in the hope that it will be useful, " +\
						    "but WITHOUT ANY WARRANTY; without even the implied warranty of " +\
						    "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the " +\
						    "GNU General Public License for more details. \n" +\
						    "You should have received a copy of the GNU General Public License " +\
						    "along with this program.  If not, see <http://www.gnu.org/licenses/>."
		image_author = "The images included in this application are taken from 'https://thispersondoesnotexist.com/image'"
		MsgBoxTk.showinfo("License", license_text + "\n\n" + image_author)

	def popup_help(self):
		short_descr = ""
		MsgBoxTk.showinfo("Help", license_text + "\n" + image_author)

if __name__ == '__main__':

	app = App()
