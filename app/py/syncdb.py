import requests
import mysql.connector
import json
from datetime import datetime, date
import time
from flask import Flask, request, jsonify

# Custom JSON encoder class
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

# Remote Flask API endpoints
users_api_url = "http://cirdb.circularityspace.com/users"
detection_api_url = "http://cirdb.circularityspace.com/detection"
bindata_api_url = "http://cirdb.circularityspace.com/bindata"  # New API endpoint for bin data

# Local MariaDB database connection
local_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="CircularityIQ",
    database="cirDB"
)

# Create a cursor object to interact with the database
cursor = local_db.cursor()

# Create a Flask app
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

@app.route("/bindata", methods=["POST"])
def receive_bin_data():
    # Receive bin data from the remote API
    if request.method == "POST":
        bin_data = request.json

        # Extract the bin data from the request
        bin_id = bin_data.get("bin_id")  # Extract the bin_id field
        user_interaction = bin_data.get("user_interaction")
        item = bin_data.get("item")
        total_weight = bin_data.get("total_weight")
        fill_level = bin_data.get("fill_level")
        fill_level_B = bin_data.get("fill_level_B")  # New fill_level_B column
        time_stamp = bin_data.get("time_stamp")

        # Convert the time_stamp to a datetime object
        time_stamp = datetime.fromisoformat(time_stamp) if time_stamp else None

        # Insert the bin data into the local database
        try:
            insert_query = "INSERT INTO bin_data (bin_id, user_interaction, item, total_weight, fill_level, fill_level_B, time_stamp, sent_to_remote) " \
                           "VALUES (%s, %s, %s, %s, %s, %s, %s, 0)"  # Set the 'sent_to_remote' column to 0
            insert_values = (bin_id, user_interaction, item, total_weight, fill_level, fill_level_B, time_stamp)
            cursor.execute(insert_query, insert_values)
            local_db.commit()
            return jsonify({"message": "Bin data received and stored successfully"})
        except mysql.connector.Error as e:
            return jsonify({"message": f"Error: Failed to insert bin data into the local database. {str(e)}"})

    return jsonify({"message": "Invalid request"})

# Infinite loop
while True:
    try:
        # Fetch data from the remote "users" API
        response = requests.get(users_api_url)
        if response.status_code == 200:
            try:
                users_data = response.json()
            except json.JSONDecodeError as e:
                print("Error: Failed to parse JSON response from the remote 'users' API.")
                print("Response content:", response.content)
                continue

            # Iterate over the fetched users' data and insert it into the local database
            for user in users_data:
                first_name = user["first_name"]
                last_name = user["last_name"]
                phone_number = user["phone_number"]

                # SQL query to check if the phone_number already exists in the local database
                select_query = f"SELECT * FROM users WHERE phone_number = '{phone_number}'"

                # Execute the select query
                cursor.execute(select_query)

                # Fetch the result
                result = cursor.fetchall()

                # If the user does not exist (result is empty), insert it into the local database
                if not result:
                    # SQL query to insert data into the local database
                    insert_query = f"INSERT INTO users (first_name, last_name, phone_number) VALUES ('{first_name}', '{last_name}', '{phone_number}')"

                    # Execute the insert query
                    cursor.execute(insert_query)

            # Commit the changes to the local database
            local_db.commit()

        else:
            print("Error: Failed to fetch users' data from the remote API. Status code:", response.status_code)

    except requests.exceptions.RequestException as e:
        print("Error: Failed to fetch users' data from the remote API.", str(e))


    try:
        # Fetch detection data from the local database
        select_query = "SELECT * FROM detection WHERE sent_to_remote = 0"  # Add a condition to fetch only unsent entries
        cursor.execute(select_query)
        result = cursor.fetchall()  # Fetch the result

        # Iterate over the fetched detection data and send it to the remote API
        for detection in result:
            bin_id = detection[1]  # Add bin_id field
            object_name = detection[2]
            confidence = detection[3]
            timestamp = detection[4]
            user_id = detection[5]
            phone_number = detection[6]

            # Convert the timestamp to a string if it's a datetime object
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Prepare the payload for the detection API request
            payload = {
                "bin_id": bin_id,  # Add bin_id field
                "object_name": object_name,
                "confidence": confidence,
                "timestamp": timestamp,
                "user_id": user_id,
                "phone_number": phone_number
            }

            # Send the detection data to the remote API
            response = requests.post(detection_api_url, data=json.dumps(payload, cls=CustomJSONEncoder), headers={'Content-Type': 'application/json'})

            if response.status_code == 200:
                # Update the sent_to_remote flag for the sent entry
                update_query = "UPDATE detection SET sent_to_remote = 1 WHERE no = %s"  # Update the query to use 'no' column
                update_value = (detection[0],)  # Use the 'no' column value as update value
                cursor.execute(update_query, update_value)
                local_db.commit()
                print("Detection data sent successfully:", payload)
            else:
                print("Error: Failed to send detection data. Status code:", response.status_code)

    except mysql.connector.Error as e:
        print("Error: Failed to fetch detection data from the local database.", str(e))

    try:
        # Fetch bin_data from the local database
        select_query = "SELECT * FROM bin_data WHERE sent_to_remote = 0"  # Add a condition to fetch only unsent entries
        cursor.execute(select_query)
        result = cursor.fetchall()  # Fetch the result

        # Iterate over the fetched bin_data and send it to the remote API
        for bin_item in result:
            user_interaction = bin_item[1]
            item = bin_item[2]
            total_weight = bin_item[3]
            fill_level = bin_item[4]
            fill_level_B = bin_item[5]  # New fill_level_B column
            time_stamp = bin_item[6]
            bin_id = bin_item[0]  # Extract bin_id from the bin_item

            # Convert the time_stamp to a string if it's a datetime object
            if isinstance(time_stamp, datetime):
                time_stamp = time_stamp.strftime("%Y-%m-%d %H:%M:%S")

            # Prepare the payload for the bin data API request
            bin_payload = {
                "bin_id": bin_id,  # Add bin_id field
                "user_interaction": user_interaction,
                "item": item,
                "total_weight": total_weight,
                "fill_level": fill_level,
                "fill_level_B": fill_level_B,
                "time_stamp": time_stamp
            }

            # Send the bin data to the remote API
            response = requests.post(bindata_api_url, data=json.dumps(bin_payload, cls=CustomJSONEncoder), headers={'Content-Type': 'application/json'})

            if response.status_code == 200:
                # Update the sent_to_remote flag for the sent entry
                update_query = "UPDATE bin_data SET sent_to_remote = 1 WHERE no = %s"  # Update the query to use 'no' column
                update_value = (bin_item[0],)  # Use the 'no' column value as update value
                cursor.execute(update_query, update_value)
                local_db.commit()
                print("Bin data sent successfully:", bin_payload)
            else:
                print("Error: Failed to send bin data. Status code:", response.status_code)

    except mysql.connector.Error as e:
        print("Error: Failed to fetch bin data from the local database.", str(e))

    # Wait for a certain period of time before fetching data again
    time.sleep(60)  # Sleep for 60 seconds

# Close the database connection (This line won't be reached as the script runs indefinitely)
local_db.close()
