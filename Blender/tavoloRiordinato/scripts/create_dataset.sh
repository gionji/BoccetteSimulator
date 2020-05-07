BLENDER_PROJECT_HOME=..
BLEND_FILE=$BLENDER_PROJECT_HOME/tavolo_giovanni_generazione_dataset.blend
BLEND_FILE_SCRAMBLED=$BLENDER_PROJECT_HOME/scrambled.blend

SCRIPTS_HOME=$BLENDER_PROJECT_HOME/scripts
SCRAMBLER_SCRIPT=$SCRIPTS_HOME/scramble_balls.py
LABELLER_SCRIPT=$SCRIPTS_HOME/label_image.py
FORMATTER_SCRIPT=$SCRIPTS_HOME/format_annotations.ipy

# Flags for specifying which kind of annotations to output
MASKS_FLAG=                  # --no-masks or empty
OUTLINES_FLAG=--no-outlines  # --no-outlines or empty
COMPLETE_MASKS_FLAG=         # --individual-renders or empty

RED_BALLS_CATEGORY_ID=0
BLUE_BALLS_CATEGORY_ID=1
WHITE_BALLS_CATEGORY_ID=2
DIAMONDS_CATEGORY_ID=3

RENDER_WIDTH=1024
RENDER_HEIGHT=768
RENDER_SAMPLES=256

function create_diamond_annotations {
    
    # Create raw annotations for the diamonds
    DIAMONDS_DIR=$1/diamonds
    mkdir -p $DIAMONDS_DIR
    blender $BLEND_FILE \
        -b \
        --python $LABELLER_SCRIPT -- \
        -rh $RENDER_HEIGHT \
        -rw $RENDER_WIDTH \
        -cn Camera_sinistra \
        -p fisheye_equisolid \
        -c T0_Diamanti \
        -cid $DIAMONDS_CATEGORY_ID \
        -cs Panno \
        $MASKS_FLAG \
        $OUTLINES_FLAG \
        -v \
        -ao $DIAMONDS_DIR

    # Refine annotations for the diamonds
    ipython3 $FORMATTER_SCRIPT -- \
        -i $DIAMONDS_DIR \
        -o $1 \
        --image-width $RENDER_WIDTH \
        --image-height $RENDER_HEIGHT
}

function create_ball_annotations {
    
    # Scramble the balls over the table
    blender $BLEND_FILE \
        -b \
        --python $SCRAMBLER_SCRIPT -- \
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
        -c T0_Palle_rosse T0_Palle_blu T0_Palle_bianche \
        -cid $RED_BALLS_CATEGORY_ID $BLUE_BALLS_CATEGORY_ID $WHITE_BALLS_CATEGORY_ID \
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
        -o $1 \
        --image-width $RENDER_WIDTH \
        --image-height $RENDER_HEIGHT \
        --image-name $3
}

N_IMAGES=${1:-500}
OUTPUT_DIR=$BLENDER_PROJECT_HOME/dataset
for (( i=1; i<=$N_IMAGES; i++ )); do
    IMG_ID=$(printf "%06d" $i)
    RENDER_PATH=$OUTPUT_DIR/$IMG_ID.png
    create_ball_annotations $OUTPUT_DIR $RENDER_PATH $IMG_ID
done
create_diamond_annotations $OUTPUT_DIR
