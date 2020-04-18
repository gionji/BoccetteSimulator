# Check this link:
# https://stackoverflow.com/questions/2477774/correcting-fisheye-distortion-programmatically#answers

import numpy as np
import mathutils

def numpy_to_blender(x, y, image_height):
    """
    """
    return y, abs((image_height - 1) - x)


def blender_to_numpy(x, y, image_height):
    """
    """
    return abs((image_height - 1) - y), x


def convert_coordinates(coords, new_origin):
    """
    Map 3D coordinates into a different coordinate system.

    Map 3D coordinates, given by `coords`, in a new coordinate system 
    where `new_origin` is the origin of axes. 
    """

    return coords - new_origin


def world_to_camera_view_with_projection(
    camera_sensor_width, 
    camera_sensor_height, 
    lens_focal_length, 
    camera_obj, 
    coords,
    projection=lambda f, theta: f * np.tan(theta)
):
    """
    Map 3D world coordinates to 2D pixel coordinates of a camera view.

    Map 3D world coordinates (given by `coords`) of any point to its 
    corresponding 2D pixel coordinates in an image that represents the 
    camera view. The argument `projection` is a function that takes the  
    camera's focal length, `f`, and `theta`, which is the angle that the 
    point forms with the optical axis, and returns the projection of the 
    point in the camera view. The default value performs a rectilinear 
    (a.k.a. perspective) projection.
    """

    # Convert `coords` from world space (i.e. relative to the origin of
    # axes) to camera space (i.e. relative to the camera location)
    coords_camera_space = camera_obj.matrix_world.inverted() @ coords
    
    # # Normalize the vector to unit length
    # coords_camera_space.normalize()

    # Calculate projection parameters
    #  - ɸ (phi) is the angle that the projection of `coords_camera_space` 
    #    onto the xy-plane of the camera's coordinate system forms with 
    #    the x-axis
    #  - ℓ (l) is the length of the projection of `coords_camera_space` 
    #    onto the xy-plane of the camera's coordinate system
    #  - θ (theta) is the angle that `coords_camera_space` forms with 
    #    the optical axis of the camera, which is nothing but the z-axis
    phi = np.arctan2(coords_camera_space.y, coords_camera_space.x)
    l = np.sqrt(coords_camera_space.x**2 + coords_camera_space.y**2)
    l_normalized = l / coords_camera_space.length
    theta = np.arcsin(l_normalized)

    # Calculate the distance at which the point will lie from the center
    # of the image, using the specified projection
    r = projection(lens_focal_length, theta)

    # Go from polar to cartesian coordinates. The addition of 0.5 to 
    # each coordinates moves it from the [-0.5, 0.5] range (relative to 
    # the center of the image) to the [0, 1] range (relative to the 
    # bottom left corner of the image)
    x = (r * np.cos(phi) / camera_sensor_width) + 0.5
    y = (r * np.sin(phi) / camera_sensor_height) + 0.5

    return x, y


def fisheye_equisolid_to_camera_view_with_projection(
    camera_sensor_width, 
    camera_sensor_height, 
    lens_focal_length,
    coords,
    projection=lambda f, theta: f * np.tan(theta)
):

    x, y = coords.x, coords.y
    x_cartesian = (x - 0.5) * camera_sensor_width
    y_cartesian = (y - 0.5) * camera_sensor_height
    
    # Go from cartesian to polar coordinates
    r_fish = np.sqrt(x_cartesian**2 + y_cartesian**2)
    phi = np.arctan2(y_cartesian, x_cartesian)

    # Given r_fish, which is the distance of the point from the center 
    # of the image with fisheye equisolid distortion, compute r_new, 
    # that is the distance of the point from the center of the image 
    # with the type of distortion determined by projection
    theta = 2 * np.arcsin(r_fish / (2 * lens_focal_length))
    r_new = projection(lens_focal_length, theta)
    
    x_camera_space = (r_new * np.cos(phi) / camera_sensor_width) + 0.5
    y_camera_space = (r_new * np.sin(phi) / camera_sensor_height) + 0.5

    return x_camera_space, y_camera_space