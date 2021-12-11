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
import six

import tensorflow as tf
from object_detection.utils import config_util
from google.protobuf import text_format
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

# email
import smtplib, ssl
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from email.message import EmailMessage

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    passwd="ying1234",
    port=3306,
    db="test",
)
# Database connection - Get victims' info
cursor = conn.cursor()
sql = f"""
    select * from victims
"""
victimsFaces = []
victimsNames =[]
ids = []
# names = ""
try:
    cursor.execute(sql)
    data = cursor.fetchall()
    for row in data:
        # print("Id = ", row[0], )
        image = row[5]
        id = row[0]
        names = row[1] + " " + row[2]
        # image = image.decode('utf-8')
        # print(image)
        # retrive all decoded images from database and store in imgs folder
        faceDecode = base64.decodebytes(image) 
        # saveImage = open('imgs/userImages.jpg', 'wb')
        # saveImage.write(faceDecode)
        open('imgs/userImages.jpg', 'wb').write(faceDecode)

        allImage = face_recognition.load_image_file("imgs/userImages.jpg")
        allFaceEncode = face_recognition.face_encodings(allImage)[0]

        # storing face encoded data, name and id into lists
        victimsFaces.append(allFaceEncode)
        victimsNames.append(names)
        ids.append(id)
        # print(cases)
        # id = row[0]
except Exception as e:
    print(e)
    print("Fail to load data!")
finally:
    conn.close()

#gestures
paths = {'CHECKPOINT_PATH': os.path.join('Tensorflow','my_ssd_mobnet')}
files = {
    'PIPELINE_CONFIG':os.path.join('Tensorflow', 'my_ssd_mobnet', 'pipeline.config'),
    'LABELMAP': os.path.join('Tensorflow','annotations', 'label_map.pbtxt')}

# Load pipeline config and build a detection model
configs = config_util.get_configs_from_pipeline_file(files['PIPELINE_CONFIG'])
detection_model = model_builder.build(model_config=configs['model'], is_training=False)
ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(os.path.join(paths['CHECKPOINT_PATH'], 'ckpt-3')).expect_partial()

def detect_fn(image):
    image, shapes = detection_model.preprocess(image)
    prediction_dict = detection_model.predict(image, shapes)
    detections = detection_model.postprocess(prediction_dict, shapes)
    return detections

category_index = label_map_util.create_category_index_from_labelmap(files['LABELMAP'])

# Initialize variables
locFace = []
encFace = []
imageNames = []
imageIds = []
webcameFrame = True

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
    def __init__(self,location):
        self.video = cv2.VideoCapture(0)
        width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        # self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.start_time = time.time()
        self.location = location
    def __del__(self):
        # remove temporary image file
        os.remove("imgs/userImages.jpg")
        self.video.release()
        
    # Camera frames with bounding boxes and predictions
    def cameraframe(self):
        global locFace
        global encFace
        global imageNames
        global imageIds
        global webcameFrame

        faces = ""
        _, frame = self.video.read()
        if frame is not None: 
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        else:
            print("Empty frame")
            exit(1)
        # Resize frame of video to 1/4 size for faster face recognition processing
        resizeFrame = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2)

        # Convert from BGR color to RGB color
        resizeFrameRGB = resizeFrame[:, :, ::-1]

        # Only process every other frame of video to save time
        if webcameFrame:
            # Find all the faces and face encodings in the current frame of video
            locFace = face_recognition.face_locations(resizeFrameRGB)
            encFace = face_recognition.face_encodings(resizeFrameRGB, locFace)

            imageNames = []
            imageIds = []
            for encode in encFace:
                # See if the face is a match for the known face(s)
                correctFace = face_recognition.compare_faces(victimsFaces, encode)
                name = "UNKNOWN"
                id = "NULL"
            # If a match was found in victimsFaces, just use the first one.
                if True in correctFace:
                    first_match_index = correctFace.index(True)
                    name = victimsNames[first_match_index]
                    id = ids[first_match_index]
                imageNames.append(name)
                imageIds.append(id)
        webcameFrame = not webcameFrame

        # code for hand guestures
        input_tensor = tf.convert_to_tensor(np.expand_dims(frame, 0), dtype=tf.float32)
        detections = detect_fn(input_tensor)
        
        label_id_offset = 1
        image_np_with_detections = frame.copy()
        num_detections = int(detections.pop('num_detections'))
        
        detections = {key: value[0, :num_detections].numpy()
                    for key, value in detections.items()}
        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)
        viz_utils.visualize_boxes_and_labels_on_image_array(
                    image_np_with_detections,
                    detections['detection_boxes'],
                    detections['detection_classes']+label_id_offset,
                    detections['detection_scores'],
                    category_index,
                    use_normalized_coordinates=True,
                    max_boxes_to_draw=3,
                    min_score_thresh=.8,
                    agnostic_mode=False)

        ids_camera = []
        for (x, y, w, h) in faces:
                    # Loop through each face in this frame of video
            for (a, b, c, d), name, id in zip(locFace, imageNames,imageIds):
                a *= 5
                b *= 5
                c *= 5
                d *= 5
                # Draw a label with a name below the face
                # cv2.rectangle(frame, (x+300,y+55), (h, y), (0, 0, 255), cv2.FILLED)
                # cv2.putText(image_np_with_detections, name, (x,y+add), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 0), 2)
                # cv2.putText(frame, str(id), (x,y+add+20), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)
                cv2.putText(image_np_with_detections, name, (d,a), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)

                # cv2.putText(image_np_with_detections, str(id), (d,a+50), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)
                ids_camera.append(str(id))

            fc = gray[y:y+h, x:x+w]
            roi = cv2.resize(fc, (48, 48),interpolation=cv2.INTER_AREA)
            pred = cnnmodel.expression_prediction(roi[np.newaxis, :, :, np.newaxis])
            
            class_name = ''
            class_score = ''
            display_str = ''
            # cv2.putText(image_np_with_detections,detections['detection_classes']+label_id_offset,(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),4)
            classes = detections['detection_classes']+label_id_offset
            for i in range(detections['detection_boxes'].shape[0]):
                if detections['detection_scores'] is None or detections['detection_scores'][i] > 0.8:
                    if classes[i] in six.viewkeys(category_index):
                        class_name = category_index[classes[i]]['name']
                        class_score = '{}: {}%'.format(class_name, round(100*detections['detection_scores'][i]))
                    else:
                        class_score = 'N/A'
                    display_str = str(class_score)

            # abnormal status
            if class_name == "HandsUp" and (pred == "Fear" or pred == "Surprise"):
                cv2.putText(image_np_with_detections,"Abnormal Status Detected!",(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),5)
                cv2.putText(image_np_with_detections, "- "+display_str,(30,100),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),3)
                cv2.putText(image_np_with_detections, "- Fear",(30,150),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),3)
            # abnormal status
            # if pred == "Fear" or pred == "Surprise":
            # print('Abnormal Status Detected')
                # cv2.putText(image_np_with_detections,"Abnormal Status Detected!",(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),4)
                # cv2.putText(fr,"Hands up!",(10,300),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),4)

                cv2.putText(image_np_with_detections, "Fear", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.rectangle(image_np_with_detections,(x,y),(x+w,y+h),(0,0,255),2)
                
                abnormal_img = "abnormal_{}.png".format(0)
                # store abnormal image into imgs file
                # cv2.imwrite(abnormal_img, frame)

                _, buffer = cv2.imencode('.jpeg', image_np_with_detections)
                jpg_as_text = base64.b64encode(buffer)
                
                if time.time() - self.start_time >= 10:
                    now = datetime.now()
                    # dd/mm/YY H:M:S
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

                    for id in ids_camera:
                        update(jpg_as_text,dt_string, id, self.location)
                    self.start_time = time.time()
                else:
                    continue  
            else:
                if pred == "Fear" or pred == "Surprise":
                    cv2.putText(image_np_with_detections, "Fear", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.rectangle(image_np_with_detections,(x,y),(x+w,y+h),(0, 0,255),2)
                else:
                    cv2.putText(image_np_with_detections, "Normal", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.rectangle(image_np_with_detections,(x,y),(x+w,y+h),(0, 255,0),2)
            # cv2.putText(frame,'No Face Found',(10,50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,255,0),4)
        return image_np_with_detections

# adding records when abnormal status detected
def update(img_Encoded,dt_string, id, location):
    # database connection
    conn = pymysql.connect(
        host="127.0.0.1",
        user="root",
        passwd="ying1234",
        port=3306,
        db="test",
    )
    cursor = conn.cursor()
    if id != "NULL":
        sql_insert = f""" 
        INSERT INTO cases
        (img, time, location, status, victim_id) VALUES (%s,%s,%s,%s,%s)
        """
        case_address = location
        insert_case = (img_Encoded,dt_string, case_address, "Detected", id)
        try:
            cursor.execute(sql_insert, insert_case)
            conn.commit()
            print("insert successfully!")
            
            #alert email
            receivers_email = []
            try:
                cursor_email = conn.cursor()
                sql = f"""
                    select email from user
                """
                cursor_email.execute(sql)
                data_email = cursor_email.fetchall()
                for row in data_email:
                    receivers_email.append(row[0]) 
                #####  sending alert email to police ####
                sendEmail(receivers_email,case_address)
            except Exception as e:
                print(e)
                print("Fail to load data!")
        except Exception as e:
            print(e)
            conn.rollback()
            print("Fail to insert data!")
    else:
        sql_insert = f""" 
        INSERT INTO cases
        (img, time, location, status) VALUES (%s,%s,%s,%s)
        """
        case_address = location
        insert_case = (img_Encoded,dt_string, case_address, "Detected")
        try:
            cursor.execute(sql_insert, insert_case)
            conn.commit()
            print("insert successfully!")

            # alert email
            receivers_email = []
            try:
                cursor_email = conn.cursor()
                sql = f"""
                    select email from user
                """
                cursor_email.execute(sql)
                data_email = cursor_email.fetchall()
                for row in data_email:
                    receivers_email.append(row[0])

                #####  sending alert email to police ####
                sendEmail(receivers_email,case_address)
            except Exception as e:
                print(e)
                print("Fail to load data!")
        except Exception as e:
            print(e)
            conn.rollback()
            print("Fail to insert data!")

# email
def sendEmail(receivers_email,case_address):
    #####  sending alert email to police ####
    smtp_server = "smtp.gmail.com"
    port = 587 
    sender_email = "istm6210ias@gmail.com"
    password = "IAS@ISTM"
    for email in receivers_email:
        receiver_email = email
        subject = 'Abnormal status alert'
        msg = EmailMessage()
        msg.add_alternative("""\
            <!doctype html>
            <html>
            <body style="background-color: #f6f6f6; -webkit-font-smoothing: antialiased; line-height: 1.4; margin: 0; padding: 0; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;">
                <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%; background-color: #f6f6f6;">
                <tr>
                    <td style="vertical-align: top;">&nbsp;</td>
                    <td style="display: block; Margin: 0 auto; max-width: 580px; padding: 10px; width: 580px;">
                    <div style="box-sizing: border-box; display: block; Margin: 0 auto; max-width: 580px; padding: 10px;">

                        <table role="presentation" style="border-collapse: separate;  width: 100%; background: #ffffff; border-radius: 3px;">
                        <tr>
                            <td style="vertical-align: top; box-sizing: border-box; padding: 20px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                                <tr>
                                <td style="vertical-align: top;">
                                    <p style="margin: 0; Margin-bottom: 15px;">Hi there,</p>
                                    <p style="margin: 0; Margin-bottom: 15px;">
                                        Thanks for subscribing IAS. We've detected an abnormal status at
                                    </p>
                                    <p style="text-align: center;" colo>
                                        <i class="fas fa-map-marker-alt" style="margin-right:5px;"></i>
                                        <span style="color: red; font-weight: bold;">"""+case_address+"""</span>
                                    </p>
                                </p>
                                    <p style="margin: 0; Margin-bottom: 15px;">
                                        You should take action ASAP!
                                    </p>
                                    <p style="margin: 0; Margin-bottom: 15px;">
                                        Be careful!
                                    </p>
                                </td>
                                </tr>
                            </table>
                            </td>
                        </tr>
                        </table>
                        <div style="clear: both; Margin-top: 10px; text-align: center; width: 100%;">
                        <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                            <tr>
                                <td style="vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; text-align: center;">
                                    Intelligent alert system
                                </td>
                            </tr>
                            <tr>
                            <td style="vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; text-align: center;">
                                <span style="color: #999999; text-align: center;">Intelligent alert system, GWU ISTM 6210, Washington DC 20052</span>
                            </td>
                            </tr>
                        </table>
                        </div>
                    </div>
                    </td>
                    <td style="vertical-align: top;">&nbsp;</td>
                </tr>
                </table>
            </body>
            </html>
            """, subtype='html')
        msg['Subject'] = subject
        msg['From'] = formataddr((str(Header('Intelligent Alert System', 
                                                'utf-8')), sender_email))
        msg['To'] = receiver_email
        message = msg.as_string()
        context = ssl.create_default_context()
        try:
            server = smtplib.SMTP(smtp_server,port)
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        except Exception as e:
            print(e)
        finally:
            server.quit() 

#################################### p5 Show output video
def showcamera(camera):
    start_time = time.time()
    while True:
        frame = camera.cameraframe()
        # cv2.imshow('IAS detection',  cv2.resize(frame, (1000, 600)))

        cv2.imshow('Intelligent Alert System',frame)
        # key = cv2.waitKey(10)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
#     video_cap.release()
    cv2.destroyAllWindows()
    for i in range (1,5):
        cv2.waitKey(1)

##################################### Execute the code
# showcamera(Webcam_Camera())

if __name__ == '__main__':
    # Initalize Camera ID
    Camera_ID = 3

    conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    passwd="ying1234",
    port=3306,
    db="test",
    )
    # Database - checking if camera exists
    cursor_camera = conn.cursor()
    sql = f"""
        SELECT camera_id, COUNT(*) FROM camera 
        WHERE camera_id = %s GROUP BY camera_id
    """
    cursor_camera.execute(sql, Camera_ID)
    count = cursor_camera.fetchone()
    if count is None:
        print(f"Camera {Camera_ID} was not found in our records!")
    else:
        sql_status = f"""
        SELECT status,location FROM camera 
        WHERE camera_id = %s
        """
        cursor_camera.execute(sql_status,Camera_ID)
        status_data = cursor_camera.fetchone()
        camera_status = status_data[0]
        camera_location = status_data[1]
        if camera_status == "ON":
            showcamera(Webcam_Camera(camera_location))
        else:
            print(f"\n Please, turn on the camera {Camera_ID}! \n")
