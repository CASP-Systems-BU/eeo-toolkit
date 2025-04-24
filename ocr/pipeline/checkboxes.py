import cv2
import numpy as np
import fitz
from PIL import Image
import json
import os


from utilities.load_config import load_cell_coordination_config


def is_rectangle_dark(image, top_left, bottom_right, threshold):
    x1, y1 = top_left
    x2, y2 = bottom_right
    roi = image[y1:y2, x1:x2]

    # Compute sum of pixel values
    pixel_sum = np.sum(roi)

    # Compute max possible sum
    max_possible_sum = roi.size * 255

    if pixel_sum <= threshold * max_possible_sum:
        return True
    return False


def extract_from_checkbox(
    form_type, input_folder, output_folder, file_name, checkbox_config
):
    zoom = 3
    directory = os.path.join(input_folder, file_name)
    doc = fitz.open(directory)

    pix = doc[0].get_pixmap(
        matrix=fitz.Matrix(zoom, zoom)
    )  # Scale factor for higher resolution
    image = np.array(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))

    checkbox_key_map = load_cell_coordination_config(checkbox_config)
    json_map = {}
    threshold = 0.7
    for key, value in checkbox_key_map.items():
        top_left = (value[0], value[1])
        bottom_right = (value[2], value[3])
        json_map[key] = is_rectangle_dark(image, top_left, bottom_right, threshold)
    json_output = {}
    if form_type == "eeo1":
        json_output["id"] = "E-AND_F"
        json_output["section"] = "E"
        json_output["content"] = json_map
    elif form_type == "eeo5":
        json_output["id"] = "a-TYPE_OF_AGENCY"
        json_output["section"] = "a"
        json_output["content"] = json_map

    folder_name = os.path.splitext(file_name)[0]
    path = os.path.join(output_folder, folder_name + "_result.json")
    with open(path, "r+") as f:
        data = json.load(f)
        data.append(json_output)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        print("Data written to json file" + folder_name + "_result.json")
        f.close()


def extract_checkboxes(input_folder, output_folder, checkbox_config):
    for file in os.listdir(input_folder):
        if file.endswith(".pdf"):
            filename = os.path.basename(file)
            extract_from_checkbox(
                input_folder, output_folder, filename, checkbox_config
            )


def debug_checkbox(input_folder, file_name, checkbox_config):
    zoom = 3
    directory = os.path.join(input_folder, file_name)
    doc = fitz.open(directory)

    pix = doc[0].get_pixmap(
        matrix=fitz.Matrix(zoom, zoom)
    )  # Scale factor for higher resolution
    image = np.array(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))

    image_with_roi = image.copy()
    checkbox_key_map = load_cell_coordination_config(checkbox_config)
    for key, value in checkbox_key_map.items():
        top_left = (value[0], value[1])
        bottom_right = (value[2], value[3])
        image_with_roi = cv2.rectangle(
            image_with_roi, top_left, bottom_right, (0, 255, 0), 2
        )
    cv2.imwrite(file_name + "_image.png", image_with_roi)
