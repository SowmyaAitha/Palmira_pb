import json
import os
import cv2
import numpy as np
from detectron2.data import DatasetCatalog
from detectron2.data import MetadataCatalog
from detectron2.structures import BoxMode

images_root = "images"  # This must contain 4 folders each for a dataset
via_json_root = "doc_pb"  # This must contain 3 folders named train, test, val; each with a via_region_data.json


categories_dict = {
    "Page Boundary": 0,
    # In case you are using it on Dataset-v1, please split Pic/Deco into 2 individual classes
}

categories_list = [
    "Page Boundary",
]


def get_indiscapes_dicts(img_dir, doc_dir):
    """
    https://detectron2.readthedocs.io/en/latest/tutorials/datasets.html
    Cleans the dataset (file name regularization, etc.) and pre-proccesses to match
    COCO type annotations to be natively loaded into detectron2
    :param img_dir: directory holding images
    :param doc_dir: directory holding annotation jsons
    :return: dictionary of COCO-type formatted annotations of Indiscapes-v2
    """
    json_file = os.path.join(doc_dir, "via_region_data.json")
    with open(json_file) as f:
        imgs_anns = json.load(f)
    dataset_dicts = []
    for idx, v in enumerate(imgs_anns["_via_img_metadata"].values()):
        record = {}
        url = v["filename"]
        filename = url.replace("%20", " ")
        bhoomi = ["Bhoomi_data", "bhoomi"]

        if 'pdf_images' in  filename:
            file_name1=img_dir+'/pdf_images'+filename.split('pdf_images')[1]
        elif "Stacked_images" in filename:
            file_name1 = filename.split("../")[1]+'.jpg'
            # print(filename)
            continue
        elif "google_scraped" in filename:
            file_name1=img_dir+"/google_scraped"+filename.split('images')[1]
        elif "ASR_Images" in filename:
            file_name1=img_dir+'/ASR_Images/'+filename.split('/')[-1]
        elif "Jain_manuscripts" in filename:
            file_name1 = img_dir +'/Jain_manuscripts/'+filename.split("images/")[1]
        elif "bhoomi" in filename:
            file_name1 = img_dir + "/Bhoomi_data/" + filename.split('/')[-1]
        elif "penn_in_hand" in filename:
            file_name1 = img_dir + '/penn_in_hand/'+filename.split('/')[-1]
        elif "penn-in-hand" in filename:
            file_name1 = img_dir +'/penn-in-hand/'+ filename.split('/')[-1]
        else:
            print(filename)
            
        if not os.path.exists(file_name1):
            continue
        # print(file_name1)
        img = cv2.imread(file_name1)
        height, width = img.shape[:2]
        record["file_name"] = file_name1
        record["height"] = height
        record["width"] = width
        record["image_id"] = idx

        annos = v["regions"]
        objs = []
        for idx, anno in enumerate(annos):
            shape = anno["shape_attributes"]

            if "all_points_x" not in shape.keys():
                shape["all_points_x"] = [
                    shape["x"] - (shape["width"] / 2),
                    shape["x"] - (shape["width"] / 2),
                    shape["x"] + (shape["width"] / 2),
                    shape["x"] + (shape["width"] / 2),
                ]
                shape["all_points_y"] = [
                    shape["y"] + (shape["height"] / 2),
                    shape["y"] - (shape["height"] / 2),
                    shape["y"] - (shape["height"] / 2),
                    shape["y"] + (shape["height"] / 2),
                ]

            px = shape["all_points_x"]
            py = shape["all_points_y"]

            if len(px) < 6:
                while len(px) < 6:
                    px.insert(1, (px[0] + px[1]) / 2)
                    py.insert(1, (py[0] + py[1]) / 2)

            poly = [(x, y) for x, y in zip(px, py)]
            poly = [p for x in poly for p in x]

            region = anno["region_attributes"]["Spatial Annotation"]

            if type(region) is list:
                region = region[0]
            if region == "Page Boundary":
                obj = {
                    "bbox": [np.min(px), np.min(py), np.max(px), np.max(py)],
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": categories_dict[region],
                }
                objs.append(obj)

        record["annotations"] = objs
        if len(objs):
            dataset_dicts.append(record)
    return dataset_dicts


def register_dataset(combined_train_val=False):
    """
    Registers the datasets to DatasetCatalog of Detectron2
    This is to ensure that Detectron can load our dataset from it's configs
    :param combined_train_val: Optional parameter for combining train and validation
    set
    :return: None
    """
    DatasetCatalog.clear()
    for d in ["train", "val", "test"] if combined_train_val else ["train", "val", "test"]:
        DatasetCatalog.register(
            "indiscapes_" + d,
            lambda d=d: get_indiscapes_dicts(images_root, os.path.join(via_json_root, d)),
        )
        MetadataCatalog.get("indiscapes_" + d).set(thing_classes=categories_list)
        MetadataCatalog.get("indiscapes_" + d).set(evaluator_type="indiscapes")
