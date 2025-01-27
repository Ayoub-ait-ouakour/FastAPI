import os
import base64
import replicate
import sqlite3
from dotenv import load_dotenv
import requests
import time
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

"""
This variable stores the API token for the Replicate service.
"""
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN") 


def save_video(video_data):
    conn = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/videos.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY, video_data BLOB)")
    cur.execute("INSERT INTO videos (video_data) VALUES (?)", (video_data,))
    conn.commit()
    conn.close()

def get_video(image_data, audio_data=None, audio_link=None):
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    
    audio_data = None
    # # Convert image and audio data to base64 encoded data URI
    image_data_uri = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
    if audio_data: 
        audio_data_uri = f"data:audio/wav;base64,{base64.b64encode(audio_data).decode()}"
    if audio_link:
        audio_data_uri = audio_link
        
    input={
        "source_image": image_data_uri,
        "driven_audio": audio_data_uri,
        "preprocess": "full",
        "use_enhancer": True,
        "use_eyeblink": True,
    }
    prediction_ = client.predictions.create(
        version="a519cc0cfebaaeade068b23899165a11ec76aaa1d2b313d40d214f204ec957a3",
        input=input
    )
    
    # list predictions 
    predictions = client.predictions.list()
    # get latest prediction
    prediction = predictions[0]
    print("predictions", predictions)
    
    while True:
        # Get the latest prediction status
        prediction = client.predictions.get(prediction.id)
        
        # Check if the prediction is complete
        if prediction.status == "succeeded":
            output = requests.get(prediction.output)
            video_data = output.content
            save_video(video_data)
            return video_data
        elif prediction.status == "failed":
            raise TimeoutError("Prediction failed")
        
        # Wait for 30 seconds before checking again
        time.sleep(5)
    


def save_picture(image_data):
    conn = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/videos.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS pictures (id INTEGER PRIMARY KEY, image_data TEXT)")
    cur.execute("INSERT INTO pictures (image_data) VALUES (?)", (base64.b64encode(image_data).decode(),))
    conn.commit()
    conn.close()

def get_picture(picture_id):
    conn = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/videos.db")
    cur = conn.cursor()
    cur.execute("SELECT image_data FROM pictures WHERE id = ?", (picture_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return base64.b64decode(result[0])
    return None

def get_saved_video(video_id):
    conn = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/videos.db")
    cur = conn.cursor()
    cur.execute("SELECT video_data FROM videos WHERE id = ?", (video_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def list_saved_videos():
    conn = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/videos.db")
    cur = conn.cursor()
    cur.execute("SELECT id, video_data FROM videos")
    videos = cur.fetchall()
    conn.close()
    return videos

def list_saved_images():
    conn = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/videos.db")
    cur = conn.cursor()
    cur.execute("SELECT id, image_data FROM pictures")
    images = cur.fetchall()
    conn.close()
    return images

def generate_audio_from_script(script):
    # TODO: Implement logic to generate audio from script
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    input={
        "text": script,
        "speaker": "https://replicate.delivery/pbxt/Jt79w0xsT64R1JsiJ0LQRL8UcWspg5J4RFrU6YwEKpOT1ukS/male.wav",
        "language": "en",
        "cleanup_voice": False
    }
    
    prediction_ = client.predictions.create(
        version="684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
        input=input
    )
    
    
    while True:
        # Get the latest prediction status
        prediction = client.predictions.get(prediction_.id)
        
        # Check if the prediction is complete
        if prediction.status == "succeeded":
            return prediction.output
        
        elif prediction.status == "failed":
            raise TimeoutError("Prediction failed")

        time.sleep(5)
        
def get_video_from_script(image_data, script): 

    audio_link = generate_audio_from_script(script)
    print(audio_link)
    video_data = get_video(image_data=image_data, audio_link=audio_link)
    return video_data
    