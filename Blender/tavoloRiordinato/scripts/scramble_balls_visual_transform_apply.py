import random
import bpy

bpy.context.scene.frame_end = 300

palleBianche = ['Palla_bianca_1', 'Palla_bianca_2',  'Palla_bianca_3',  'Palla_bianca_4',]
palleRosse   = ['Palla_rossa_1', 'Palla_rossa_2',  'Palla_rossa_3',  'Palla_rossa_4',]
boccino      = ['Palla_blu']
palle        = palleBianche + palleRosse + boccino

#bordiPalle   = [0.25, -2.52, 0.68, -0.6825] # x min x max y_min y_max
BORDI_PALLE_MAX = {'x_max':0.25, 'x_min':-2.52, 'y_max':0.68, 'y_min':-0.6825}

bordiPalle      = {'x_max':-1.0, 'x_min':-1.2, 'y_max':0.10, 'y_min':-0.10825}

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


## randomizzare luci ( accendere  o meno il tavolo vicino)
## mettere delle persone
## posizione camera ??
## palle
## colore panno
## colore tavolo
## colore sponde
## muri

bpy.ops.ptcache.free_bake_all()

for key, items in posizioni.items():
    posizioni[key] = (
        random.uniform(bordiPalle['x_min'], bordiPalle['x_max']),
        random.uniform(bordiPalle['y_min'], bordiPalle['y_max']),
   )

#liste per salvare le posizini        
posizioniIniziali = list()
posizioniFinali = list()

print("Posizioni Iniziali")
for palla, pos in posizioni.items():
    bpy.data.objects[ palla ].location.x = pos[0]
    bpy.data.objects[ palla ].location.y = pos[1]
    bpy.data.objects[ palla ].location.z = 1.008
   
    #salvo le posizioni iniziali prima della simulazioni in un  lista
    posizioniIniziali.append( bpy.data.objects[ palla ].location )
    
    x = bpy.data.objects[ palla ].location.x
    y = bpy.data.objects[ palla ].location.y
    print(f'{palla}: ({x}, {y})')
     
#evolve simulation      
for f in range( 1, bpy.context.scene.frame_end):
   bpy.context.scene.frame_set(f)

bpy.ops.object.visual_transform_apply()

print("Posizioni Finali")
for palla, pos in posizioni.items():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
            
    bpy.data.objects[palla].select_set(True)
    bpy.ops.object.visual_transform_apply()
            
    x = bpy.data.objects[ palla ].location.x
    y = bpy.data.objects[ palla ].location.y
    print(f'{palla}: ({x}, {y})')    







