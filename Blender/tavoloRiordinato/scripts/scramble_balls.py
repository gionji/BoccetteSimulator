from pathlib import Path
import argparse
import random
import sys

import numpy as np
import bpy

parser = argparse.ArgumentParser()
parser.add_argument(
    '-o', '--output-path', 
    default=str(Path.home() / 'output.blend')
)

if '--' in sys.argv:
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
else:
    # Stick to default values for each parameter
    args = parser.parse_args([])

palle = bpy.data.collections['T0_Palle'].all_objects[:]
birilli = bpy.data.collections['T0_Birilli'].all_objects[:]

game_area = bpy.data.objects['Panno']
x_table_center = game_area.location.x
y_table_center = game_area.location.y
# limiti_palle = {
#     'x_max': -1.0, 
#     'x_min': -1.2, 
#     'y_max': 0.10, 
#     'y_min': -0.10825
# }
limiti_palle = {
    'x_max': x_table_center + (game_area.dimensions.x / 2) - 0.295, 
    'x_min': x_table_center - (game_area.dimensions.x / 2) + 0.295, 
    'y_max': y_table_center + (game_area.dimensions.y / 2) - 0.295, 
    'y_min': y_table_center - (game_area.dimensions.y / 2) + 0.295
}

## randomizzare luci (accendere  o meno il tavolo vicino)
## mettere delle persone
## posizione camera ??
## palle
## colore panno
## colore tavolo
## colore sponde
## muri

def select_single_object(obj):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def select_multiple_objects(objs):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = objs[0]
    for obj in objs:
        obj.select_set(True)


def enable_rigid_body_physics(
    obj, 
    collision_shape, 
    rigid_body_type, 
    mass, 
    friction=1.0,
    bounciness=0,
    linear_damping=0.04, 
    angular_damping=0.1):
    
    select_single_object(obj)
    
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.collision_shape = collision_shape
    obj.rigid_body.type = rigid_body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = bounciness
    obj.rigid_body.linear_damping = linear_damping
    obj.rigid_body.angular_damping = angular_damping


def disable_rigid_body_physics(obj):
    select_single_object(obj)
    bpy.ops.rigidbody.object_remove()


def set_random_initial_velocity(obj, max_offset):
    """
    Set a random initial velocity (with only x and y components) for the 
    given object, using keyframes. For a demonstration of how this works 
    in practice, check this YouTube video:
    https://www.youtube.com/watch?v=Xe5fiGrG_2s
    """

    offset_x, offset_y = np.random.uniform(
        low=-max_offset, 
        high=max_offset, 
        size=2)

    scene = bpy.context.scene

    scene.frame_set(1)
    obj.rigid_body.kinematic = True
    obj.keyframe_insert('location')
    obj.keyframe_insert('rigid_body.kinematic')

    scene.frame_set(3)
    obj.location.x += offset_x
    obj.location.y += offset_y
    obj.keyframe_insert('location')
    obj.keyframe_insert('rigid_body.kinematic')

    scene.frame_set(4)
    obj.rigid_body.kinematic = False
    obj.keyframe_insert('rigid_body.kinematic')


def position_balls(balls, game_area, max_ball_diameter_m=0.059):

    game_area_center = game_area.location
    game_area_width = game_area.dimensions.x
    game_area_height = game_area.dimensions.y
    
    x_min = game_area_center.x - (game_area_width / 2)
    x_max = game_area_center.x + (game_area_width / 2)
    # y_min = game_area_center.y - (game_area_height / 2)
    # y_max = game_area_center.y + (game_area_height / 2)

    n_balls_in_first_row = (len(balls) + 1) // 2
    x_coordinates_first_row, step_x = np.linspace(
        x_min, 
        x_max, 
        num=n_balls_in_first_row + 2, 
        retstep=True)
    x_coordinates_first_row = x_coordinates_first_row[1:-1]

    n_balls_in_second_row = len(balls) // 2
    x_coordinates_second_row = np.linspace(
        x_min, 
        x_max, 
        num=n_balls_in_second_row + 2, 
        retstep=False)
    x_coordinates_second_row = x_coordinates_second_row[1:-1]

    step_y = game_area_height / 2
    y_coordinate_first_row = game_area_center.y + (step_y / 2)
    y_coordinate_second_row = game_area_center.y - (step_y / 2)

    permuted_ball_indices = np.random.permutation(len(balls))

    for i, x_coord in enumerate(x_coordinates_first_row):
        
        balls[permuted_ball_indices[i]].location.x = x_coord
        balls[permuted_ball_indices[i]].location.y = y_coordinate_first_row

    for i, x_coord in enumerate(
        x_coordinates_second_row, 
        len(x_coordinates_first_row)):
        
        balls[permuted_ball_indices[i]].location.x = x_coord
        balls[permuted_ball_indices[i]].location.y = y_coordinate_second_row
    
    # Set initial velocity
    for ball in balls:
        max_offset = min(step_x//2, step_y//2) - max_ball_diameter_m
        set_random_initial_velocity(ball, max_offset=max_offset)


def apply_visual_transform(objs):
    select_multiple_objects(objs)
    bpy.ops.object.visual_transform_apply()    


# Enable rigid body physics for both balls and pins
for palla in palle:
    enable_rigid_body_physics(
        palla, 
        collision_shape='SPHERE', 
        rigid_body_type='ACTIVE', 
        mass=1,
        bounciness=0.5
    )
for birillo in birilli:
    enable_rigid_body_physics(
        birillo, 
        collision_shape='CONVEX_HULL', 
        rigid_body_type='ACTIVE', 
        mass=0.005,
        linear_damping=0.5,
        angular_damping=1.0
    )

# Scramble the balls (leaving the z-coordinate unchanged) and give them 
# an initial velocity
position_balls(palle, game_area)

# for palla in palle:
    # palla.location.x = random.uniform(
    #     limiti_palle['x_min'], limiti_palle['x_max']
    # )
    # palla.location.y = random.uniform(
    #     limiti_palle['y_min'], limiti_palle['y_max']
    # )

# Run the simulation to separate overlapping objects
bpy.context.scene.frame_end = 300
for f in range(1, bpy.context.scene.frame_end):
    bpy.context.scene.frame_set(f)

# Apply transformations (location and rotation) made by the simulation
all_objects = palle + birilli
apply_visual_transform(all_objects)

# Disable rigid body physics for all objects
for obj in all_objects:
    disable_rigid_body_physics(obj)

# Remove animation data from balls that was used to give them an initial
#  velocity
for palla in palle:
    palla.animation_data_clear()

# Save the blend file
bpy.ops.wm.save_as_mainfile(filepath=args.output_path)