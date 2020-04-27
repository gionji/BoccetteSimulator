from pathlib import Path
import argparse
import sys

import numpy as np
import bpy

scripts_folder = Path(__file__).parent
sys.path.insert(0, str(scripts_folder))
import segmentation_utils as su
import coordinates_utils as cu
import lens_projections as lp

this_script_name = Path(__file__).stem
parser = argparse.ArgumentParser(this_script_name)
parser.add_argument(
    '-rw', '--render-width', 
    type=int, 
    default=2048
)
parser.add_argument(
    '-rh', '--render-height', 
    type=int, 
    default=1536
)
parser.add_argument(
    '-rs', '--render-samples', 
    type=int, 
    default=64
)
parser.add_argument(
    '-cn', '--camera-name', 
    type=str, 
    default='Camera'
)
parser.add_argument(
    '-csw', '--camera-sensor-width', 
    type=float, 
    default=18.0
)
parser.add_argument(
    '-csh', '--camera-sensor-height', 
    type=float, 
    default=13.5
)
parser.add_argument(
    '-f', '--lens-focal-length', 
    type=float, 
    default=8.90999984741211
)
parser.add_argument(
    '-p', '--lens-projection', 
    choices=[
        'rectilinear',
        'fisheye_equisolid',
        'fisheye_equidistant'
    ],
    default='fisheye_equisolid'
)
parser.add_argument(
    '-c', '--collections', 
    nargs='+', 
    default=['Balls']
)
parser.add_argument(
    '-cid', '--category-ids', 
    nargs='+', 
    type=int,
    default=[0]
)
parser.add_argument(
    '-cs', '--reference-coordinate-system', 
    type=str, 
    default=None
)
parser.add_argument(
    '-nm', '--no-masks', 
    action='store_true', 
    default=False
)
parser.add_argument(
    '-no', '--no-outlines', 
    action='store_true', 
    default=False
)
parser.add_argument(
    '-i', '--individual-renders', 
    action='store_true', 
    default=False
)
parser.add_argument(
    '-v', '--vertex-coordinates', 
    action='store_true', 
    default=False
)
parser.add_argument(
    '-ro', '--render-output-path', 
    default=None
)
parser.add_argument(
    '-ao', '--annotations-output-dir', 
    default=str(Path.home() / 'annotations')
)

if '--' in sys.argv:
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
else:
    # Stick to default values for each parameter
    args = parser.parse_args([])

projections = {
    'rectilinear': lp.rectilinear,
    'fisheye_equisolid': lp.fisheye_equisolid,
    'fisheye_equidistant': lp.fisheye_equidistant 
}
projection = projections[args.lens_projection]

objects = []
for collection_name, category_id in zip(args.collections, args.category_ids):
    objects.extend([
        (obj, category_id) for obj in bpy.data.collections[collection_name].all_objects[:]
    ])

scene = bpy.context.scene

# Set rendering settings
scene.render.engine = 'CYCLES'
scene.render.resolution_x = args.render_width
scene.render.resolution_y = args.render_height
scene.render.resolution_percentage = 100
scene.render.tile_x = 128
scene.render.tile_y = 128
scene.cycles.samples = args.render_samples
scene.cycles.max_bounces = 1
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.view_layers['View Layer'].cycles.use_denoising = True

# Set GPU settings
scene.cycles.device = 'GPU'
preferences = bpy.context.preferences
cycles_preferences = preferences.addons['cycles'].preferences
cycles_preferences.compute_device_type = 'CUDA'
for device in cycles_preferences.get_devices_for_type('CUDA'):
    device.use = True

# Use nodes in compositing
scene.use_nodes = True

# Deliver objects' pass indexes to the rendering engine
scene.view_layers['View Layer'].use_pass_object_index = True

# Get access to the compositing tree
tree = bpy.data.scenes['Scene'].node_tree
nodes = tree.nodes
links = tree.links

# Create a new 'File Output' node for saving annotations to disk
file_output_node = nodes.new(type='CompositorNodeOutputFile')
file_output_node.base_path = args.annotations_output_dir
file_output_node.file_slots.remove(file_output_node.inputs[0])

def create_node_pipeline_for_object(
    obj, 
    nodes, 
    links, 
    file_output_node, 
    output_masks=True,
    output_outlines=True,
    filename_suffix='visible'
):
    """
    Given an object, create a pipeline made of compositing nodes for 
    extracting a pixel mask as well as an outline mask of the object in 
    the rendered image.
    """

    render_layers_node = nodes.get('Render Layers')

    id_mask_node = nodes.new(type='CompositorNodeIDMask')
    id_mask_node.index = obj.pass_index

    # Connect 'Render Layers' to 'ID Mask'
    links.new(
        render_layers_node.outputs.get('IndexOB'), 
        id_mask_node.inputs[0]
    )

    if output_masks:
        pixel_mask_input_socket_name = f'{obj.name}_mask_{filename_suffix}'
        file_output_node.file_slots.new(pixel_mask_input_socket_name)
        # Connect 'ID Mask' to 'File Output'
        links.new(
            id_mask_node.outputs[0], 
            file_output_node.inputs.get(pixel_mask_input_socket_name)
        )

    if output_outlines:
        # Create a new 'Laplace' node
        filter_node = nodes.new(type='CompositorNodeFilter')
        filter_node.filter_type = 'LAPLACE'

        # Connect 'ID Mask' to 'Laplace'
        links.new(
            id_mask_node.outputs[0], 
            filter_node.inputs.get('Image')
        )

        outline_input_socket_name = f'{obj.name}_outline_{filename_suffix}'
        file_output_node.file_slots.new(outline_input_socket_name)
        # Connect 'Laplace' to 'File Output'
        links.new(
            filter_node.outputs[0], 
            file_output_node.inputs.get(outline_input_socket_name)
        )
    else:
        filter_node = None

    return id_mask_node, filter_node

# Check if the user has requested to perform a separate render for each 
# object (this comes in handy when some objects are occluded by others)
if args.individual_renders:

    # Hide all objects
    for obj, _ in objects:
        obj.cycles_visibility.camera = False

    # We don't care about the quality of this render: all we care about 
    # is knowing which pixels in the render belong to a given object.  
    # Let's then set the number of render samples to be equal to 1 so 
    # that the rendering can be carried out as quickly as possible. 
    # Also, let's turn off denoising.
    original_rendering_samples = scene.cycles.samples
    scene.cycles.samples = 1
    scene.view_layers['View Layer'].cycles.use_denoising = False
    for obj, _ in objects:

        # Make this object (and only this one) visible
        obj.cycles_visibility.camera = True
        
        # Set up a node pipeline for `obj` that will output a pixel mask
        # as well as an outline of the object in the render (including 
        # any non-visible portions of it)
        id_mask_node, filter_node = create_node_pipeline_for_object(
            obj, 
            nodes, 
            links, 
            file_output_node, 
            not args.no_masks,
            not args.no_outlines,
            filename_suffix='complete'
        )

        # Render the scene (`obj` will be the only the visible object)
        bpy.ops.render.render(use_viewport=False, write_still=False)

        # Delete the previously created nodes
        nodes.remove(id_mask_node)
        if filter_node is not None:
            nodes.remove(filter_node)

        # Make the object invisible again
        obj.cycles_visibility.camera = False

    # Restore the original number of render samples and re-enable 
    # denoising
    scene.cycles.samples = original_rendering_samples
    scene.view_layers['View Layer'].cycles.use_denoising = True


for obj, _ in objects:
    
    obj.cycles_visibility.camera = True

    # Set up a node pipeline for `obj` that will output a pixel mask as 
    # well as an outline of the visible portion of the object in the 
    # render
    create_node_pipeline_for_object(
        obj, 
        nodes, 
        links, 
        file_output_node, 
        not args.no_masks,
        not args.no_outlines,        
        filename_suffix='visible'
    )

if args.render_output_path is not None:
    # Render the scene
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = args.render_output_path
    bpy.ops.render.render(use_viewport=False, write_still=True)

else:
    # The user doesn't want to perform a complete render, but only 
    # retrieve a pixel and/or an outline mask of the objects

    scene.cycles.samples = 1
    scene.view_layers['View Layer'].cycles.use_denoising = False
    bpy.ops.render.render(use_viewport=False, write_still=False)


if args.reference_coordinate_system is not None:
    # The user wants x and y coordinates of the objects to be relative 
    # to another object in the scene. For example, in the case of balls 
    # on a pool table, the user might want balls' coordinates relative 
    # to the table, so that they will be fixed regardless of the 
    # location of the table in the 3D scene.

    reference_coordinate_system = bpy.data.objects[
        args.reference_coordinate_system
    ]
    
    # Compute the coordinates of the top-left corner of the reference 
    # object (for example, the table)    
    top_left_corner_x = reference_coordinate_system.location.x          \
                        - reference_coordinate_system.dimensions.x / 2

    top_left_corner_y = reference_coordinate_system.location.y          \
                        + reference_coordinate_system.dimensions.y / 2

    top_left_corner = np.array([
        top_left_corner_x,
        top_left_corner_y
    ])

camera_obj = bpy.data.objects[args.camera_name]
for obj, category_id in objects:

    # Location of the object in the 3D scene
    location = np.array([
        obj.location.x,
        obj.location.y
    ])

    if args.reference_coordinate_system is not None:
        # Compute location relative to a given reference object
        location = cu.convert_coordinates(location, top_left_corner)
      
    # Make the y-coordinate grow downwards
    location[1] = -location[1]

    # Coordinates of `obj`'s vertices in the render
    vertex_coordinates = su.get_vertex_coordinates_in_rendered_image(
        obj, 
        camera_obj,
        args.camera_sensor_width, 
        args.camera_sensor_height,
        args.lens_focal_length,
        args.render_width,
        args.render_height,
        projection
    )

    # Bounding box of `obj` in the render
    min_row_index = np.min(vertex_coordinates[:, 0])
    max_row_index = np.max(vertex_coordinates[:, 0])
    min_col_index = np.min(vertex_coordinates[:, 1])
    max_col_index = np.max(vertex_coordinates[:, 1])

    bounding_box_width = max_col_index - min_col_index + 1
    bounding_box_height = max_row_index - min_row_index + 1

    # Save annotations to disk
    output_dir = Path(args.annotations_output_dir)
    np.savetxt(str(output_dir / f'{obj.name}_category_id'), np.array([category_id]))
    np.savetxt(str(output_dir / f'{obj.name}_location'), location)
    np.savetxt(str(output_dir / f'{obj.name}_bbox'), np.array([
        min_row_index,
        min_col_index,
        bounding_box_width,
        bounding_box_height
    ]))

    if args.vertex_coordinates:
        np.savetxt(
            str(output_dir / f'{obj.name}_vertices'), 
            vertex_coordinates
        )
