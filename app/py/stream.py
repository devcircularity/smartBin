import subprocess
import os
import mysql.connector
import aiohttp
import asyncio

# MySQL database credentials
db_config = {
    "host": "localhost",
    "user": "CirAdmin",
    "password": "CircularityIQ",
    "database": "cirDB"
}

def record_video(output_path, duration):
    command = [
        'ffmpeg', '-t', str(duration),
        '-f', 'v4l2',
        '-framerate', '1',
        '-video_size', '640x480',
        '-i', '/dev/video0',
        '-c:v', 'libx264',  # using H.264 codec
        '-preset', 'fast',  # Use a preset. 'fast' gives a good balance of speed and quality. Adjust as needed.
        '-pix_fmt', 'yuv420p',  # ensures maximum compatibility
        output_path
    ]
    subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def upload_video(video_path, upload_url):
    async with aiohttp.ClientSession() as session:
        with open(video_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('video', f, filename=os.path.basename(video_path), content_type='video/mp4')
            async with session.post(upload_url, data=data) as response:
                if response.status == 200:
                    print("Video uploaded successfully.")
                else:
                    print("Error uploading video. Status code:", response.status)
                    print("Error message:", await response.text())

async def check_results(result_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(result_url) as response:
            result = await response.json()
            # ... [Your existing code here]
            if 'results' in result:
                if result['results']['status'] == '[Approved]':
                    send_message_to_main("[electronic]")
                    write_to_database("Approved", result['results']['objects'])
                    
                elif result['results']['status'] == '[Not Approved]':
                    send_message_to_main("[not-electronic]")
                    write_to_database("Not Approved", [])
                   
                else:
                    print('Invalid result:', result['results'])
            else:
                print('Invalid response:', result)

def send_message_to_main(message):
    # Code to send the message to main.py
    print(message)

def write_to_database(object_name, identified_objects):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Set bin_id to "cir_office" if not provided
        bin_id = "cir_office"

        # Insert the detection result into the "detection" table
        sql = "INSERT INTO detection (bin_id, object_name, confidence) VALUES (%s, %s, %s)"
        values = (bin_id, object_name, ', '.join(identified_objects))
        cursor.execute(sql, values)
        connection.commit()

        print("Successfully wrote to the database.")

    except mysql.connector.Error as error:
        print("Error writing to the database:", error)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


async def main():
    output_directory = '/home/cir/Documents/records/'
    output_filename = 'output.mp4'
    output_path = os.path.join(output_directory, output_filename)
    upload_url = 'http://ciriq.circularityspace.com/upload-video'
    result_url = 'http://ciriq.circularityspace.com/get-results'  # Endpoint to retrieve the results
    record_duration = .30  # 5 seconds

    record_video(output_path, record_duration)
    await upload_video(output_path, upload_url)
    await check_results(result_url)
    os.remove(output_path)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
