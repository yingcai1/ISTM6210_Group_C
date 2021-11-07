##################################### p1 import libraries
import cv2
import numpy as np
import base64
import pymysql
import time
from datetime import datetime
from tensorflow.keras.models import model_from_json
import face_recognition
import os

# Database connection - Get victims' info
conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    passwd="ying1234",
    port=3306,
    db="test",
)
cursor = conn.cursor()
sql = f"""
    select * from user
"""
known_face_encodings = []
known_face_names =[]
names = ""
try:
    cursor.execute(sql)
    data = cursor.fetchall()
    for row in data:
        # print("Id = ", row[0], )
        image = row[7]
        id = row[0]
        names = row[2] + " "+ row[3]
        # image = image.decode('utf-8')
        # print(image)
        # retrive all decoded images from database and store in imgs folder
        image_64_decode = base64.decodebytes(image) 
        image_result = open('imgs/userImages.jpg', 'wb')
        image_result.write(image_64_decode)

        kw_image = face_recognition.load_image_file("imgs/userImages.jpg")
        kw_face_encoding = face_recognition.face_encodings(kw_image)[0]

        # storing face encoded data and name into different lists
        known_face_encodings.append(kw_face_encoding)
        known_face_names.append(names)
        # print(cases)
        
        # id = row[0]
except Exception as e:
    print(e)
    print("Fail to load data!")
finally:
    conn.close()

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
face_classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
##################################### p2 Class - loading cnn model & model weights
class FacialExpression(object):
    expressions = ["Fear", 
                "Angry", 
                "Happy",
                "Disgust",
                "Neutral", 
                "Sad",
                "Surprise"]
    def __init__(self, json_file, weights_file):
        # Load model from JSON
        with open(json_file, "r") as json_file:
            loaded_json = json_file.read()
            self.loaded_model = model_from_json(loaded_json)
        # Load weights into the new model
        self.loaded_model.load_weights(weights_file)
        self.loaded_model.make_predict_function()

    def expression_prediction(self, img):
        self.pred = self.loaded_model.predict(img)
        return FacialExpression.expressions[np.argmax(self.pred)]


#################################### p3 get camera frames & make prediction
cnnmodel = FacialExpression("cnn_model.json", "cnn_modelWeights.h5")

# video_cap = cv2.VideoCapture(0)
class Webcam_Camera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.start_time = time.time()
    def __del__(self):
        # remove temporary image file
        os.remove("imgs/userImages.jpg")
        self.video.release()
        
    # Camera frames with bounding boxes and predictions
    def cameraframe(self):
        global face_locations
        global face_encodings
        global face_names
        global process_this_frame

        _, frame = self.video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
            # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                face_names.append(name)
        process_this_frame = not process_this_frame


        for (x, y, w, h) in faces:
                    # Loop through each face in this frame of video
            for (a, b, c, d), name in zip(face_locations, face_names):
                a *= 5
                b *= 5
                c *= 5
                d *= 5
                
                # Draw a label with a name below the face
                # cv2.rectangle(frame, (x+300,y+55), (h, y), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, name, (x,y+30), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 0), 2)
            fc = gray[y:y+h, x:x+w]
            roi = cv2.resize(fc, (48, 48),interpolation=cv2.INTER_AREA)
            pred = cnnmodel.expression_prediction(roi[np.newaxis, :, :, np.newaxis])
            
            # abnormal status
            if pred == "Fear" or pred == "Surprise":
            # print('Abnormal Status Detected')
                cv2.putText(frame,"Abnormal Status Detected!",(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),4)
                # cv2.putText(fr,"Hands up!",(10,300),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),4)

                cv2.putText(frame, "Fear", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
                
                abnormal_img = "abnormal_{}.png".format(0)
                # store abnormal image into imgs file
                # cv2.imwrite(abnormal_img, frame)

                _, buffer = cv2.imencode('.jpeg', frame)
                jpg_as_text = base64.b64encode(buffer)
                
                if time.time() - self.start_time >= 10:
                    now = datetime.now()
                    # dd/mm/YY H:M:S
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    
                    # update(jpg_as_text,dt_string)
                    self.start_time = time.time()
                else:
                    continue  
            else:
                cv2.putText(frame, "Normal", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0, 255,0),2)
            # cv2.putText(frame,'No Face Found',(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,255,0),4)
        return frame

# adding records when abnormal status detected
def update(img_Encoded,dt_string):
    # database connection
    conn = pymysql.connect(
        host="127.0.0.1",
        user="root",
        passwd="ying1234",
        port=3306,
        db="test",
    )
    cursor = conn.cursor()
    sql_insert = f""" 
        INSERT INTO cases
        (img, time, location, status) VALUES (%s,%s,%s,%s)
    """
    case_address = "Duques Hall, 2201 G St NW, Washington, DC 20052"
    insert_case = (img_Encoded,dt_string, case_address, "Detected")
    try:
        cursor.execute(sql_insert, insert_case)
        conn.commit()
        print("insert successfully!")
    except Exception as e:
        print(e)
        conn.rollback()
        print("Fail to insert data!")
    finally:
        conn.close()
    
#################################### p5 Show output video
def showcamera(camera):
    start_time = time.time()
    while True:
        frame = camera.cameraframe()
        cv2.imshow('Intelligent Alert System',frame)
        # key = cv2.waitKey(10)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
#     video_cap.release()
    cv2.destroyAllWindows()
    for i in range (1,5):
        cv2.waitKey(1)

##################################### Execute the code
showcamera(Webcam_Camera())



