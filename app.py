import os
from flask import Flask, render_template, Response,request,redirect
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import load_img,img_to_array
import yaml
from urllib.request import Request
import urllib
import cv2
import pywhatkit

from camera import Video
from send_email import sendEmail

app = Flask(__name__)

db = yaml.full_load(open('Application/database.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

uploadFolder = "G:/Mask Detection using flask/Uploads"

model = "F:/Project_Data/MobileNetV2.model"

global loggedInUsers
loggedInUsers = []

# model = "F:/Project_Data/mask_detector_check_50epoch"
# model = "C:/Users/HP/Downloads/MobileNetV250.model"

pretrained_model = load_model(model)

classes = {0:"Mask",1:"No Mask"}

def predict_image_class(img_path,model):

    img = load_img(img_path,target_size=(224,224))
    img = img_to_array(img)
    img = img/255
    image = np.expand_dims(img,axis=0)

    result = np.argmax(model.predict(image))
    prediction = classes[result]

    return prediction


@app.route('/')
def home():
    """Video streaming home page."""
    return render_template('homepage.html')

@app.route('/logon',methods=('GET','POST'))
def signupscreen():
    return render_template('Signup.html')

@app.route('/login')
def signinscreen():
    return render_template('Signin.html')

@app.route('/signup',methods=('GET','POST'))
def getData():
    if request.method == "POST":
        userDetails = request.form
        uname = userDetails['user']
        uemail = userDetails['usermail']
        upswd = userDetails['password']
        ucnfpswd = userDetails['cnfpassword']
        uphno = userDetails['phone']
        cur = mysql.connection.cursor()
        cur2 = mysql.connection.cursor()
        # cur.execute('INSERT INTO user(username,mailid,pswd,phno) VALUES (%s,%s,%s,%s)',(uname,uemail,upswd,uphno))
        cur.execute("SELECT * FROM user where (username = %s)",[uname])
        cur2.execute("SELECT * FROM user where (phno = %s)",[uphno])
        result = cur.fetchone()
        result2 = cur2.fetchone()
        if result:
            return render_template('existinguser.html')
        elif result2:
            return render_template('existingphonenumber.html')
        else:
            cur.execute('INSERT INTO user(username,mailid,pswd,phno) VALUES (%s,%s,%s,%s)',(uname,uemail,upswd,uphno))
            mysql.connection.commit()
            cur.close()
            print(request.form)
        return render_template('Signin.html')
    else:
        return "Method Falied"

@app.route('/signin',methods=('GET','POST'))
def redirect():
    if request.method == "POST":
        details = request.form
        user_name = details['username']
        password = details['pwd']
        cur = mysql.connection.cursor()
        cur2 = mysql.connection.cursor()
        cur.execute('SELECT * FROM user where username = %s and pswd = %s',(user_name,password))
        cur2.execute("SELECT pswd FROM user where (username = %s)",[user_name])
        result = cur.fetchone()
        print(result)
        result2 = cur2.fetchone()
        if result == None:
            return render_template('usernotexist.html')
        elif result and result2[0] == password:
            username = result[1]
            loggedInUsers.append(username)
            print(loggedInUsers)
            return render_template('index.html')
        else:
            return render_template('wrongpassword.html')

print(loggedInUsers)

@app.route('/main-index',methods=('GET','POST'))
def options():
    return render_template('index.html') 

@app.route('/takeimage',methods=('GET','POST'))
def capture_image():
    camera = cv2.VideoCapture(0)
    _,frame = camera.read()
    filename = "capture.png"
    cv2.imwrite("webacpture.jpg",frame)
    camera.release()
    
    img_file_path = "G:\Mask Detection using flask\webacpture.jpg"
    result = predict_image_class(img_file_path, pretrained_model)
    if result == "Mask":
        return render_template('wearingmask.html')
    else:
        if loggedInUsers:
            lastuser = loggedInUsers[-1]
            cur = mysql.connection.cursor()
            cur.execute("SELECT mailid FROM user WHERE (username = %s)",[lastuser])
            result = cur.fetchone()
            receivermail = str(result[0])
            message = "Hi {} Hope You Are Doing Well. It Is Found That You Are Not Wearing The Mask In The Premises. Please Wear The Mask To Protect From The Respiratory Diseases.".format(lastuser)
            sendEmail(img_file_path,receivermail,message)
            return "Mail Sent SuccessFully"
        else:
            return "Error Occured"
        
@app.route('/uploadfile',methods=('GET','POST'))
def upload_image():
    print("File Upload Function is enabled")
    file = request.files['files']
    filename = file.filename
    print("Image Uploaded {}".format(filename))

    file_path = os.path.join(uploadFolder,filename)
    file.save(file_path)

    print("Predicting Class")

    pred = predict_image_class(file_path, pretrained_model)

    if pred == "Mask":
        return render_template('wearingmask2.html')
    else:
        if loggedInUsers:
            lastuser = loggedInUsers[-1]
            cur = mysql.connection.cursor()
            cur.execute("SELECT phno FROM user where (username = %s)",[lastuser])
            result = cur.fetchone()
            requiredNumber = "+91"+result[0]
            message = "Hi {} Hope You Are Doing Well. As It Is Noticed That You Are Not Wearing A Mask.Please Wear Mask For Better Health.".format(lastuser)
            pywhatkit.sendwhatmsg_instantly(requiredNumber, message)
            return "Message Has Sent Successfully"
        else:
            return "Error Occured"

def gen_frames(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/live-cam',methods=('GET','POST'))
def live_capture():
    return Response(gen_frames(Video()),mimetype='multipart/x-mixed-replace; boundary=frame')




if __name__ == "__main__":
    app.run(debug=True)