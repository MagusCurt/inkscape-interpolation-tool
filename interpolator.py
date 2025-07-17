#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2025 MagusCurt, maguscurt@protonmail.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
This extension allows interpolation of the rotate and axis transformation of a selected object
"""

import inkex

class Interpolator(inkex.EffectExtension):
    def add_arguments(self, pars):
        #Amount of iterations to perform
        pars.add_argument("--steps", type=int, default=1)

        #Transformation options (rotation in degrees)
        pars.add_argument("--rotation", type=int, default=90)
        pars.add_argument("--change_x", type=float, default=0.0)
        pars.add_argument("--change_y", type=float, default=0.0)
        pars.add_argument("--rotation_center_x", type=float, default=0.0)
        pars.add_argument("--rotation_center_y", type=float, default=0.0)

        #If the user wants to use another object as the basis for the transformation
        #   these variabes are used instead of the ones above
        pars.add_argument("--axis_selection", type=inkex.Boolean, default=False)
        pars.add_argument("--center_point_selection", type=inkex.Boolean, default=False)


    def effect(self):
        # Note: It seems shape strokes are not included in the size calculation
        #       This messes up the calculations for the center of the element

        # Get the frame of the selected element
        selected_frame = self.svg.selection[0]
        #Grab and create a new element based on the first selected element
        selected_elem = self.svg.selection[1]

        # Initialize variables for axis and center point selections
        # If the user has selected an axis or center point, these variables will be set to
        selected_axis = None
        selected_center_point = None

        # Check if axis and center point selections are used
        # If both are used, the 3rd selection is the axis and the 4th selection is the center point
        # If only one is used, the 3rd selection is the respective option
        if self.options.axis_selection and self.options.center_point_selection:
            selected_axis = self.svg.selection[2]
            selected_center_point = self.svg.selection[3]
        elif self.options.axis_selection:
            selected_axis = self.svg.selection[2]
        elif self.options.center_point_selection:
            selected_center_point = self.svg.selection[2]

        #Recreates the original element so that the original is technically not modified
        selected_elem.duplicate()

        # Get the bounding box of the selected element and frame for later calculations
        frame_bbox = selected_frame.bounding_box()
        elem_bbox = selected_elem.bounding_box()


        # if the user decided to use an object as the center point for the rotation
        if selected_center_point is not None:
            point_bbox = selected_center_point.bounding_box()
            elem_center_x = point_bbox.x.minimum + (point_bbox.width / 2)
            elem_center_x += self.options.rotation_center_x

            elem_center_y = point_bbox.y.minimum + (point_bbox.height / 2)
            elem_center_y += self.options.rotation_center_y
        else:
            elem_center_x = elem_bbox.x.minimum + (elem_bbox.width / 2)
            elem_center_x += self.options.rotation_center_x

            elem_center_y = elem_bbox.y.minimum + (elem_bbox.height / 2)
            elem_center_y += self.options.rotation_center_y

        # If the user decided to use an object as the axis for x-y translation
        if selected_axis is not None:
            # Get the bounding box of the selected axis for later calculations
            axis_bbox = selected_axis.bounding_box()
            # Calculate the center of the axis
            axis_center_x = axis_bbox.x.minimum + (axis_bbox.width / 2)
            axis_center_y = axis_bbox.y.minimum + (axis_bbox.height / 2)

            steps_length_x = (axis_center_x - elem_center_x) / self.options.steps
            steps_length_y = (axis_center_y - elem_center_y) / self.options.steps
        else:
            # The distance to move the element in each step
            steps_length_x = self.options.change_x / self.options.steps
            steps_length_y = self.options.change_y / self.options.steps

        for i in range(1, self.options.steps + 1):

            if i > 1: #No need to duplicate the element for the first step
                # Duplicate the selected element for each step
                selected_elem.duplicate()

            group = inkex.Group()
            self.svg.add(group)
            group.append(selected_elem)

            # Create a pad perfect square to encase the element in a perfect square
            # This is used to ensure the element is centered and rotated correctly
            pad_rect = inkex.Rectangle()
            if elem_bbox.width > elem_bbox.height:
                pad_rect.set('width', str(elem_bbox.width))
                pad_rect.set('height', str(elem_bbox.width))
            else:
                pad_rect.set('width', str(elem_bbox.height))
                pad_rect.set('height', str(elem_bbox.height))

            pad_rect.set('x', str(elem_bbox.x.minimum - (pad_rect.width - elem_bbox.width) / 2))
            pad_rect.set('y', str(elem_bbox.y.minimum - (pad_rect.height - elem_bbox.height) / 2))
            pad_rect.style = {'fill': 'none', 'stroke': 'none'}

            group.insert(0, pad_rect)

            # Set the degree of rotation for each step
            step_degrees = (self.options.rotation / self.options.steps) * i

            # Perform the rotation transformation
            translation_string = f'rotate({step_degrees}, {elem_center_x}, {elem_center_y})'# translate({(frame_bbox.width * i) + (steps_length_x * i)}, {steps_length_y})'

            group.transform = translation_string

            # Create a second pad perfect square to rotate the selection
            rotated_group = inkex.Group()
            self.svg.add(rotated_group)
            rotated_group.append(group)

            rotated_elem_bbox = group.bounding_box()
            rotated_pad_rect = inkex.Rectangle()
            if rotated_elem_bbox.width > rotated_elem_bbox.height:
                rotated_pad_rect.set('width', str(rotated_elem_bbox.width))
                rotated_pad_rect.set('height', str(rotated_elem_bbox.width))
            else:
                rotated_pad_rect.set('width', str(rotated_elem_bbox.height))
                rotated_pad_rect.set('height', str(rotated_elem_bbox.height))

            rotated_pad_rect.style = {'fill': 'none', 'stroke': 'none'}

            rotated_group.insert(0, rotated_pad_rect)

            rotated_group.transform = f'translate({(frame_bbox.width * i) + (steps_length_x * i)}, {steps_length_y * i})'

            # Code below removes the padding squares, so the user just have their original element

            rotated_group.remove(group)
            group.transform = rotated_group.transform @ group.transform
            self.svg.append(group)

            group.remove(selected_elem)
            selected_elem.transform = group.transform
            self.svg.append(selected_elem)



if __name__ == '__main__':
    Interpolator().run()