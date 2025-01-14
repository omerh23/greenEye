import datetime
import io
import re
import tempfile
import base64
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import UploadFile, File, APIRouter, HTTPException
import numpy as np
from io import BytesIO
from PIL import Image
from pymongo import MongoClient
from authentication import get_current_user
from yolo.yolo import classify
import os
from cloudinary.uploader import upload
import cloudinary
from pydantic import BaseModel
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import cv2
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("./private.json")
firebase_admin.initialize_app(cred)

scheduler = AsyncIOScheduler()

load_dotenv()
router = APIRouter()
mongodb_url = os.getenv("MONGODB_URL")
db_url = os.getenv("DB")
cluster = MongoClient(mongodb_url)
cluster_url = os.getenv("CLUSTER")
db = cluster[cluster_url]
algo = os.getenv("ALGO")
collection = db[db_url]

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)


@router.get("/ping")
async def ping():
    return "Hello, I am alive"


@router.get("/")
async def run():
    return "Server Running"


def read_file_as_image(data) -> np.ndarray:
    image = np.array(Image.open(BytesIO(data)))
    return image


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = read_file_as_image(await file.read())
    predTuple = classify(image)

    return predTuple


def load_image_to_array(image_path):
    # Open the image file
    with Image.open(image_path) as img:
        # Convert the image to RGB (if not already in this format)
        img = img.convert('RGB')

        # Convert the image to a NumPy array
        img_array = np.array(img)

        return img_array


def upload_image_to_cloudinary(image_path):
    response = cloudinary.uploader.upload(image_path)
    return response


class ImageData(BaseModel):
    imageUri: str
    token: str


@router.post("/manualCapture")  # manual capture of broadcast camera
async def receive_image(data: ImageData):
    try:
        userId = ObjectId(get_current_user(data.token))
        header, encoded = data.imageUri.split(",", 1)
        image_data = base64.b64decode(encoded)

        # Use a temporary file to upload to Cloudinary
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as file:
            file.write(image_data)
            file_path = file.name

        image = np.array(Image.open(BytesIO(image_data)))
        predTuple = classify(image)

        # name = input("Enter image name: ")
        # image_path = rf'C:\Users\omerh\PycharmProjects\GreenEye\mobile\images\{name}.jpg'
        #
        # array = load_image_to_array(image_path)
        # upload_response = upload_image_to_cloudinary(image_path)
        #
        # predTuple = classify(array)

        result = predTuple
        if predTuple['confidence'] > 50 and predTuple['label'] == 'Sick':
            # Upload to Cloudinary
            response = upload(file_path, folder="your_folder_name")  # specify your folder name
            image_url = response.get("url")
            os.remove(file_path)

            result = uploadImageToDatabase(userId, image_url, predTuple, "manual")

        return result

    except HTTPException:
        return {"status":"Unknown Error"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


class obj:
    def __init__(self, url, description, uploaded):
        self.url = url
        self.description = description
        self.uploaded = uploaded




@router.post("/latestHistory")
async def receive_image(data: dict):
    try:
        userId = ObjectId(get_current_user(data["token"]))
        existing_user = collection.find_one({"_id": userId})

        latestHistory = []
        for image_info in existing_user['images']:
            image_url = image_info['url']
            response = requests.get(image_url)

            if response.status_code == 200:
                base64_image = base64.b64encode(response.content).decode('utf-8')
                latestHistory.append({
                    'url': f"data:image/jpeg;base64,{base64_image}",
                    'description': image_info['description'],
                    'uploaded': image_info['uploaded']
                })
            else:
                print("Failed to download the image")

        return latestHistory

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


@router.post('/automaticDetectionHistory')
async def automaticDetection(data: dict):
    try:
        userId = ObjectId(get_current_user(data["token"]))
        existing_user = collection.find_one({"_id": userId})

        latestHistory = []
        for image_info in existing_user['images']:

            if image_info['isAutomatic']:
                image_url = image_info['url']
                response = requests.get(image_url)
                if response.status_code == 200:
                    base64_image = base64.b64encode(response.content).decode('utf-8')
                    latestHistory.append({
                        'url': f"data:image/jpeg;base64,{base64_image}",
                        'description': image_info['description'],
                        'uploaded': image_info['uploaded']
                    })
                else:
                    print("Failed to download the image")

        return latestHistory

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


@router.post('/manualDetectionHistory')
async def manualDetection(data: dict):
    try:
        userId = ObjectId(get_current_user(data["token"]))
        existing_user = collection.find_one({"_id": userId})

        manualHistory = []
        for image_info in existing_user['images']:

            if image_info['isManual']:
                image_url = image_info['url']
                response = requests.get(image_url)
                if response.status_code == 200:
                    base64_image = base64.b64encode(response.content).decode('utf-8')
                    manualHistory.append({
                        'url': f"data:image/jpeg;base64,{base64_image}",
                        'description': image_info['description'],
                        'uploaded': image_info['uploaded']
                    })
                else:
                    print("Failed to download the image")

        return manualHistory

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


@router.post('/changeDetails')
async def changeDetails(data: dict):
    try:
        if not all(data.values()):
            return {"status": "empty_fields"}

        userId = ObjectId(get_current_user(data["token"]))
        existing_user = collection.find_one({"_id": userId})

        existing_mail = collection.find_one({"email": data['email']})

        if existing_mail and data['email'] != existing_user['email']:
            return {"status": "email_already_registered"}

        userId = ObjectId(get_current_user(data["token"]))
        existing_user = collection.find_one({"_id": userId})

        old_password = data['oldPassword'].encode('utf-8')
        if not bcrypt.checkpw(old_password, existing_user['password'].encode('utf-8')):
            return {"status": "wrong_old_password"}

        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, data['email']):
            return {"status": "invalid_email"}

        if not len(data['newPassword']) > 5:
            return {"status": "short_password"}

        new_hashed_password = bcrypt.hashpw(data['newPassword'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_result = collection.update_one(
            {"_id": userId},
            {"$set": {
                "username": data['username'],
                "email": data['email'],
                "password": new_hashed_password,
                "cameraUrl": data['cameraUrl']
            }}
        )

        if update_result.modified_count == 0:
            return {"message": "Failed to update the database"}

        updated_user = collection.find_one({"_id": userId})
        updated_user['_id'] = str(existing_user['_id'])
        return {"status": "success", "user": updated_user}

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


@router.post("/selfCamera")
async def receive_image(data: dict):
    try:
        userId = ObjectId(get_current_user(data['token']))
        encoded_image = data['base64Image']
        image_data = base64.b64decode(encoded_image)

        # name = input("Enter image name: ")
        # image_path = rf'C:\Users\omerh\\Desktop\images\{name}.jpg'
        # array = load_image_to_array(image_path)
        # upload_response = upload_image_to_cloudinary(image_path)
        # image_url = upload_response.get("url")
        # predTuple = classify(array)

        if data['broadcastCamera']: #if its broadcast camera dont rotate
            angle = 0
        else:
            angle = -90

        image = Image.open(io.BytesIO(image_data))
        rotated_image = image.rotate(angle, expand=True)
        buffer = io.BytesIO()
        if rotated_image.mode == 'RGBA':
            rotated_image = rotated_image.convert('RGB')

        rotated_image.save(buffer, format="JPEG")
        # image.save(buffer, format="JPEG")
        buffer.seek(0)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as file:
            file.write(buffer.read())
            file_path = file.name

        rotateImg = np.array(rotated_image)
        predTuple = classify(np.array(rotateImg))

        result = predTuple
        if predTuple['confidence'] > 20 and predTuple['label'] == 'Sick':
            # Upload to Cloudinary
            response = upload(file_path, folder="your_folder_name")  # specify your folder name
            image_url = response.get("url")
            os.remove(file_path)

            result = uploadImageToDatabase(userId, image_url, predTuple, "manual")

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


def capture_frame(camera_url):
    # Connect to the camera using OpenCV
    cap = cv2.VideoCapture(camera_url)

    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera")
        return None

    # Read a frame from the camera
    ret, frame = cap.read()

    # Release the VideoCapture object
    cap.release()

    if ret:
        # Frame captured successfully
        return frame
    else:
        print("Error: Could not read frame")
        return None


def identificationExplore():
    try:
        for user in collection.find():
            cameraUrl = user['cameraUrl']
            if cameraUrl != 'None':
                frame = capture_frame(cameraUrl)
                predTuple = classify(frame)
                if predTuple['label'] != 'No identify' and predTuple['label'] == 'Sick':
                    # if predTuple['confidence'] > 20:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as file:
                        file_path = file.name
                    # Write frame to the temporary file using OpenCV
                    cv2.imwrite(file_path, frame)

                    # Upload to Cloudinary
                    response = upload(file_path, folder="your_folder_name")  # specify your folder name
                    image_url = response.get("url")
                    os.remove(file_path)

                    update_result = collection.update_one(
                        {"_id": user['_id']},
                        {
                            "$push": {
                                "images": {
                                    "url": image_url,
                                    # "url": upload_response['url'],
                                    "description": f"Result: {predTuple['label']}, confidence: {predTuple['confidence']}%",
                                    "uploaded": datetime.date.today().isoformat(),
                                    "isManual": False,
                                    "isAutomatic": True
                                }
                            }
                        }
                    )

                    if update_result.modified_count == 0:
                        return {"message": "Failed to update the database"}
                    else:
                        print(f"success with user {user['username']}")

                        # Send Notification
                        fcm_token = user['fcmToken']
                        if fcm_token:
                            # Create a message for FCM
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title="Alert",
                                    body=f"Result: {predTuple['label']}, confidence: {predTuple['confidence']}%"
                                ),
                                token=fcm_token
                            )

                            # Send the message
                            response = messaging.send(message)
                            print('Successfully sent message:', response)
                        else:
                            print(f"No FCM token for user {user['username']}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


def uploadImageToDatabase(userId, imageUrl, predTuple, detectionType):
    isManual = False
    isAuto = False
    if detectionType == "manual":
        isManual = True
    if detectionType == "auto":
        isAuto = True

    update_result = collection.update_one(
        {"_id": userId},
        {
            "$push": {
                "images": {
                    "$each": [{
                        "url": imageUrl,
                        "description": f"Result: {predTuple['label']}, confidence: {predTuple['confidence']}%",
                        "uploaded": datetime.date.today().isoformat(),
                        "isManual": isManual,
                        "isAutomatic": isAuto
                    }],
                    "$slice": -30
                }
            }
        }
    )

    if update_result.modified_count == 0:
        return {"message": "Failed to update the database"}
    else:
        return predTuple


@router.on_event("startup")
async def start_scheduler():
    # Schedule the function to run every 5 seconds
    #scheduler.add_job(identificationExplore, 'interval', hours=3)
    scheduler.add_job(identificationExplore, 'interval', seconds=180)
    scheduler.start()
