#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2016 Alexei Kireev

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

"""
### Installation

 - Copy **gimp_megadrive_generate_all_colors.py** to your Gimp plugins folder. To find out
 its location, run Gimp and go to ``Edit > Preferences > Folders > Plug-ins``

 - (Skip if you're using Windows) Change file permissions by adding executable bit: ``chmod +x gimp_megadrive_generate_all_colors.py``

 - Restart Gimp

### Use

 - Go to File > Create > Megadrive Colors...;

 - Pick background color;

 - Pick color sample size, your image size depends on it. Might be a good idea to choose 1;

 - Click "Ok";

 - Done.
"""

import struct
from gimpfu import *


def generate_image(background_color, sample_size):
    sample_size = int(sample_size)

    img_width = int(8 * 8 * sample_size + math.ceil(1.5 * sample_size) + 7 * math.ceil(sample_size * 2.5))
    img_height = int(8 * 3 * sample_size + math.ceil(1.5 * sample_size) + 2 * math.ceil(sample_size * 3.5) + 7 * sample_size)
    # print "img_width =", img_width, "img_height =", img_height
    img = gimp.Image(img_width, img_height, RGB)

    img.disable_undo()

    pdb.gimp_context_push()  # Save current foreground color
    gimp.set_background(background_color)

    layer = gimp.Layer(img, "Megadrive/Genesis colors", img_width, img_height,
                            RGB_IMAGE, 100, NORMAL_MODE)
    layer.fill(BACKGROUND_FILL)
    img.add_layer(layer, 0)
    pdb.gimp_edit_fill(layer, BACKGROUND_FILL)

    rgn = layer.get_pixel_rgn(0, 0, img_width, img_height)
    start_y = 0
    row_height = int(round(3.5 * sample_size + 8 * sample_size))
    paint_map("R", "G", 0, start_y, sample_size, rgn, 0, 4)
    start_y += row_height
    paint_map("G", "B", 0, start_y, sample_size, rgn, 1, 4)
    start_y += row_height
    paint_map("R", "B", 0, start_y, sample_size, rgn, 2, 4)
    start_y += row_height
    paint_additional_gradients(0, start_y, sample_size, 3, 4, rgn)

    img.enable_undo()

    gimp.Display(img)  # Create a new window for our image
    gimp.displays_flush()  # Show the new window

    pdb.gimp_context_pop()  # Restore old background color


def paint_map(x_color_type, y_color_type, start_x, start_y, sample_size, rgn, this_map_idx, total_maps_count):
    """x_color_type and y_color_type are two uppercase characters representing X axis color and Y axis color, respectively"""
    x = start_x
    for third_color in xrange(0, 8):
        paint_color_slice(x_color_type, y_color_type, third_color, x, start_y, sample_size, rgn)
        x += int(round(8 * sample_size + 2.5 * sample_size))
        prgrs = 1.0 / total_maps_count * this_map_idx + ((1.0 / total_maps_count) * (third_color + 1.0)) / 8.0
        gimp.progress_update(prgrs)


def paint_color_slice(x_color_type, y_color_type, z_color_val, start_x, start_y, sample_size, rgn):
    """x_color_type and y_color_type are two uppercase characters representing X axis color and Y axis color, respectively"""
    r = g = b = 0
    if "R" not in (x_color_type, y_color_type):
        r = z_color_val
    elif "G" not in (x_color_type, y_color_type):
        g = z_color_val
    else:
        b = z_color_val
    paint_rect(rgn, start_x, start_y, sample_size, sample_size, r, g, b)

    # X axis
    r = g = b = 0
    x = start_x + int(round(1.5 * sample_size))
    for sega_x_color in xrange(0, 8):
        if x_color_type == "R":
            r = sega_x_color
        elif x_color_type == "G":
            g = sega_x_color
        else:
            b = sega_x_color
        paint_rect(rgn, x, start_y, sample_size, sample_size, r, g, b)
        x += sample_size

    # Y axis
    r = g = b = 0
    y = start_y + int(round(1.5 * sample_size))
    for sega_y_color in xrange(0, 8):
        if y_color_type == "R":
            r = sega_y_color
        elif y_color_type == "G":
            g = sega_y_color
        else:
            b = sega_y_color
        paint_rect(rgn, start_x, y, sample_size, sample_size, r, g, b)
        y += sample_size

    y = start_y + int(round(sample_size * 1.5))
    r = g = b = z_color_val
    for sega_y_color in xrange(0, 8):
        x = start_x + int(round(sample_size * 1.5))
        if y_color_type == "R":
            r = sega_y_color
        elif y_color_type == "G":
            g = sega_y_color
        else:  # "B", supposedly
            b = sega_y_color
        for sega_x_color in xrange(0, 8):
            if x_color_type == "R":
                r = sega_x_color
            elif x_color_type == "G":
                g = sega_x_color
            else:  # "B", supposedly
                b = sega_x_color
            paint_rect(rgn, x, y, sample_size, sample_size, r, g, b)
            x += sample_size
        y += sample_size


def paint_additional_gradients(start_x, start_y, sample_size, this_map_idx, total_maps_count, rgn):
    double_size = sample_size * 2
    # Grays
    x = start_x
    for col in xrange(0, 8):
        paint_rect(rgn, x, start_y, double_size, double_size, col, col, col)
        x += double_size
    x += double_size

    # Reds
    for col in xrange(0, 8):
        paint_rect(rgn, x, start_y, double_size, double_size, col, 0, 0)
        x += double_size
    x += double_size

    # Greens
    for col in xrange(0, 8):
        paint_rect(rgn, x, start_y, double_size, double_size, 0, col, 0)
        x += double_size
    x += double_size

    # Blues
    for col in xrange(0, 8):
        paint_rect(rgn, x, start_y, double_size, double_size, 0, 0, col)
        x += double_size

    # Cyans
    x = start_x
    y = start_y + 3 * sample_size
    for col in xrange(0, 8):
        paint_rect(rgn, x, y, double_size, double_size, 0, col, col)
        x += double_size
    x += double_size

    # Magentas
    for col in xrange(0, 8):
        paint_rect(rgn, x, y, double_size, double_size, col, 0, col)
        x += double_size
    x += double_size

    # Yellows
    for col in xrange(0, 8):
        paint_rect(rgn, x, y, double_size, double_size, col, col, 0)
        x += double_size

    prgrs = 1.0 * (this_map_idx + 1.0) / total_maps_count
    gimp.progress_update(prgrs)


def paint_rect(rgn, x, y, w, h, sega_r, sega_g, sega_b):
    #print "x =", x, "y =", y, "r =", sega_r, "g = ", sega_g, "b =", sega_b
    r = sega_to_rgb(sega_r)
    g = sega_to_rgb(sega_g)
    b = sega_to_rgb(sega_b)
    colors = struct.pack("BBB", r, g, b) * w * h
    rgn[x:(x + w), y:(y + h)] = colors
    # - is SO much faster than -
    #for curr_y in xrange(y, y + h):
    #    for curr_x in xrange(x, x + w):
    #        rgn[curr_x, curr_y] = color
    # (where color = struct.pack("BBB", r, g, b))


def sega_to_rgb(col_elem):
    return int(round(float(col_elem) / 7.0 * 255.0))


register("megadrive-generate-all-colors",
         "Create a map of Sega Genesis/Megadrive colors.\r\n"
         "Each row will contain all 512 colors (with RGB-marked axes).\r\n"
         "In addition, below that you'll find grays, reds, greens, blues, "
         "also cyans, magentas and yellows.",
         "This script generates a new image showing all Sega Genesis/Megadrive colors",
         "Alexei Kireev",
         "Copyright 2016 Alexei Kireev",
         "2016-10-08",
         "Megadrive colors...",
         "",  # No open image is required for us to run
         [
             (PF_COLOR, "background_color", "Background color", (255, 255, 255)),
             (PF_SLIDER, "sample_size", "Color sample size", 4, (1, 40, 1)),
         ],
         [],
         generate_image,
         menu="<Image>/File/Create")


main()
