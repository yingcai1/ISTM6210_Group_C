##################################### p1 import libraries
import cv2
import numpy as np
import base64
import pymysql
import time
from datetime import datetime
from tensorflow.keras.models import model_from_json

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
        self.video.release()
        
    # Camera frames with bounding boxes and predictions
    def cameraframe(self):
        _, frame = self.video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
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



