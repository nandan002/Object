import time
import os.path
from multiprocessing import Process, Queue
from threading import Thread
import queue
import cv2
import numpy as np

from flask import Flask, request, render_template, jsonify,make_response
import concurrent.futures

app = Flask(__name__)

def drawBox(img,bbox):
    x,y,w,h =int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])

    cv2.rectangle(img,(x, y),((x+w),(y+h)),(255,0,255),1,1)
    cv2.putText(img, "TRACKING", (75,75), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)


def object_track(video,image,bbox,description,price):
    cap=cv2.VideoCapture(video)
    tracker = cv2.legacy_TrackerKCF.create()
    image=cv2.imread(image)
    bbox=bbox.split(',')
    print(bbox)
    bbox=tuple((int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])))
    tracked=[]
    track, lost = 0, 0
    track_frame_count,lost_frame_count=0,0
    total_frame_count=0

    tracker_time=[]

    tracker.init(image,bbox)
    fourcc=cv2.VideoWriter_fourcc(*'MJPG')
    result = cv2.VideoWriter('filename.mp4',
                             fourcc,
                             10, (image.shape[1], image.shape[0]))
    while cap.isOpened():
        success, img = cap.read()
        if success:
            # img = cv2.resize(img, (800, 600))
            total_frame_count += 1
            fps = cap.get(cv2.CAP_PROP_FPS)
            success, bbox = tracker.update(img)
            height, width, channel = img.shape
            if success:
                drawBox(img, bbox)
                track_frame_count += 1
                track += 1
                if track == 1:
                    tracked.append(lost_frame_count)
                    #     duration = round((float(lost_frame_count) / fps), 3)
                    #     lost.append(duration)
                    lost = 0
            else:
                lost_frame_count += 1
                lost += 1

                if lost == 1:
                    tracked.append(track_frame_count)

                    track = 0

                cv2.putText(img, "LOST", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, str(description), (20, int(height) - 50), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 0, 255),
                        1,lineType=cv2.LINE_AA)
            cv2.putText(img, str(price)+"$", (width - 100, int(height) - 50), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 255),
                        1)
            result.write(img)
            cv2.waitKey(1)
        else:
            break
    tracked.append(total_frame_count)
    new_list = [round(float(x / fps), 3) for x in tracked]

    for i in range(1, len(new_list)):
        new_list[i] += new_list[i - 1]

    for i in range(1, len(new_list), 2):
        tracker_time.append(str(new_list[i - 1]) + ":" + str(new_list[i]))
    cap.release()
    return jsonify({"Tracker Time":tracker_time})

@app.route('/object', methods=["POST"])
def object():

    if request.method == 'GET':
        return make_response(jsonify({'error':'Please Send POST request'}))
    elif request.method == 'POST':

        params = request.get_json()
        tracker_time=object_track(params['video'],params['image'],params['bbox'],params['description'],params['price'])

    return tracker_time

if __name__ == '__main__':
    app.run(debug=True)