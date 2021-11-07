# part 1
import cv2
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import utils
import os
import tensorflow as tf

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, Input, Dropout,Flatten, Conv2D
from tensorflow.keras.layers import BatchNormalization, Activation, MaxPooling2D
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from livelossplot.inputs.tf_keras import PlotLossesCallback
from tensorflow.keras.utils import plot_model
from tensorflow.keras.models import model_from_json

from IPython.display import SVG, Image
print("Tensorflow version:", tf.__version__)


# part 2
for expressions in os.listdir("train/"):
    print(str(len(os.listdir("train/" + expressions))) + " " + expressions + " images")

# part 3
train_dataGenerator = ImageDataGenerator(horizontal_flip=True)
validation_dataGenerator = ImageDataGenerator(horizontal_flip=True)

train_generator = train_dataGenerator.flow_from_directory("train/",
                                                    target_size=(48,48),
                                                    color_mode="grayscale",
                                                    batch_size=64,
                                                    class_mode='categorical',
                                                    shuffle=True)
validation_generator = validation_dataGenerator.flow_from_directory("test/",
                                                    target_size=(48,48),
                                                    color_mode="grayscale",
                                                    batch_size=64,
                                                    class_mode='categorical',
                                                    shuffle=False)

# part 4
# Initializing the CNN model
cnn_model = Sequential()

# 1 - Convolution
cnn_model.add(Conv2D(64,(3,3), padding='same', input_shape=(48, 48,1)))
cnn_model.add(BatchNormalization())
cnn_model.add(Activation('relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))
cnn_model.add(Dropout(0.25))

# 2nd Convolution layer
cnn_model.add(Conv2D(128,(5,5), padding='same'))
cnn_model.add(BatchNormalization())
cnn_model.add(Activation('relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))
cnn_model.add(Dropout(0.25))

# 3rd Convolution layer
cnn_model.add(Conv2D(512,(3,3), padding='same'))
cnn_model.add(BatchNormalization())
cnn_model.add(Activation('relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))
cnn_model.add(Dropout(0.25))

# 4th Convolution layer
cnn_model.add(Conv2D(512,(3,3), padding='same'))
cnn_model.add(BatchNormalization())
cnn_model.add(Activation('relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))
cnn_model.add(Dropout(0.25))

# Flattening
cnn_model.add(Flatten())

# Fully connected layer 1st layer
cnn_model.add(Dense(256))
cnn_model.add(BatchNormalization())
cnn_model.add(Activation('relu'))
cnn_model.add(Dropout(0.25))

# Fully connected layer 2nd layer
cnn_model.add(Dense(512))
cnn_model.add(BatchNormalization())
cnn_model.add(Activation('relu'))
cnn_model.add(Dropout(0.25))

cnn_model.add(Dense(7, activation='softmax'))

cnn_model.compile(loss='categorical_crossentropy', 
                  optimizer = Adam(lr=0.0005),  
                  metrics=['accuracy'])
# cnn_model.summary()

# part 6 - CNN model architecture
# plot_model(cnn_model, to_file='cnn_model.png', show_shapes=True, show_layer_names=True)
# Image('cnn_model.png',width=400, height=200)


# part 7 - Training and Evaluating CNN Model
steps_per_epoch = train_generator.n//train_generator.batch_size
validation_steps = validation_generator.n//validation_generator.batch_size

Model_reducelr = ReduceLROnPlateau(monitor='val_loss', 
                              factor=0.1,
                              patience=2, 
                              min_lr=0.00001, 
                              mode='auto')
Model_CP = ModelCheckpoint("cnn_modelWeights.h5", 
                             monitor='val_accuracy',
                             mode='max', 
                             save_weights_only = True, 
                             verbose=1)
callbacks = [PlotLossesCallback(), Model_CP, Model_reducelr]

history = cnn_model.fit(
    x = train_generator,
    steps_per_epoch = steps_per_epoch,
    epochs = 20,
    validation_data = validation_generator,
    validation_steps = validation_steps,
    callbacks=callbacks
)

# part 8 - CNN model to JSON
cnn_model_json = cnn_model.to_json()
with open("cnn_model.json", "w") as json_file:
    json_file.write(cnn_model_json)




######## Code to run facial expressions ###########
###################################################
###################################################

# part 9 - Class for loading cnn model & model weights
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


# part 10 - Get camera frames & make prediction
face_classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cnnmodel = FacialExpression("cnn_model.json", "cnn_modelWeights.h5")

class Webcam_Camera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    # Camera frames with bounding boxes and predictions
    def cameraframe(self):
        _, frame = self.video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            fc = gray[y:y+h, x:x+w]
            roi = cv2.resize(fc, (48, 48))
            pred = cnnmodel.expression_prediction(roi[np.newaxis, :, :, np.newaxis])
            cv2.putText(frame, pred, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
        return frame

# part 11 - Showing output video
def showcamera(camera):
    while True:
        frame = camera.cameraframe()
        cv2.imshow('Facial Expression Recognization',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

# part 12 - Running the code
showcamera(Webcam_Camera())