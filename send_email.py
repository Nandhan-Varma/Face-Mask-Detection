import os 
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

email = "19951a05a1@iare.ac.in"
pswd = "@Nandhu!_8714"

def sendEmail(imgfile,receivermail,message):
    with open(imgfile,'rb') as f:
        img_data = f.read()
    
    msg = MIMEMultipart()
    msg['Subject'] = "Regarding Not Wearing Of Mask"
    msg['From'] = email
    msg['To'] = receivermail

    text = MIMEText(message)
    msg.attach(text)

    image = MIMEImage(img_data,name=os.path.basename(imgfile))
    msg.attach(image)

    with smtplib.SMTP("smtp.gmail.com",port=587) as server:
        server.starttls()
        server.login(email,pswd)
        server.sendmail(email, receivermail, msg.as_string())
        server.quit()

