import os
import json
from pprint import pprint
from PIL import Image

def convert_to_yolo_format(bbox, img_width, img_height):
    """
    Convert bounding box to YOLO format.
    bbox: [x_min, y_min, x_max, y_max]
    img_width: Width of the image
    img_height: Height of the image
    Returns: [x_center, y_center, width, height]
    """
    x_min, y_min, x_max, y_max = bbox
    x_center = (x_min + x_max) / 2 / img_width
    y_center = (y_min + y_max) / 2 / img_height
    width = (x_max - x_min) / img_width
    height = (y_max - y_min) / img_height
    return x_center, y_center, width, height

def process_annotations():
    """
    Process annotations and convert to YOLO format.
    """

    # access all sub-subfolders in root_path
    count = 0
    target_labels = ("bed", "couch", "railing", "rug", "stairs", "kerb", "step")
    label_counts = {label: 0 for label in target_labels}
    output_dir_images = "./data/ade20k_yolo/images/train"
    output_dir_labels = "./data/ade20k_yolo/labels/train"
    root_path = "./data/archive/ADE20K_2021_17_01/images/ADE/training"

    for outer_folder in os.listdir(root_path):
        for inner_folder in os.listdir(os.path.join(root_path, outer_folder)):
            # get annotation file
            for annotation_file in os.listdir(os.path.join(root_path, outer_folder, inner_folder)):
                if not annotation_file.endswith(".json"):
                    continue
                # read json file
                annotations_path = os.path.join(root_path, outer_folder, inner_folder, annotation_file)
                annotations_file_name = os.path.splitext(annotation_file)[0]

                with open(annotations_path, "r") as f:
                    # pretty print json file and send to output file
                    data = json.load(f)
                    for obj in data["annotation"]["object"]:
                        instance_mask_path = obj["instance_mask"]
                        img_file_name = data["annotation"]["filename"]
                        for target in target_labels:
                            if target in [label for hypernym in obj["hypernym"] for label in hypernym.split(", ")]:
                                label_counts[target] += 1
                                # compute bounding box for yolo from polygon x and y
                                x_max = max(obj["polygon"]["x"])
                                x_min = min(obj["polygon"]["x"])
                                y_max = max(obj["polygon"]["y"])
                                y_min = min(obj["polygon"]["y"])
                                # open img_file to get image width and height
                                img_path = os.path.join(root_path, outer_folder, inner_folder, img_file_name)
                                with Image.open(img_path) as img:
                                    img_width, img_height = img.size
                                    yolo_bbox = convert_to_yolo_format([x_min, y_min, x_max, y_max], img_width, img_height)
                                    label_index = list(target_labels).index(target)  # Assign a numeric label
                                    yolo_annotation = f"{label_index} {' '.join(map(str, yolo_bbox))}"
                                    # Write YOLO annotations to file
                                    yolo_file = os.path.join(output_dir_labels, f"{annotations_file_name}.txt")
                                    with open(yolo_file, "a") as f:
                                        f.write(yolo_annotation + "\n")
                                    # save image to output_dir
                                    output_img_path = os.path.join(output_dir_images, img_file_name)
                                    if not os.path.exists(output_img_path):
                                        img.save(output_img_path)
                        count += 1
                        if count % 10000 == 0:
                            print(f"Processed {count} objects")
    pprint(label_counts)

if __name__ == "__main__":
    process_annotations()