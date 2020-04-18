import itertools

import numpy as np
import bpy

import coordinates_utils as cu

def get_vertex_coordinates_in_rendered_image(
    obj, 
    camera_obj,
    camera_sensor_width, 
    camera_sensor_height,
    lens_focal_length,
    render_width,
    render_height,
    projection
):
    """
    Given an object `obj` in a 3D scene, get pixel coordinates of each 
    of its vertices in the rendered image.
    """

    vertex_coordinates = []
    for vertex in obj.data.vertices:

        # Get vertex coordinates in world space
        vertex_coords = obj.matrix_world @ vertex.co

        # Get vertex coordinates in camera space. Each coordinate will 
        # be in the [0, 1] range, provided that the 3D point is within 
        # the camera's scope
        vertex_camera_view_coords = cu.world_to_camera_view_with_projection(
            camera_sensor_width, 
            camera_sensor_height,
            lens_focal_length, 
            camera_obj,
            vertex_coords,
            projection
        )
        
        # Map the x-coordinate in the range [0, render_width]
        vertex_camera_view_x = int(vertex_camera_view_coords[0] * render_width)
        # Map the y-coordinate in the range [0, render_height]
        vertex_camera_view_y = int(vertex_camera_view_coords[1] * render_height)

        # Convert pixel coordinates from Blender format (where (0, 0) is
        # at the bottom left of the image) to NumPy format (where (0, 0)
        # is at the top left of the image)
        vertex_camera_view_x, vertex_camera_view_y = cu.blender_to_numpy(
            vertex_camera_view_x,
            vertex_camera_view_y,
            render_height
        )

        vertex_coordinates.append([
            vertex_camera_view_x,
            vertex_camera_view_y
        ])

    # Remove duplicates from the resulting array before returning it. 
    # This will be useful in case the object has lots of vertices. For 
    # example, spheres in Blender can have over 5000 vertices, so it is 
    # only natural for some of them to be mapped on the very same pixel
    vertex_coordinates = np.array(vertex_coordinates)
    vertex_coordinates = np.unique(vertex_coordinates, axis=0)

    return vertex_coordinates


def get_visible_pixel_mask_in_rendered_image(
    object_pass_index,
    render_width,
    render_height
):
    """
    Given an object's pass index, get the pixel mask of the visible 
    portion of such object in the rendered image. 

    NOTE: before calling this function, you must:
        1. Assign each object in the scene a unique pass index, which 
           you can set in 'Object Properties' / 'Relations'.
        2. Enable the passing of object index in 'View Layer Properties'
           by checking the 'Object Index' checkbox.
        3. Go to the 'Compositing' workspace and make sure to have a 
           'Render Layers' and a 'Viewer' node. Connect the 'IndexOB' 
           output of the 'Render Layers' node to the 'Image' input of 
           the 'Viewer' node.
        4. Render the scene (either programmatically or via the GUI).
    """

    pixels = np.array(bpy.data.images['Viewer Node'].pixels[:]).reshape([
        render_height, 
        render_width, 
        4  # RGBA, that is
    ])

    # Keep only one value for each pixel (white pixels have 1 in all 
    # RGBA channels anyway), thus converting the image to black and 
    # white
    pixels = pixels[:, :, 0]
    
    pixel_mask = np.argwhere(pixels == object_pass_index)
    # TODO: capire perché c'è bisogno di questa istruzione
    pixel_mask[:, 0] = render_height - pixel_mask[:, 0]

    return pixel_mask


def get_visible_outline_in_rendered_image(
    object_pass_index,
    render_width,
    render_height
):
    """
    Given an object's pass index, get the pixel coordinates of the 
    visible portion of such object's outline in the rendered image.

    NOTE: before calling this function, you must:
        1. Assign each object in the scene a unique pass index, which 
           you can set in 'Object Properties' / 'Relations'.
        2. Enable the passing of object index in 'View Layer Properties'
           by checking the 'Object Index' checkbox.
        3. Go to the 'Compositing' workspace and make sure to have a 
           'Render Layers' and a 'Viewer' node. Connect the 'IndexOB' 
           output of the 'Render Layers' node to the 'Image' input of 
           the 'Viewer' node.
        4. Render the scene (either programmatically or via the GUI).   
    """

    pixels = np.array(bpy.data.images['Viewer Node'].pixels[:]).reshape([
        render_height, 
        render_width, 
        4  # RGBA, that is
    ])

    # Keep only one value for each pixel (white pixels have 1 in all 
    # RGBA channels anyway), thus converting the image to black and 
    # white
    pixels = pixels[:, :, 0]

    pixels_copy = np.zeros_like(pixels)

    indexes = itertools.product(
        range(1, render_height - 1), 
        range(1, render_width - 1)
    )
    for row, col in indexes:

        val = pixels[row, col]

        if pixels[row, col-1] != val or \
           pixels[row-1, col] != val or \
           pixels[row, col+1] != val or \
           pixels[row+1, col] != val:
            
            # The pixel is part of the outline of an object, so we keep 
            # it
            pixels_copy[row, col] = val        

    outline = np.argwhere(pixels_copy == object_pass_index)
    outline[:, 0] = render_height - outline[:, 0]

    return outline