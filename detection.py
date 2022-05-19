import time
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
import core.utils as utils
from tensorflow.python.saved_model import tag_constants
from core.config import cfg
import cv2
import numpy as np
import matplotlib.pyplot as plt
# from tensorflow.compat.v1 import ConfigProto
from deep_sort import preprocessing, nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from tools import generate_detections as gdet

import csv


def video_detection(path, filename):
    # Definition of the parameters
    max_cosine_distance = 0.4
    nn_budget = None
    nms_max_overlap = 1.0

    # initialize deep sort
    model_filename = 'model_data/mars-small128.pb'
    encoder = gdet.create_box_encoder(model_filename, batch_size=1)
    # calculate cosine distance metric
    metric = nn_matching.NearestNeighborDistanceMetric("cosine",
                                                       max_cosine_distance,
                                                       nn_budget)
    # initialize tracker
    tracker = Tracker(metric)

    # load configuration for object detector
    # config = ConfigProto()
    # config.gpu_options.allow_growth = True

    input_size = 416
    video_path = path

    saved_model_loaded = tf.saved_model.load('./checkpoints/yolov4-416',
                                             tags=[tag_constants.SERVING])
    infer = saved_model_loaded.signatures['serving_default']

    # begin video capture
    try:
        vid = cv2.VideoCapture(int(video_path))
    except:
        vid = cv2.VideoCapture(video_path)

    # get video ready to save locally if flag is set
    width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(vid.get(cv2.CAP_PROP_FPS))
    codec = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter(os.path.join('outputs/', filename), codec, fps, (width, height))

    coordinates = []
    frame_num = 0

    # while video is running
    while True:
        return_value, frame = vid.read()
        if return_value:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            break
        frame_num += 1
        image_data = cv2.resize(frame, (input_size, input_size))
        image_data = image_data / 255.
        image_data = image_data[np.newaxis, ...].astype(np.float32)
        start_time = time.time()

        # run detections
        batch_data = tf.constant(image_data)
        pred_bbox = infer(batch_data)
        for key, value in pred_bbox.items():
            boxes = value[:, :, 0:4]
            pred_conf = value[:, :, 4:]

        boxes, scores, classes, \
        valid_detections = tf.image.combined_non_max_suppression(
            boxes=tf.reshape(boxes, (tf.shape(boxes)[0], -1, 1, 4)),
            scores=tf.reshape(
                pred_conf,
                (tf.shape(pred_conf)[0], -1, tf.shape(pred_conf)[-1])),
            max_output_size_per_class=50,
            max_total_size=50,
            iou_threshold=0.45,
            score_threshold=0.4
        )

        # convert data to numpy arrays and slice out unused elements
        num_objects = valid_detections.numpy()[0]
        bboxes = boxes.numpy()[0]
        bboxes = bboxes[0:int(num_objects)]
        scores = scores.numpy()[0]
        scores = scores[0:int(num_objects)]
        classes = classes.numpy()[0]
        classes = classes[0:int(num_objects)]

        # format bounding boxes from normalized ymin, xmin, ymax, xmax --->
        # xmin, ymin, width, height
        original_h, original_w, _ = frame.shape
        bboxes = utils.format_boxes(bboxes, original_h, original_w)

        # read in all class names from config
        class_names = utils.read_class_names(cfg.YOLO.CLASSES)

        # custom allowed classes
        # (uncomment line below to customize tracker for only people)
        allowed_classes = ['person']

        # loop through objects and use class index to get class name,
        # allow only classes in allowed_classes list
        names = []
        deleted_indx = []
        for i in range(num_objects):
            class_indx = int(classes[i])
            class_name = class_names[class_indx]
            if class_name not in allowed_classes:
                deleted_indx.append(i)
            else:
                names.append(class_name)
        names = np.array(names)
        count = len(names)

        cv2.putText(frame, "Objects being tracked: {}".format(count),
                    (5, 35), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2,
                    (0, 255, 0), 2)

        # delete detections that are not in allowed_classes
        bboxes = np.delete(bboxes, deleted_indx, axis=0)
        scores = np.delete(scores, deleted_indx, axis=0)

        # encode yolo detections and feed to tracker
        features = encoder(frame, bboxes)
        detections = [Detection(bbox, score, class_name, feature) for
                      bbox, score, class_name, feature in
                      zip(bboxes, scores, names, features)]

        # initialize color map
        cmap = plt.get_cmap('tab20b')
        colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]

        # run non-maxima supression
        boxs = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        classes = np.array([d.class_name for d in detections])
        indices = preprocessing.non_max_suppression(boxs, classes,
                                                    nms_max_overlap, scores)
        detections = [detections[i] for i in indices]

        # Call the tracker
        tracker.predict()
        tracker.update(detections)

        # update tracks
        for track in tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            bbox = track.to_tlbr()
            class_name = track.get_class()

            # draw bbox on screen
            color = colors[int(track.track_id) % len(colors)]
            color = [i * 255 for i in color]
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])),
                          (int(bbox[2]), int(bbox[3])), color, 2)
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1] - 30)), (
                int(bbox[0]) + (
                        len(class_name) + len(str(track.track_id))) * 17,
                int(bbox[1])), color, -1)
            cv2.putText(frame, class_name + "-" + str(track.track_id),
                        (int(bbox[0]), int(bbox[1] - 10)), 0, 0.75,
                        (255, 255, 255), 2)

            coordinates.append(
                [frame_num, str(track.track_id), (bbox[0] + bbox[2]) / 2,
                 bbox[3]])

        result = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        out.write(result)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

