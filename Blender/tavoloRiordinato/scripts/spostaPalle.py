import random
import bpy

palleBianche = ['Palla_bianca_1', 'Palla_bianca_2',  'Palla_bianca_3',  'Palla_bianca_4',]

palleRosse   = ['Palla_rossa_1', 'Palla_rossa_2',  'Palla_rossa_3',  'Palla_rossa_4',]

boccino      = ['Palla_blu']

palle        = palleBianche + palleRosse + boccino

#bordiPalle   = [0.25, -2.52, 0.68, -0.6825] # x min x max y_min y_max
bordiPalleMax   = {'x_max':0.25, 'x_min':-2.52, 'y_max':0.68, 'y_min':-0.6825}

bordiPalle   = {'x_max':-1.25, 'x_min':-2.0, 'y_max':0.38, 'y_min':-0.3825}

posizioni = {
        'Palla_bianca_1' : (-1 , 0.0),
        'Palla_bianca_2' : (-1 , 0.1),
        'Palla_bianca_3' : (-1 , 0.2),
        'Palla_bianca_4' : (-1 , 0.3),
        'Palla_rossa_1'  : (-1.2 , 0.1),
        'Palla_rossa_2'  : (-1.2 , 0.2),
        'Palla_rossa_3'  : (-1.2 , 0.3),
        'Palla_rossa_4'  : (-1.2 , 0.4),
        'Palla_blu'      : (-1.3 , 0.1),	 
}

print(bordiPalle)

scn = bpy.context.scene
scn.frame_set(1)

for key, items in posizioni.items():
        posizioni[key] = (random.uniform(bordiPalle['x_min'], bordiPalle['x_max']),
                          random.uniform(bordiPalle['y_min'], bordiPalle['y_max']),
        )
        

for palla, pos in posizioni.items():
        bpy.data.objects[ palla ].location.x = pos[0]
        bpy.data.objects[ palla ].location.y = pos[1]
        bpy.data.objects[ palla ].location.z = 1.008
        
scn.frame_set(10)

