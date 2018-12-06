import keyboard #use the space bar as a "signal/new question" for testing
import cv2
import datetime
import tensorflow as tf
from scipy.spatial import distance as dist
from multiprocessing import Queue, Pool,Process #used for multiprocessing
from threading import Thread #used for threading
from imutils import face_utils
import dlib

try:
    from utilities.detector_utils import WebcamVideoStream
    from utilities import detector_utils

except ModuleNotFoundError:
    from .utilities.detector_utils import WebcamVideoStream
    from .utilities import detector_utils


# To run visual detection only:
# python detect_multi_threaded.py

def eye_aspect_ratio(eye):
    # compute the euclidean distances between the two sets of
    # vertical eye landmarks (x, y)-coordinates
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # compute the euclidean distance between the horizontal
    # eye landmark (x, y)-coordinates
    C = dist.euclidean(eye[0], eye[3])

    # compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    # return the eye aspect ratio
    return ear


frame_processed = 0
score_thresh = 0.2


# Create a worker thread that loads graph and
# does detection on images in an input queue and puts results on an output queue
# worker process is called by record() using Pool
def worker(input_q, output_q, cap_params, frame_processed):
    print(">> loading frozen model for worker")
    detection_graph, sess = detector_utils.load_inference_graph()
    sess = tf.Session(graph=detection_graph)
    thresh_touch_ratio=0.3
    frames_touch = 0
    prev_frame_processed = 0
    while True:
        # print("> ===== in worker loop, frame ", frame_processed)
        (frame,face_pts) = input_q.get() #get the frame of the webcam and the 17 points of the jaw from dlib from record()
        # print(face_pts)
        touch_detected = False #hand to face touch default is false

        if (frame is not None):
            # actual detection of hands
            boxes, scores = detector_utils.detect_objects(frame, detection_graph, sess)

            number_of_points = len(face_pts)
            # print(number_of_points)

            for i in range(cap_params['num_hands_detect']):
                # draw bounding boxes around the hands
                if (scores[i] > cap_params["score_thresh"]):
                    (left, right, top, bottom) = (boxes[i][1] * cap_params['im_width'], boxes[i][3] * cap_params['im_width'],
                                                  boxes[i][0] * cap_params['im_height'], boxes[i][2] * cap_params['im_height'])
                    p1 = (int(left), int(top))
                    p2 = (int(right), int(bottom))
                    cv2.rectangle(frame, p1, p2, (77, 255, 9), 3, 1)
                    j = 0
                    # CHECK IF DETECTED HANDS ARE TOUCHING THE FACE
                    while j < (number_of_points / 4 + 4):
                        """
                        x1,y1 -- x4,y4          L,T -- L+(R-L/2),T -- R,T       Top level
                          |  face  |             |   box around hands  |
                        x2,y2 -- x3,y3        L,T+(B-T/2)          R,T+(B-T/2)  Mid level
                        the face_pts are [0:17] from left to right
                        """
                        (x1, y1) = face_pts[-j-1]
                        (x2, y2) = face_pts[-j-2]
                        (x3, y3) = face_pts[j+1]
                        (x4, y4) = face_pts[j]

                        x_half = (right - left) / 2
                        y_half = (bottom - top) / 2
                        xL_half = left + x_half #L+(R-L/2)
                        yT_half = top + y_half  #T+(B-T/2)

                        #check if top left of box is touching face
                        if ((left <= x2) and (left >= x3) and (top >= y1) and (top <= y2)):
                            touch_detected = True
                        #check if top mid of box is touching face
                        elif ((xL_half <= x2) and (xL_half >= x3) and (top >= y1) and (top <= y2)):
                            touch_detected = True
                        #check if top right of box is touching face\
                        elif ((right <= x2) and (right >= x3) and (top >= y1) and (top <= y2)):
                            touch_detected = True
                        #check if mid left of box is touching face
                        elif ((left <= x2) and (left >= x3) and (yT_half >= y1) and (yT_half <= y2)):
                            touch_detected = True
                        #check if mid right of box is touching face
                        elif ((right <= x2) and (right >= x3) and (yT_half >= y1) and (yT_half <= y2)):
                            touch_detected = True
                        else:
                            pass
                        j = j + 1
            #keep track of how many frames there with hands touching a face
            if touch_detected:
                frames_touch = frames_touch + 1
            # print("touched: ", frames_touch)

            # add frame annotated with bounding box to queue
            output_q.put(frame)
            frame_processed += 1
        else:
            output_q.put(frame)

        try:  # used try so that if user pressed other than the given key error will not be shown
            if keyboard.is_pressed(' '):  # if space bar is pressed
            # IF SIGNAL IS RECIEVED, i.e. new question
                # HAND TOUCHING FACE -- LIE OR NOT
                num_frame_processed = frame_processed - prev_frame_processed
                current_touch_ratio = frames_touch/num_frame_processed
                # print("frames w/ hand touching face / frames processed", frames_touch," / ",frame_processed , " = ", current_touch_ratio )
                if (current_touch_ratio > thresh_touch_ratio):
                    print("HANDS-FACE: possibly a lie ", frames_touch," / ",num_frame_processed , " = ", current_touch_ratio)
                else:
                    print("HANDS-FACE: possibly NOT a lie ", frames_touch," / ",num_frame_processed , " = ", current_touch_ratio)
                frames_touch = 0 #reset counter for how total frames of hand to face touch for a question
                prev_frame_processed = frame_processed

                # BLINKING -- LIE OR NOT is at record()

            else:
                pass
        except:
            pass
    sess.close()

def record():

    # define two constants, one for the eye aspect ratio to indicate
    # blink and then a second constant for the number of consecutive
    # frames the eye must be below the threshold
    EYE_AR_THRESH = 0.3
    EYE_AR_CONSEC_FRAMES = 3

    # initialize the frame counters and the total number of blinks
    TOTAL_BLINKS = 0

    # initialize dlib's face detector (HOG-based) and then create
    # the facial landmark predictor
    print("[INFO] loading facial landmark predictor...")
    detector = dlib.get_frontal_face_detector()

    predictor = dlib.shape_predictor("visual/shape_predictor_68_face_landmarks.dat")

    # grab the indexes of the facial landmarks for the left and
    # right eye, respectively
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    # grab the indexes of the facial landmarks for the jaw
    (lStartjaw,rEndjaw)  = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

    input_q = Queue(maxsize=5)
    output_q = Queue(maxsize=7)

    video_capture = WebcamVideoStream(src=0,
                                      width=300,
                                      height=200).start()
    cap_params = {}
    frame_processed = 0
    cap_params['im_width'], cap_params['im_height'] = video_capture.size()
    cap_params['score_thresh'] = score_thresh

    # max number of hands we want to detect/track
    cap_params['num_hands_detect'] = 2

    # print(cap_params, args)

    # Assume face is exact center until found using dlib
    jaw_ = cv2.ellipse2Poly((150, 100), (45, 85), 0, 0, 180, 5)


    # spin up workers to paralleize detection.
    pool = Pool(4, worker,
                (input_q, output_q, cap_params, frame_processed))


    num_frames = 0
    fps = 0
    index = 0
    BLINK_COUNTER = 0
    TOTAL_BLINKS = 0

    current_blink_ratio = 0  # Blinks per second for current question
    thresh_blink_ratio = 26/60  # Threshold for blinks per minute --> possible lie or not

    show_display =1  # show display must be enabled in order for other show_x below to work
    show_fps = 1
    show_blinks = 1
    show_face = 1   # show_face means to show the jaw or not

    if(show_display>0):
        cv2.namedWindow('Multi-Threaded Detection', cv2.WINDOW_NORMAL)

    # time.sleep(1)
    start_time = datetime.datetime.now()    # start time for the camera feed
    start_time_quest = datetime.datetime.now() # start time for each question
    while True:

        frame = video_capture.read()
        frame = cv2.flip(frame, 1)
        index += 1

        #send the webcam feed and the points for the jaw over to worker
        input_q.put((cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),jaw_))
        #get the frames with or without bounding boxes around the hands
        output_frame = output_q.get()

        gray = cv2.cvtColor(output_frame, cv2.COLOR_BGR2GRAY)
        output_frame = cv2.cvtColor(output_frame, cv2.COLOR_RGB2BGR)

        elapsed_time = (datetime.datetime.now() -
                        start_time).total_seconds()
        num_frames += 1
        fps = num_frames / elapsed_time
        # print("frame ",  index, num_frames, elapsed_time, fps)

        if (output_frame is not None):

            try:  # used try so that if user pressed other than the given key error will not be shown
                if keyboard.is_pressed(' '):  # if space bar is pressed
                # IF SIGNAL IS RECIEVED, i.e. new question
                    elapsed_time_quest = (datetime.datetime.now() - start_time_quest).total_seconds()
                    print("elapsed time for the question: ",elapsed_time_quest)
                    # BLINKING -- LIE OR NOT
                    current_blink_ratio = TOTAL_BLINKS / elapsed_time_quest
                    if (current_blink_ratio > thresh_blink_ratio):
                        print("Blinking: possibly a lie ",TOTAL_BLINKS," / ",elapsed_time_quest," = ",current_blink_ratio)
                    else:
                        print("Blinking: not a lie ",TOTAL_BLINKS," / ",elapsed_time_quest," = ",current_blink_ratio)
                    TOTAL_BLINKS = 0

                    # HAND TOUCHING FACE -- LIE OR NOT is at the worker()

                    start_time_quest = datetime.datetime.now()
                else:
                    pass
            except:
                pass

            # detect faces in the grayscale frame
            rects = detector(gray, 0)

            # loop over the face detections
            for rect in rects:
                # determine the facial landmarks for the face region, then
                # convert the facial landmark (x, y)-coordinates to a NumPy
                # array

                shape = predictor(output_frame, rect)
                shape = face_utils.shape_to_np(shape)

                # extract the left and right eye coordinates, then use the
                # coordinates to compute the eye aspect ratio for both eyes
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)

                jaw_ = shape[lStartjaw:rEndjaw]
                # parent_conn.send(jaw_)
                # print(jaw_)

                # average the eye aspect ratio together for both eyes
                ear = (leftEAR + rightEAR) / 2.0

                # check to see if the eye aspect ratio is below the blink
                # threshold, and if so, increment the blink frame counter
                if ear < EYE_AR_THRESH:
                    BLINK_COUNTER += 1

                # otherwise, the eye aspect ratio is not below the blink
                # threshold
                else:
                    # if the eyes were closed for a sufficient number of
                    # then increment the total number of blinks
                    if BLINK_COUNTER >= EYE_AR_CONSEC_FRAMES:
                        TOTAL_BLINKS += 1

                    # reset the eye frame counter
                    BLINK_COUNTER = 0


                # if (args.display > 0):
                #     if (args.fps > 0):
                if (show_display > 0):
                    if (show_fps > 0):
                        detector_utils.draw_fps_on_image("FPS : " + str(int(fps)), output_frame)

                        # center=( int(args.width/2), int(args.height/2))
                        # cv2.ellipse(output_frame,center , (45, 85), 0, 0, 180, 255, 1)
                        # face_pts = cv2.ellipse2Poly((150, 100), (45, 85), 0, 0, 180, 5)
                        # cv2.polylines(output_frame, [face_pts], 1, (0, 255, 0))
                    if (show_blinks > 0):
                        # compute the convex hull for the left and right eye, then
                        # visualize each of the eyes
                        leftEyeHull = cv2.convexHull(leftEye)
                        rightEyeHull = cv2.convexHull(rightEye)
                        cv2.drawContours(output_frame, [leftEyeHull], -1, (0, 255, 0), 1)
                        cv2.drawContours(output_frame, [rightEyeHull], -1, (0, 255, 0), 1)

                        # draw the total number of blinks on the frame along with
                        # the computed eye aspect ratio for the frame
                        cv2.putText(output_frame, "Blinks: {}".format(TOTAL_BLINKS), (50, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(output_frame, "EAR: {:.2f}".format(ear), (200, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if (show_face > 0):
                        # compute the convex hull for the jaw, then
                        # visualize the jaw
                        jawHull = cv2.convexHull(jaw_)
                        cv2.drawContours(output_frame, [jawHull], -1, (0, 255, 0), 1)

                # print(left, right, top, bottom)

            cv2.imshow('Multi-Threaded Detection', output_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            else:
                if (num_frames == 400):
                    num_frames = 0
                    start_time = datetime.datetime.now()

                # else:
                #     print("frames processed: ", index, "elapsed time: ",
                #           elapsed_time, "fps: ", str(int(fps)))


        else:
            # print("video end")
            break
    elapsed_time = (datetime.datetime.now() -
                    start_time).total_seconds()
    fps = num_frames / elapsed_time
    print("fps", fps)

    # parent_conn.close()

    pool.terminate()
    video_capture.stop()
    cv2.destroyAllWindows()


	

if __name__ == '__main__':

#Process2 (audio was commented out for testing visual)

    ## Multiprocessing way
    try:
        process1 = Process(target=record)

        # process2 = Process(target=run_audio_detection)

        process1.start()
        print("Proecss 1 started")
        # process2.start()
        # print("Process 2 started")

        process1.join()
        # process2.join()


    except:
        print("process failed")

    ## This is the Threading way
    # try:
    #     thread1 = threading.Thread(target=record)
    #
    #     thread2 = threading.Thread(target=run)
    #
    #
    #     thread1.start()
    #      print("Thread 1 started")
    #     thread2.start()
    #     print("Thread 2 started")
    #
    #     thread1.join()
    #     thread2.join()
    #
    # except:
    #     print("Thread failed")

