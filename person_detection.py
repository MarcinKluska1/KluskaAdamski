import os

import cv2
import cvlib as cv
from cvlib.object_detection import draw_bbox
# import time
import numpy
import tensorflow

def process_image(image) -> tuple[list, list, list]:
    image: numpy.ndarray = cv2.imread(image)
    # start: float = time.time()
    bboxes, labels, confidences = cv.detect_common_objects(
        image,
        confidence=MINIMUM_CONFIDENCE,
        model=MODEL)
    # end: float = time.time()
    return bboxes, labels, confidences


def draw_bbox_for_persons(
        image_path: str,
        directory: str,
        labels: list,
        bboxes: list,
        confidences: list) -> None:
    bbox_person: list = []
    label_person: list = []
    image_name: str = image_path.split("/")[-1]
    image: numpy.ndarray = cv2.imread(image_path)
    colors: list[:tuple] = []
    for bbox, label, confidence in zip(bboxes, labels, confidences):
        if label == 'person':
            bbox_person.append(bbox)
            label_person.append(label)
            colors.append((0, 0, 255))
    processed_image = draw_bbox(
        image,
        bbox_person,
        label_person,
        confidences,
        write_conf=True,
        colors=colors)
    cv2.imwrite(os.path.join('processed_images/', image_name), processed_image)


# def print_picture(image_path: str) -> None:
#     image: numpy.ndarray = cv2.imread(image_path)
#     cv2.imshow(image_path, image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()


def get_results(image) -> None:
    bboxes, labels, confidences = process_image(image)
    person_counter: int = 0
    # print("========= Zdjęcie: {} ========="
    #       .format(image_path.split("\\")[-1]))
    for label, confidence in zip(labels, confidences):
        if label == "person":
            person_counter += 1
            print(f"Wykryto osobę z "
                  f"prawdopodobieństwem: {round(confidence * 100, 1)}%")
    if person_counter == 0:
        return f"Nie wykryto żadnych osób na zdjęciu"
    else:
        # return f"Wykryto {person_counter} osób na zdjęciu"
        draw_bbox_for_persons(
            image,
            IMAGE_OUTPUT_DIRECTORY,
            labels,
            bboxes,
            confidences)
    # print_picture(
    #     IMAGE_OUTPUT_DIRECTORY + "\\" + image_path.split("\\")[-1])


# IMAGE_INPUT_DIRECTORY: str = "images"
IMAGE_OUTPUT_DIRECTORY: str = "processed_images"
MINIMUM_CONFIDENCE: float = 0.4
MODEL: str = "yolov4-tiny"
# MODEL: str = "yolov4"
# get_results()

