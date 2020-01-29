# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

import math
import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty
from mathutils import Vector, Euler, Matrix
from random import random as rand, seed, uniform as randuni, randint

#############################################################
# COMPUTE THE LENGTH OF THE BOARD AFTER THE TILT
#############################################################
# The 'Tilt' is not a rotation.
# It's a translation of the two first vertex on X axis (translatex)
# and a translation of the two ending vertex on the Y axis (translatey)
# This will distord the board. So, to keep the end shape and the length
# I compute the end shape's opposite (1) then the hypotenuse (3)
# using the width (2) and the angle (offsetx) from the Pythagoras Theorem (yeaah trigonometry !)
# Then, I compute the new length of the board (translatex)
#     1
#   *---*-----------------------           |   *----*
#   |  /                                   |    \    \
# 2 | / 3                                  V     \    \
#   |/                                 translatey \    \
#   *---------------------------                   *----*  ---> translatex

def calculangle(tilt, width, lengthboard):

	opposite = width * math.tan(tilt)
	hyp = math.sqrt(width ** 2 + opposite ** 2)
	translatex = lengthboard * math.sin(tilt)
	translatey = math.sqrt((lengthboard ** 2) - (translatex ** 2))

	return (hyp, translatex, translatey)

#############################################################
# BOARD
#############################################################
# Mesh of the board.
# If the boards are tilt, we need to inverse the angle each time we call this function :
# /\/\/ -> So each board will be upside-down compared to each other
def board(start, left, right, end, tilt, translatex, hyp, herringbone, gapy, height, randheight):

	gapx = 0
	height = randheight * randuni(0, height)                              # Add randomness to the height of the boards
	if not herringbone: gapy = 0

	if tilt > 0:                                                          # / / / -> 1 board, 3 board, 5 board...
		shiftdown = translatex
		shiftup = 0
		if herringbone:
			gapy = gapy / 2
			gapx = 0

	else:                                                                 #  \ \ \-> 2 board, 4 board, 6 board...
		shiftdown = 0
		shiftup = -translatex
		if herringbone:
			gapy = gapy / 2
			gapx = gapy * 2

	dl = Vector((left + shiftdown + gapx, start - gapy, height))          # down left [0,0,0]
	dr = Vector((right + shiftdown + gapx, start - gapy, height))         # down right [1,0,0]
	ur = Vector((right - shiftup + gapx, end - gapy, height))             # up right [1,1,0]
	ul = Vector((left - shiftup + gapx, end - gapy, height))              # up left [0,1,0]

	if herringbone:
		if tilt > 0:                                                      # / / / -> 1 board, 3 board, 5 board...
			ur[0] = ur[0] - (hyp / 2)
			ur[1] = ur[1] + (hyp / 2)
			dr[0] = dr[0] - (hyp / 2)
			dr[1] = dr[1] + (hyp / 2)
		else:                                                             #  \ \ \-> 2 board, 4 board, 6 board...
			dl[0] = dl[0] + (hyp / 2)
			dl[1] = dl[1] + (hyp / 2)
			ul[0] = ul[0] + (hyp / 2)
			ul[1] = ul[1] + (hyp / 2)

	verts = (dl, ul, ur, dr)

	return (verts)

#############################################################
# TRANSVERSAL
#############################################################
# Creation of the boards in the interval.
# --    -> tilt > 0 : No translation on the x axis
# \\
#  --   -> tilt < 0 : Translation on the x axis to follow the tilted boards
# //

def transversal(left, right, start, tilt, translatex, gapy, gapx, gaptrans, randgaptrans, end, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty):
	gaptrans = gaptrans + (randgaptrans * randuni(0, gaptrans))           # Add randomness to the gap of the transversal of the boards
	if borders: nbrtrans = 1                                              # Constrain the transversal to 1 board if borders activate
	if gaptrans < (end-start)/(nbrtrans+1):                               # The gap can't be > to the width of the interval
		x = 0
		lengthint = 0
		if tilt > 0: translatex = 0                                       # Constrain the board to 0 on the x axis
		width = ((end - start) - (gaptrans * (nbrtrans + 1))) * (1 / nbrtrans)# Width of 1 board in the interval
		startint = start + gaptrans                                       # Find the start of the first board
		while right > lengthint:                                          # While the transversal is < to the right edge of the floor (if unlock) or the board (if locked)
			if locktrans:                                                 # If the length of the transversal is unlock
				lengthint += lengthtrans                                  # Add the length

			if not locktrans or (lengthint > right): lengthint = right    # Constrain the length of the transversal to th length of the board (locked)

			while x < nbrtrans:                                           # Nbr of boards in the transversal
				x += 1
				endtrans = startint + width                               # Find the end of the board

				# Create the boards in the interval
				nbvert = len(verts)
				verts.extend(interval(left, lengthint, startint, translatex, gapy, endtrans, height, randheight, width, gapx, gaptrans, borders, endfloor, tilt, shifty))
				if shifty == 0 and borders and tilt == 0:
					faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3, nbvert+4, nbvert+5))
				else :
					faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3))
				startint = endtrans + gaptrans                            # Find the start of the next board

			#------------------------------------------------------------
			# Increment / initialize
			#------------------------------------------------------------
			if locktrans:
				left = lengthint + gaptrans
				lengthint += gaptrans
				x = 0
				endtrans = start + width
				startint = start + gaptrans

			# The boards can't be > to the length of the floor
			if left > right:
				lengthint = left


#############################################################
# INTERVAL
#############################################################
# Creation of 1 transversal

def interval(left, right, start, translatex, gapy, end, height, randheight, width, gapx, gaptrans, borders, endfloor, tilt, shifty):
	height = randheight * randuni(0, height)                              # Add randomness to the height of the boards
	if gaptrans == gapx: bgap = 0
	else: bgap = gaptrans
	if shifty == 0 and borders and tilt == 0:
		tipleft = left-gapx/2+bgap
		tipright = right+gapx/2-bgap
		if tipleft < 0: tipleft = 0                                       # Constrain the first left tip to 0...
		elif tipleft > left: tipleft = left                               # ...and the other to the left of the board
		if tipright < right: tipright = right                             # Constrain the right tips to the right of the board..
		if endfloor > 0 : tipright = endfloor                             # ...and the last one to the last board of the floor
		dr = Vector((right, start, height))                               # Down right
		dl = Vector((left, start, height))                                # Down left
		tl = Vector((tipleft, start+(width/2), height))                   # Tip left
		ul = Vector((left, end, height))                                  # Up left
		ur = Vector((right, end, height))                                 # Up right
		tr = Vector((tipright, start+(width/2), height))                  # Tip right

		verts = (dr, dl, tl, ul, ur, tr)

	else:
		dr = Vector((right + translatex, start, height))                  # Down right
		dl = Vector((left + translatex, start, height))                   # Down left
		ul = Vector((left + translatex, end, height))                     # Up left
		ur = Vector((right + translatex, end, height))                    # Up right

		verts = (dl, ul, ur, dr)

	return verts

#############################################################
# BORDERS
#############################################################
# Creation of the borders

def border(left, right, start, gapy, end, height, randheight, gaptrans, randgaptrans, floor_length, translatey):
	height = randheight * randuni(0, height)                              # Add randomness to the height of the boards
	gaptrans = gaptrans + (randgaptrans * randuni(0, gaptrans))
	tdogapy = gapy
	tupgapy = gapy
	if end+tupgapy > floor_length:
		tupgapy = (floor_length - end)
	tipdown = start-tdogapy/2+gaptrans
	tipup = end+tupgapy/2-gaptrans
	if tipup < end: tipup = end
	if tipdown < 0 : tipdown = 0
	elif tipdown > start: tipdown = start
	td = Vector(((left + right) /2, tipdown, height))                     # Tip down
	tdl = Vector((left, start, height))                                   # Tip down left
	tup = Vector((left, end, height))                                     # Tip up left
	tu = Vector(((left + right) /2, tipup, height))                       # Tip up
	tur = Vector((right, end, height))                                    # Tip up right
	tdr = Vector((right, start, height))                                  # Tip down right

	verts = (td, tdl, tup, tu, tur, tdr)

	return verts

# -------------------------------------------------------------------- #
def get_lock_length(self):
	"""Get the number of boards for the surface length"""
	plancher = bpy.data.objects[self.id_data.name]
	try:
		return self["lock_length"]
	except KeyError:
		return False

def set_lock_length(self, value):
	plancher = bpy.data.objects[self.id_data.name]
	_, _, translatey = calculangle(plancher.Plancher.tilt, plancher.Plancher.width, plancher.Plancher.lengthboard)
	plancher.Plancher.nbr_length = round(plancher.Plancher.floor_length / (translatey + plancher.Plancher.gapy))
	print("SET LOCK")
	self["lock_length"] = value

# -------------------------------------------------------------------- #
def get_nbr_length(self):
	"""Get the surface length for the number of boards"""
	plancher = bpy.data.objects[self.id_data.name]
	try:
		return self["nbr_length"]
	except KeyError:
		return 1

def set_nbr_length(self, value):
	plancher = bpy.data.objects[self.id_data.name]
	_, _, translatey = calculangle(plancher.Plancher.tilt, plancher.Plancher.width, plancher.Plancher.lengthboard)
	plancher.Plancher.floor_length = (plancher.Plancher.nbr_length * (translatey + plancher.Plancher.gapy)) - plancher.Plancher.gapy
	self["nbr_length"] = value


# -------------------------------------------------------------------- #
def get_herringbone(self):
	plancher = bpy.data.objects[self.id_data.name]
	try:
		return self["herringbone"]
	except KeyError:
		return False

def set_herringbone(self, value):
	plancher = bpy.data.objects[self.id_data.name]
	plancher.Plancher.lock_length = value
	self["herringbone"] = value

# -------------------------------------------------------------------- #
def update_type(self,context):
	"""Update the type of floor """

	parquet = bpy.data.objects[self.id_data.name]
	if plancher.Plancher.floor_type == "Stack Bond":
		create_stack_bond(parquet)



# -------------------------------------------------------------------- #
def create_stack_bond(parquet):
	"""Create a Stack Bond type of floor """

	bpy.ops.mesh.primitive_cube_add()
	context.active_object.name = "Parquet"
	parquet = context.object
	parquet.Plancher.nbrboards = 2










	x = 0
	y = 0
	verts = []
	faces = []
	listinter = []
	start = 0
	left = 0
	bool_translatey = True
	end = lengthboard
	interleft = 0
	interright = 0


	if gapy == 0:
		fill_gap_y = False

	if herringbone:
		shifty = 0
		tilt = math.radians(45)
		randwith = 0
		fill_gap_y = False

	# Compute the new length and width of the board if tilted
	hyp, translatex, translatey = calculangle(tilt, width, lengthboard)

	randwidth = hyp + (randwith * randuni(0, hyp))
	right = randwidth
	end = translatey - (translatey * randuni(randomshift, shifty))

	if herringbone or lock_length:
		floor_length = (nbr_length * (translatey + gapy)) - gapy
	noglue = gapx
	#------------------------------------------------------------
	# Loop for the boards on the X axis
	#------------------------------------------------------------
	while x < nbrboards:
		x += 1

		if glue and (x % nbrshift != 0):
			gapx = gaptrans
		else:
			gapx = noglue


		if (x % nbrshift != 0): bool_translatey = not bool_translatey
		if end > floor_length :
			end = floor_length

		# Creation of the first board
		nbvert = len(verts)
		verts.extend(board(start, left, right, end, tilt, translatex, hyp, herringbone, gapy, height, randheight))
		faces.append((nbvert,nbvert+1, nbvert+2, nbvert+3))

		# Start a new column (Y)
		start2 = end + gapy
		end2 = start2
		#------------------------------------------------------------
		# TRANSVERSAL
		#------------------------------------------------------------
		# listinter = List of the length (left) of the interval || x = nbr of the actual column || nbrshift = nbr of columns to shift || nbrboards = Total nbr of column
		# The modulo (%) is here to determined if the actual interval has to be shift
		listinter.append(left)
		endfloor = 0
		if x == nbrboards: endfloor = right
		if fill_gap_y and ((x % nbrshift == 0) or ((x % nbrshift != 0) and (x == nbrboards))) and (end < floor_length) and not locktrans:
			if start2 > floor_length:
				start2 = floor_length
			transversal(listinter[0], right, end, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)
		elif fill_gap_y and (x == nbrboards) and locktrans:
			if start2 > floor_length: start2 = floor_length
			transversal(listinter[0], right, end, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)

		#------------------------------------------------------------
		# BORDERS
		#------------------------------------------------------------
		# Create the borders in the X gap if boards are glued
		if borders and glue and (x % nbrshift == 0) and translatex == 0 and (x != nbrboards) and (shifty == 0) and (gaptrans*2 < gapx):
			nbvert = len(verts)
			verts.extend(border(right+gaptrans, right+noglue-gaptrans, start, gapy, end, height, randheight, gaptrans, randgaptrans, floor_length, start2 + translatey))
			faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3, nbvert+4, nbvert+5))

		#------------------------------------------------------------
		# Loop for the boards on the Y axis
		#------------------------------------------------------------
		while floor_length > end2 :
			if end2 > floor_length :
				end2 = floor_length

			if tilt < 0:
				tilt = tilt * (-1)
			else:
				tilt = -tilt

			# Creation of the board
			nbvert = len(verts)
			verts.extend(board(start2, left, right, end2, tilt, translatex, hyp, herringbone, gapy, height, randheight))
			faces.append((nbvert,nbvert+1, nbvert+2, nbvert+3))

			#------------------------------------------------------------
			# BORDERS
			#------------------------------------------------------------
			# Create the borders in the X gap if boards are glued
			if borders and glue and (x % nbrshift == 0) and translatex == 0 and (x != nbrboards) and (shifty == 0) and (gaptrans*2 < gapx):
				nbvert = len(verts)
				verts.extend(border(right+gaptrans, right+noglue-gaptrans, start2, gapy, end2, height, randheight, gaptrans, randgaptrans, floor_length, start2 + translatey))
				faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3, nbvert+4, nbvert+5))

			# New column
			start2 += translatey + gapy

			#------------------------------------------------------------
			# TRANSVERSAL
			#------------------------------------------------------------
			# x = nbr of the actual column || nbrshift = nbr of columns to shift || nbrboards = Total nbr of column
			# The modulo (%) is  here to determined if the actual interval as to be shift
			endfloor = 0
			if x == nbrboards: endfloor = right
			if fill_gap_y and ((x % nbrshift == 0) or ((x % nbrshift != 0) and (x == nbrboards))) and (end2 < floor_length) and not locktrans:
				if start2 > floor_length: start2 = floor_length         # Cut the board if it's > than the floor
				transversal(listinter[0], right, end2, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)

			elif fill_gap_y and locktrans and (x == nbrboards) and (end2 < floor_length) :
				if start2 > floor_length: start2 = floor_length         # Cut the board if it's > than the floor
				transversal(listinter[0], right, end2, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)

			end2 = start2
		#------------------------------------------------------------#

		#------------------------------------------------------------
		# Increment / initialize
		#------------------------------------------------------------
		if (x % nbrshift == 0) and not locktrans:
			listinter = []
		if not herringbone:
			left += gapx
			right += gapx
		else:
			right += gapy * 2
			left += gapy * 2
		left += randwidth
		randwidth = hyp + (randwith * randuni(0, hyp))
		right += randwidth
		#------------------------------------------------------------#

		#------------------------------------------------------------
		# Shift on the Y axis
		#------------------------------------------------------------
		# bool_translatey is turn on and off at each new column to reverse the direction of the shift up or down.
		if (bool_translatey and shifty > 0):
			if (x % nbrshift == 0 ):
				end = translatey * randuni(randomshift, shifty)
			bool_translatey = False
		else:
			if (x % nbrshift == 0 ):
				end = translatey - (translatey * randuni(randomshift, shifty))
			bool_translatey = True
		#------------------------------------------------------------#

		#------------------------------------------------------------
		# Herringbone only
		#------------------------------------------------------------
		# Invert the value of the tilted parameter
		if tilt < 0:
		   tilt = tilt * (-1)
		#------------------------------------------------------------#

	#------------------------------------------------------------         # End of the loop on X axis
	return verts, faces





































#############################################################
# FLOOR BOARD
#############################################################
# Creation of a column of boards

def parquet(lock_length, nbrboards, nbr_length, height, randheight, width, randwith, gapx, lengthboard, gapy, shifty, nbrshift, tilt, herringbone, randoshifty, floor_length, fill_gap_y, gaptrans, randgaptrans, glue, borders, lengthtrans, locktrans, nbrtrans):

	x = 0
	y = 0
	verts = []
	faces = []
	listinter = []
	start = 0
	left = 0
	bool_translatey = True                                                # shifty = 0
	end = lengthboard
	interleft = 0
	interright = 0
	if locktrans:
		shifty = 0                                                        # No shift with unlock !
		glue = False
		borders = False
	if shifty: locktrans = False                                          # Can't have the boards shifted and the tranversal unlocked
	if randoshifty > 0:                                                   # If randomness in the shift of the boards
		randomshift = shifty * (1-randoshifty)                            # Compute the amount of randomness in the shift
	else:
		randomshift = shifty                                              # No randomness

	if shifty > 0:
		tilt = 0
		herringbone = False

	if gapy == 0:                                                         # If no gap on the Y axis : the transversal is not possible
		fill_gap_y = False
	if herringbone:                                                       # Constraints if herringbone is choose :
		shifty = 0                                                        # - no shift
		tilt = math.radians(45)                                           # - Tilt = 45°
		randwith = 0                                                      # - No random on the width
		fill_gap_y = False                                                     # - No transversal

	# Compute the new length and width of the board if tilted
	hyp, translatex, translatey = calculangle(tilt, width, lengthboard)

	randwidth = hyp + (randwith * randuni(0, hyp))                        # Randomness in the width
	right = randwidth                                                     # Right = width of the board
	end = translatey - (translatey * randuni(randomshift, shifty))        # Randomness in the length

	if herringbone or lock_length:                                        # Compute the length of the floor based on the length of the boards
		floor_length = (nbr_length * (translatey + gapy)) - gapy
	noglue = gapx
	#------------------------------------------------------------
	# Loop for the boards on the X axis
	#------------------------------------------------------------
	while x < nbrboards:                                                  # X axis
		x += 1

		if glue and (x % nbrshift != 0):
			gapx = gaptrans
		else:
			gapx = noglue


		if (x % nbrshift != 0): bool_translatey = not bool_translatey     # Invert the shift
		if end > floor_length :                                          # Cut the last board if it's > than the floor
			end = floor_length

		# Creation of the first board
		nbvert = len(verts)
		verts.extend(board(start, left, right, end, tilt, translatex, hyp, herringbone, gapy, height, randheight))
		faces.append((nbvert,nbvert+1, nbvert+2, nbvert+3))

		# Start a new column (Y)
		start2 = end + gapy
		end2 = start2
		#------------------------------------------------------------
		# TRANSVERSAL
		#------------------------------------------------------------
		# listinter = List of the length (left) of the interval || x = nbr of the actual column || nbrshift = nbr of columns to shift || nbrboards = Total nbr of column
		# The modulo (%) is here to determined if the actual interval has to be shift
		listinter.append(left)                                            # Keep the length of the actual interval
		endfloor = 0
		if x == nbrboards: endfloor = right
		if fill_gap_y and ((x % nbrshift == 0) or ((x % nbrshift != 0) and (x == nbrboards))) and (end < floor_length) and not locktrans:
			if start2 > floor_length:
				start2 = floor_length             # Cut the board if it's > than the floor
			transversal(listinter[0], right, end, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)
		elif fill_gap_y and (x == nbrboards) and locktrans:
			if start2 > floor_length: start2 = floor_length             # Cut the board if it's > than the floor
			transversal(listinter[0], right, end, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)

		#------------------------------------------------------------
		# BORDERS
		#------------------------------------------------------------
		# Create the borders in the X gap if boards are glued
		if borders and glue and (x % nbrshift == 0) and translatex == 0 and (x != nbrboards) and (shifty == 0) and (gaptrans*2 < gapx):
			nbvert = len(verts)
			verts.extend(border(right+gaptrans, right+noglue-gaptrans, start, gapy, end, height, randheight, gaptrans, randgaptrans, floor_length, start2 + translatey))
			faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3, nbvert+4, nbvert+5))

		#------------------------------------------------------------
		# Loop for the boards on the Y axis
		#------------------------------------------------------------
		while floor_length > end2 :                                      # Y axis
			end2 = start2 + translatey                                    # New column
			if end2 > floor_length :                                     # Cut the board if it's > than the floor
				end2 = floor_length

			if tilt < 0:                                                  # This part is used to inversed the tilt of the boards
				tilt = tilt * (-1)
			else:
				tilt = -tilt

			# Creation of the board
			nbvert = len(verts)
			verts.extend(board(start2, left, right, end2, tilt, translatex, hyp, herringbone, gapy, height, randheight))
			faces.append((nbvert,nbvert+1, nbvert+2, nbvert+3))

			#------------------------------------------------------------
			# BORDERS
			#------------------------------------------------------------
			# Create the borders in the X gap if boards are glued
			if borders and glue and (x % nbrshift == 0) and translatex == 0 and (x != nbrboards) and (shifty == 0) and (gaptrans*2 < gapx):
				nbvert = len(verts)
				verts.extend(border(right+gaptrans, right+noglue-gaptrans, start2, gapy, end2, height, randheight, gaptrans, randgaptrans, floor_length, start2 + translatey))
				faces.append((nbvert, nbvert+1, nbvert+2, nbvert+3, nbvert+4, nbvert+5))

			# New column
			start2 += translatey + gapy

			#------------------------------------------------------------
			# TRANSVERSAL
			#------------------------------------------------------------
			# x = nbr of the actual column || nbrshift = nbr of columns to shift || nbrboards = Total nbr of column
			# The modulo (%) is  here to determined if the actual interval as to be shift
			endfloor = 0
			if x == nbrboards: endfloor = right
			if fill_gap_y and ((x % nbrshift == 0) or ((x % nbrshift != 0) and (x == nbrboards))) and (end2 < floor_length) and not locktrans:
				if start2 > floor_length: start2 = floor_length         # Cut the board if it's > than the floor
				transversal(listinter[0], right, end2, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)

			elif fill_gap_y and locktrans and (x == nbrboards) and (end2 < floor_length) :
				if start2 > floor_length: start2 = floor_length         # Cut the board if it's > than the floor
				transversal(listinter[0], right, end2, tilt, translatex, gapy, noglue, gaptrans, randgaptrans, start2, nbrtrans, verts, faces, locktrans, lengthtrans, height, randheight, borders, endfloor, shifty)

			end2 = start2                                                 # End of the loop on Y axis
		#------------------------------------------------------------#

		#------------------------------------------------------------
		# Increment / initialize
		#------------------------------------------------------------
		if (x % nbrshift == 0) and not locktrans: listinter = []          # Initialize the list of interval if the nbr of boards to shift is reaches
		if not herringbone:                                               # If not herringbone
			left += gapx                                                  #  Add the value of gapx to the left side of the boards
			right += gapx                                                 #  Add the value of gapx to the right side of the boards
		else:                                                             # If herringbone, we don't use the gapx anymore in the panel
			right += gapy * 2                                             #  used only the gapy
			left += gapy * 2                                              #  ""     ""      ""
		left += randwidth                                                 # Add randomness on the left side of the boards
		randwidth = hyp + (randwith * randuni(0, hyp))                    # Compute the new randomness on the width (hyp)
		right += randwidth                                                # Add randomness on the right side of the boards
		#------------------------------------------------------------#

		#------------------------------------------------------------
		# Shift on the Y axis
		#------------------------------------------------------------
		# bool_translatey is turn on and off at each new column to reverse the direction of the shift up or down.
		if (bool_translatey and shifty > 0):                              # If the columns are shifted
			if (x % nbrshift == 0 ):                                      # If the nbr of column to shift is reach
				end = translatey * randuni(randomshift, shifty)           # Compute and add the randomness to the new end (translatey) shifted
			bool_translatey = False                                       # Turn on the boolean, so it will be inverted for the next colmun
		else:
			if (x % nbrshift == 0 ):
				end = translatey - (translatey * randuni(randomshift, shifty)) # Compute and add the randomness to the new end (translatey) shifted
			bool_translatey = True                                        # Turn on the boolean, so it will be inverted for the next colmun
		#------------------------------------------------------------#

		#------------------------------------------------------------
		# Herringbone only
		#------------------------------------------------------------
		# Invert the value of the tilted parameter
		if tilt < 0:                                                      # The tilted value is inverted at each column
		   tilt = tilt * (-1)                                             # so the boards will be reverse
		#------------------------------------------------------------#

	#------------------------------------------------------------         # End of the loop on X axis
	return verts, faces

#############################################################
# PANEL PRINCIPAL
#############################################################
class MAIN_PT_Plancher(bpy.types.Panel):
	bl_idname = "MAIN_PT_Plancher"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Plancher"
	bl_label = "Plancher"
	# bl_context = "objectmode"

	#------------------------------------------------------------
	# PANEL
	#------------------------------------------------------------
	def draw(self, context):
		layout = self.layout
		myObj = bpy.context.active_object
		col = layout.column()
		cobj = context.object
		if not myObj or myObj.name != 'Plancher' :
			layout.operator('plancher.add_object')

		if bpy.context.mode == 'EDIT_MESH':
			col = layout.column()
			col = layout.column()
			col.label(text="Vertex / UV")
			col = layout.column(align=True)
			#Vertex Color
			if cobj.Plancher.colphase == 0:
				row = col.row(align=True)
				row.prop(cobj.Plancher, "colrand")
			if cobj.Plancher.colrand > 0:
				row = col.row(align=True)
				row.prop(cobj.Plancher, "allrandom", text='All random', icon='BLANK1')
			#Phase Color
			if cobj.Plancher.colrand == 0:
				row = col.row(align=True)
				row.prop(cobj.Plancher, "colphase")

			#Seed color
			row = col.row(align=True)
			row.prop(cobj.Plancher, "colseed")
			#layout.label('Plancher only works in Object Mode.')
		elif myObj and myObj.name == 'Plancher'  :
			#-------------------------------------------------------------FLOOR
			col = layout.column(align=True)
			col.label(text="SURFACE")
			row = col.row(align=True)
			row.prop(cobj.Plancher, "lock_length", icon='BLANK1')
			row = col.row(align=True)
			if cobj.Plancher.lock_length:
				row.prop(cobj.Plancher, "nbr_length")
			else:
				row.prop(cobj.Plancher, "floor_length")
			row = col.row(align=True)
			row.prop(cobj.Plancher, "height")
			row.prop(cobj.Plancher, "randheight")

			col = layout.column()
			col = layout.column(align=True)

			#-------------------------------------------------------------BOARDS
			col.label(text="BOARD")
			row = col.row(align=True)
			row.prop(cobj.Plancher, "lengthboard")
			row.prop(cobj.Plancher, "width")
			row = col.row(align = True)
			row.prop(cobj.Plancher, "nbrboards")
			row.prop(cobj.Plancher, "randwith", text="Random", slider=True)

			col.separator
			col = layout.column(align=True)

			#-------------------------------------------------------------GAP
			if cobj.Plancher.herringbone == False:
				col.label(text="GAP")
				row = col.row(align=True)
				row.prop(cobj.Plancher, "gapx")
				row.prop(cobj.Plancher, "gapy")
				# if cobj.Plancher.gapy > 0:

			#-------------------------------------------------------------TRANSVERSAL
				col2 = col.column(align=True)
				col2.enabled = False if (cobj.Plancher.locktrans or cobj.Plancher.tilt > 0 or cobj.Plancher.gapy == 0) else True
				row_shift = col2.row(align=True)
				row_shift.prop(cobj.Plancher, "shifty")
				row_shift.prop(cobj.Plancher, "randoshifty")
				col2.prop(cobj.Plancher, "nbrshift")

				# if cobj.Plancher.gapy > 0:

				col2 = layout.column(align=True)
				col2.enabled = False if (cobj.Plancher.gapy == 0) else True
				col2.label(text="FILL GAP Y")
				row = col2.row(align=True)
				row.prop(cobj.Plancher, "fill_gap_y", text='Fill GapY', icon='BLANK1')

				if cobj.Plancher.fill_gap_y:
					row.prop(cobj.Plancher, "locktrans", text='Unlock', icon='BLANK1')
					row = col2.row(align=True)
					if cobj.Plancher.locktrans: row.prop(cobj.Plancher, "lengthtrans")
					else: row.prop(cobj.Plancher, "nbrshift", text='Column')
					row.prop(cobj.Plancher, "nbrtrans", text='Row')
				if (cobj.Plancher.fill_gap_y or cobj.Plancher.glue):
					row = col2.row(align=True)
					row.prop(cobj.Plancher, "gaptrans")
					row.prop(cobj.Plancher, "randgaptrans")
				row2 = col2.row(align=True)

				# if not cobj.Plancher.locktrans:
				row2.enabled = False if (not col2.enabled or cobj.Plancher.locktrans or cobj.Plancher.nbrshift == 1) else True
				row2.prop(cobj.Plancher, "glue", text='Glue GapX', icon='BLANK1')
				# row3 = col2.row(align=True)
				# row3.enabled = False if (not row2.enabled or not cobj.Plancher.glue) else True
				if cobj.Plancher.glue:
					row2.prop(cobj.Plancher, "borders", text='Borders GapX', icon='BLANK1')

			#-------------------------------------------------------------CHEVRON / HERRINGBONE

			if cobj.Plancher.shifty == 0 :
				if cobj.Plancher.herringbone == False:
					col = layout.column()
					col = layout.column(align=True)
					col.label(text="CHEVRON")
					row = col.row(align=True)
					row.prop(cobj.Plancher, "tilt")

				if cobj.Plancher.herringbone == True:
					col = layout.column()
					col = layout.column(align=True)
					row = col.row(align=True)
					row.prop(cobj.Plancher, "gapy")
					self.lock_length = True

				row = col.row(align=True)
				row.prop(cobj.Plancher, "herringbone", text='Herringbone', icon='BLANK1')

			#-------------------------------------------------------------SEED
			col = layout.column()
			col = layout.column(align=True)
			col.label(text="SEED")
			row = col.row(align=True)
			row.prop(cobj.Plancher, "colseed")

			#-------------------------------------------------------------UV / VERTEX
			# Warning, 'cause all the parameters are lost when going back to Object mode...
			# Have to do something with this.
			col = layout.column()
			col = layout.column()
			col = layout.column(align=True)
			col.label(text="Go in edit mode for UV !")
			col.label(text="Warning ! Any change here will reset the uv/color !")

#############################################################
# FUNCTION PLANCHER
#############################################################
def create_plancher(self,context):
	context.preferences.edit.use_global_undo = False
	obj_mode = context.active_object.mode
	bpy.ops.object.mode_set(mode='OBJECT')
	context.scene.unit_settings.system = 'METRIC'
	cobj = context.object
	verts, faces = parquet(cobj.Plancher.lock_length,
						   cobj.Plancher.nbrboards,
						   cobj.Plancher.nbr_length,
						   cobj.Plancher.height,
						   cobj.Plancher.randheight,
						   cobj.Plancher.width,
						   cobj.Plancher.randwith,
						   cobj.Plancher.gapx,
						   cobj.Plancher.lengthboard,
						   cobj.Plancher.gapy,
						   cobj.Plancher.shifty,
						   cobj.Plancher.nbrshift,
						   cobj.Plancher.tilt,
						   cobj.Plancher.herringbone,
						   cobj.Plancher.randoshifty,
						   cobj.Plancher.floor_length,
						   cobj.Plancher.fill_gap_y,
						   cobj.Plancher.gaptrans,
						   cobj.Plancher.randgaptrans,
						   cobj.Plancher.glue,
						   cobj.Plancher.borders,
						   cobj.Plancher.lengthtrans,
						   cobj.Plancher.locktrans,
						   cobj.Plancher.nbrtrans,)

	# Code from Michel Anders script Floor Generator
	# Create mesh & link object to scene
	emesh = cobj.data

	mesh = bpy.data.meshes.new("Plancher_mesh")
	mesh.from_pydata(verts, [], faces)
	mesh.update(calc_edges=True)

	for i in bpy.data.objects:
		if i.data == emesh:
			i.data = mesh

	name = emesh.name
	emesh.user_clear()
	bpy.data.meshes.remove(emesh)
	mesh.name = name

	#---------------------------------------------------------------------COLOR & UV
	if obj_mode =='EDIT':                                                 # If we are in 'EDIT MODE'
		seed(cobj.Plancher.colseed)                                            # New random distribution
		# mesh.uv_textures.new("Txt_Plancher")                          # New UV map
		mesh.uv_layers.new(name="Txt_Plancher")                          # New UV map
		# cobj.data.uv_layers.new(name="Txt_Plancher")                    # New UV map
		vertex_colors = mesh.vertex_colors.new().data                 # New vertex color
		rgb = []

		if cobj.Plancher.colrand > 0:                                          # If random color
			for i in range(cobj.Plancher.colrand):
				color = [round(rand(),1), round(rand(),1), round(rand(),1), 1] # Create as many random color as in the colrand variable
				rgb.append(color)                                     # Keep all the colors in the RGB variable

		elif cobj.Plancher.colphase > 0:                                       # If phase color
			for n in range(cobj.Plancher.colphase):
				color = [round(rand(),1), round(rand(),1), round(rand(),1), 1] # Create as many random color as in the colphase variable
				rgb.append(color)                                     # Keep all the colors in the RGB variable

	#---------------------------------------------------------------------VERTEX GROUP
		bpy.context.object.vertex_groups.clear()                      # Clear vertex group if exist
		if cobj.Plancher.colrand == 0 and cobj.Plancher.colphase == 0:                  # Create the first Vertex Group
			bpy.context.object.vertex_groups.new()
		elif cobj.Plancher.colrand > 0:                                        # Create as many VG as random color
			for v in range(cobj.Plancher.colrand):
				bpy.context.object.vertex_groups.new()
		elif cobj.Plancher.colphase > 0:                                       # Create as many VG as phase color
			for v in range(cobj.Plancher.colphase):
				bpy.context.object.vertex_groups.new()

	#---------------------------------------------------------------------VERTEX COLOR
		phase = cobj.Plancher.colphase
		color = {}
		for poly in mesh.polygons:                                    # For each polygon of the mesh

			if cobj.Plancher.colrand == 0 and cobj.Plancher.colphase == 0:              # If no color
				color = [rand(), rand(), rand(), 1]                      # Create at least one random color

			elif cobj.Plancher.colrand > 0:                                    # If random color

				if cobj.Plancher.allrandom:                                    # If all random choose
					nbpoly = len(mesh.polygons.items())               # Number of boards
					randvg = randint(0,cobj.Plancher.colrand)                  # Random vertex group
					for i in range(nbpoly):
						color = [round(rand(),1), round(rand(),1), round(rand(), 1), 1]     # Create as many random color as in the colrand variable
						rgb.append(color)                             # Keep all the colors in the RGB variable

				else:
					color = rgb[randint(0,cobj.Plancher.colrand-1)]            # Take one color ramdomly from the RGB list


				for loop_index in poly.loop_indices:                  # For each vertice from this polygon
					vertex_colors[loop_index].color = color           # Assign the same color
					if cobj.Plancher.allrandom:                                # If all random choose
						vg = bpy.context.object.vertex_groups[randvg-1] # Assign a random vertex group
					else:
						vg = bpy.context.object.vertex_groups[rgb.index(color)] # Else assign a vertex group by color index
					vg.add([loop_index], 1, "ADD")                    # index, weight, operation

			elif cobj.Plancher.colphase > 0:                                   # If phase color
				color = rgb[phase-1]                                  # Take the last color from the RGB list
				phase -= 1                                            # Substract 1 from the phase number
				if phase == 0: phase = cobj.Plancher.colphase                  # When phase = 0, start again from the beginning to loop in the rgb list

				for loop_index in poly.loop_indices:                  # For each vertice from this polygon
					vertex_colors[loop_index].color = color           # Assign the same color
					vg = bpy.context.object.vertex_groups[rgb.index(color)]
					vg.add([loop_index], 1, "ADD")                    # index, weight, operation
		color.clear()                                                 # Clear the color list


		#-----------------------------------------------------------------UV UNWRAP
		ob = bpy.context.object
		ob.select_set(True)
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.uv.unwrap(method='ANGLE_BASED', correct_aspect=True)
		#-----------------------------------------------------------------UV LAYER
		me = ob.data
		bm = bmesh.from_edit_mesh(me)
		uv_lay = bm.loops.layers.uv.verify()

		#-----------------------------------------------------------------GROUP UV
		# Group all the UV points at the origin point
		# Need more work, it's not working everytimes, don't know why...
		v = 0
		tpuvx = {}
		tpuvy = {}
		for face in bm.faces:                                             # For each polygon
			for loop in face.loops:                                       # For each loop
				luv = loop[uv_lay]
				v += 1
				uv = loop[uv_lay].uv                                      # Keep the coordinate of the uv point
				tpuvx[uv.x] = loop.index                                  # Keep the X coordinate of the uv point
				tpuvy[uv.y] = loop.index                                  # Keep the Y coordinate of the uv point

				if v > 3:                                                 # When the last uv point of this polygon is reached
					minx = min(tpuvx.keys())                              # Keep the smallest value on the X axis from the 4 uv point
					miny = min(tpuvy.keys())                              # Keep the smallest value on the Y axis from the 4 uv point
					for loop in face.loops:                               # A new loop in the loop ... really need more work
						loop[uv_lay].uv[0] -= minx                        # For each UV point, substract the value of the smallest X
						loop[uv_lay].uv[1] -= miny                        # For each UV point, substract the value of the smallest Y
					v = 0                                                 # Initialize counter
			tpuvx.clear()                                                 # Clear the list
			tpuvy.clear()                                                 # Clear the list

		bmesh.update_edit_mesh(me)                                        # Update the mesh

	else:
		bpy.ops.object.mode_set(mode='OBJECT')                            # We are in 'OBJECT MODE' here, nothing to do

	#---------------------------------------------------------------------MODIFIERS
	nbop = len(cobj.modifiers)
	obj = context.active_object
	if nbop == 0:
		obj.modifiers.new('Solidify', 'SOLIDIFY')
		obj.modifiers.new('Bevel', 'BEVEL')
	cobj.modifiers['Solidify'].show_expanded = False
	cobj.modifiers['Solidify'].thickness = self.height
	cobj.modifiers['Bevel'].show_expanded = False
	cobj.modifiers['Bevel'].width = 0.001
	cobj.modifiers['Bevel'].use_clamp_overlap

	bpy.context.preferences.edit.use_global_undo = True

# -------------------------------------------------------------------- #
## Properties
class Plancher_prop(bpy.types.PropertyGroup):
#---List of environment options
	floor_type : EnumProperty(name="Type",
								description="Type:\n"+
								"\u2022 Sky texture: Use the internal sky texture for background\n"+
								"\u2022 Image texture: Use HDRI for background\n"+
								"Selected",
								items = {
										("Herringbone", "Herringbone", "Herringbone", 0),
										("Tiles", "Tiles", "Tiles", 1),
										("Squares", "Squares", "Squares", 2),
										("Chevron", "Chevron", "Chevron", 3),
										("Ladder", "Ladder", "Ladder", 4),
										("Fougere", "Fougere", "Fougere", 5),
										("Stack Bond", "Stack Bond", "Stack Bond", 6),
										},
								default = "Stack Bond",
								update=update_type,
								)

#---Switch between length of the board and meters
	lock_length : BoolProperty(
			   name="Lock length",
			   description="Lock the length of the surface to a number of boards",
			   default=False,
			   get=get_lock_length,
			   set=set_lock_length,
			   update=create_plancher)

#---Length of the floor
	floor_length : FloatProperty(
			   name="Length",
			   description="Length of the floor",
			   min=0.01, max=10000000.0,
			   default=4.0,
			   precision=2,
			   subtype='DISTANCE',
			   update=create_plancher)

#---Number of column
	nbr_length : IntProperty(
			name="Count",
			description="Number of columns",
			min=1, max=100,
			default=1,
			get=get_nbr_length,
			set=set_nbr_length,
			update=create_plancher)

#---Number of row
	nbrboards : IntProperty(
			name="Count",
			description="Number of rows",
			min=1, max=100,
			default=2,
			update=create_plancher)

#---Length of a board after tilt
	length_y : FloatProperty(
			   name="Length",
			   description="Length of a board after tilt",
			   min=0.01, max=1000000000.0,
			   default=2.0,
			   precision=2,
			   subtype='DISTANCE',
			   )

#---Length of a board
	lengthboard : FloatProperty(
			   name="Length",
			   description="Length of a board",
			   min=0.01, max=1000000000.0,
			   default=2.0,
			   precision=2,
			   subtype='DISTANCE',
			   update=create_plancher)

#---Height of the floor
	height : FloatProperty(
			  name="Height",
			  description="Height of the floor",
			  min=0.01, max=100,
			  default=0.01,
			  precision=2,
			  subtype='DISTANCE',
			  update=create_plancher)

#---Add random to the height
	randheight : FloatProperty(
			   name="Random",
			   description="Add random to the height",
			   min=0, max=1,
			   default=0,
			   precision=2,
			   subtype='PERCENTAGE',
			   unit='NONE',
			   step=0.1,
			   update=create_plancher)
#---Width of a board
	width : FloatProperty(
			  name="Width",
			  description="Width of a board",
			  min=0.01, max=100.0,
			  default=0.18,
			  precision=3,
			  subtype='DISTANCE',
			  update=create_plancher)

#---Add random to the width
	randwith : FloatProperty(
			   name="Random",
			   description="Add random to the width",
			   min=0, max=1,
			   default=0,
			   precision=2,
			   subtype='PERCENTAGE',
			   unit='NONE',
			   step=0.1,
			   update=create_plancher)

#---Add a gap between the columns (X)
	gapx : FloatProperty(
			  name="Gap X",
			  description="Add a gap between the columns (X)",
			  min=0.00, max=100.0,
			  default=0.01,
			  precision=2,
			  subtype='DISTANCE',
			  update=create_plancher)

#---Add a gap between the row (Y) (for the transversal's boards)
	gapy : FloatProperty(
			  name="Gap Y",
			  description="Add a gap between the row (Y)",
			  min=0.00, max=100.0,
			  default=0.01,
			  precision=2,
			  subtype='DISTANCE',
			  update=create_plancher)

#---Shift the columns
	shifty : FloatProperty(
			   name="Shift",
			   description="Shift the columns",
			   min=0, max=1,
			   default=0,
			   precision=2,
			   step=0.1,
			   update=create_plancher)

#---Add random to the shift
	randoshifty : FloatProperty(
			   name="Random",
			   description="Add random to the shift",
			   min=0, max=1,
			   default=0,
			   precision=2,
			   subtype='PERCENTAGE',
			   unit='NONE',
			   step=0.1,
			   update=create_plancher)

#---Number of column to shift
	nbrshift : IntProperty(
			name="Nbr Shift",
			description="Number of column to shift",
			min=1, max=100,
			default=1,
			update=create_plancher)

#---Fill in the gap between the row (transversal)
	fill_gap_y : BoolProperty(
			   name=" ",
			   description="Fill in the gap between the row",
			   default=False,
			   update=create_plancher)

#---Unlock the length of the transversal
	locktrans : BoolProperty(
			   name="Unlock",
			   description="Unlock the length of the transversal",
			   default=False,
			   update=create_plancher)

#---Length of the transversal
	lengthtrans : FloatProperty(
			  name="Length",
			  description="Length of the transversal",
			  min=0.01, max=100,
			  default=2,
			  precision=2,
			  subtype='DISTANCE',
			  update=create_plancher)

#---Number of transversals in the interval
	nbrtrans : IntProperty(
			name="Count X",
			description="Number of transversals in the interval",
			min=1, max=100,
			default=1,
			update=create_plancher)

#---Gap between the transversals
	gaptrans : FloatProperty(
			  name="Gap",
			  description="Gap between the transversals",
			  min=0.00, max=100,
			  default=0.01,
			  precision=2,
			  subtype='DISTANCE',
			  update=create_plancher)

#---Add random to the width
	randgaptrans : FloatProperty(
			   name="Random",
			   description="Add random to the gap of the transversal",
			   min=0, max=1,
			   default=0,
			   precision=2,
			   subtype='PERCENTAGE',
			   unit='NONE',
			   step=0.1,
			   update=create_plancher)

#---Glue the boards in the shift parameter
	glue : BoolProperty(
			   name="glue",
			   description="Glue the boards in the shift parameter",
			   default=False,
			   update=create_plancher)

#---Add borders
	borders : BoolProperty(
			   name="Borders",
			   description="Add borders between the glued boards",
			   default=False,
			   update=create_plancher)

#---Tilt the columns
	tilt : FloatProperty(
			   name="Tilt",
			   description="Tilt the columns",
			   min= math.radians(0), max= math.radians(70),
			   default=0.00,
			   precision=2,
			   subtype='ANGLE',
			   unit='ROTATION',
			   step=1,
			   update=create_plancher)

#---Floor type Herringbone
	herringbone : BoolProperty(
			   name="Herringbone",
			   description="Floor type Herringbone",
			   default=False,
			   get=get_herringbone,
			   set=set_herringbone,
			   update=create_plancher)

#---Random color to the vertex group
	colrand : IntProperty(
			   name="Random Color",
			   description="Random color to the vertex group",
			   min=0, max=100,
			   default=0,
			   update=create_plancher)

#---Orderly color to the vertex group
	colphase : IntProperty(
			   name="Phase color",
			   description="Orderly color to the vertex group",
			   min=0, max=100,
			   default=0,
			   update=create_plancher)

#---New distribution for the random
	colseed : IntProperty(
			   name="Seed",
			   description="New distribution for the random",
			   min=0, max=999999,
			   default=0,
			   update=create_plancher)

#---Random color for each board
	allrandom : BoolProperty(
			   name="allrandom",
			   description="Make a random color for each board",
			   default=False,
			   update=create_plancher)

class PLANCHER_OT_AddObject(bpy.types.Operator):
	bl_idname = "plancher.add_object"
	bl_label = "Add a new floor"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		bpy.ops.mesh.primitive_cube_add()
		context.active_object.name = "Plancher"
		cobj = context.object
		cobj.Plancher.nbrboards = 2
		return {'FINISHED'}


# -------------------------------------------------------------------- #
## Register

classes = (
	MAIN_PT_Plancher,
	PLANCHER_OT_AddObject,
	Plancher_prop,
	)

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)
	bpy.types.Object.Plancher = bpy.props.PointerProperty(type=Plancher_prop)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	del bpy.types.Object.Plancher
