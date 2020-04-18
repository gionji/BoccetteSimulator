BLENDER_PROJECT_HOME=..
BLEND_FILE=$BLENDER_PROJECT_HOME/tavolo_giovanni_generazione_dataset.blend
BLEND_FILE_SCRAMBLED=$BLENDER_PROJECT_HOME/scrambled.blend

SCRIPTS_HOME=$BLENDER_PROJECT_HOME/scripts
SCRAMBLER_SCRIPT=$SCRIPTS_HOME/scramble_balls.py
LABELLER_SCRIPT=$SCRIPTS_HOME/label_image.py
FORMATTER_SCRIPT=$SCRIPTS_HOME/format_annotations.ipy

# Flags for specifying which kind of annotations to output
MASKS_FLAG=
OUTLINES_FLAG=--no-outlines
COMPLETE_MASKS_FLAG=

BALLS_CATEGORY_ID=1
DIAMONDS_CATEGORY_ID=2

RENDER_WIDTH=1024
RENDER_HEIGHT=768
RENDER_SAMPLES=64

function create_diamond_annotations {
    
    # Create raw annotations for the diamonds
    DIAMONDS_DIR=$1/diamonds
    mkdir -p $DIAMONDS_DIR
    blender $BLEND_FILE \
        -b \
        --python $LABELLER_SCRIPT \
        -- \
        -cn Camera_sinistra \
        -p fisheye_equisolid \
        -c T0_Diamanti \
        -cs Panno \
        $MASKS_FLAG \
        $OUTLINES_FLAG \
        -v \
        -ao $DIAMONDS_DIR

    # Refine annotations for the diamonds
    ipython3 $FORMATTER_SCRIPT -- \
        -i $DIAMONDS_DIR \
        -r $2 \
        -c $DIAMONDS_CATEGORY_ID \
        -o $1
}

function create_ball_annotations {
    
    # Scramble the balls over the table
    blender $BLEND_FILE \
        -b \
        --python $SCRAMBLER_SCRIPT \
        -- \
        -o $BLEND_FILE_SCRAMBLED

    # Create raw annotations for the balls
    BALLS_DIR=$1/balls
    mkdir -p $BALLS_DIR
    blender $BLEND_FILE_SCRAMBLED \
        -b \
        --python $LABELLER_SCRIPT -- \
        -rh $RENDER_HEIGHT \
        -rw $RENDER_WIDTH \
        -rs $RENDER_SAMPLES \
        -cn Camera_sinistra \
        -p fisheye_equisolid \
        -c T0_Palle \
        -cs Panno \
        $MASKS_FLAG \
        $OUTLINES_FLAG \
        $COMPLETE_MASKS_FLAG \
        -ro $2 \
        -ao $BALLS_DIR

    # Remove the temporary blend file containing scrambled balls
    rm -f $BLEND_FILE_SCRAMBLED

    # Refine annotations for the balls
    ipython3 $FORMATTER_SCRIPT -- \
        -i $BALLS_DIR \
        -r $2\
        -c $BALLS_CATEGORY_ID \
        -o $1
}

N_IMAGES=1
DATASET_DIR=$BLENDER_PROJECT_HOME/dataset
for (( i=1; i<=$N_IMAGES; i++ )); do
    IMG_ID=$(printf "%06d" $i)
    OUTPUT_DIR=$DATASET_DIR/img_$IMG_ID
    RENDER_PATH=$OUTPUT_DIR/$IMG_ID.png
    create_ball_annotations $OUTPUT_DIR $RENDER_PATH
done
create_diamond_annotations $DATASET_DIR $RENDER_PATH
