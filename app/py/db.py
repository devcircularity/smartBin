import mysql.connector
import uuid

# MySQL database credentials
db_config = {
    "host": "localhost",
    "user": "CirAdmin",
    "password": "CircularityIQ",
    "database": "cirDB"
}


def save_user_detected_count(user_detected_count):
    # Connect to the MySQL database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Update the most recent row in the detection table with the value of user_detected_count
    update_query = """
    UPDATE detection 
    SET user_id = %s
    WHERE no = (SELECT MAX(no) FROM detection)
    """
    cursor.execute(update_query, (user_detected_count,))
    connection.commit()

    # Close the cursor and connection
    cursor.close()
    connection.close()
    
def generate_token():
    # Generate a random token using UUID
    return str(uuid.uuid4())

async def check_user(input_value, token, count):
    # Modify the input_value by adding (+254) prefix
    modified_input_value = "254" + input_value[1:]

    # Connect to the MySQL database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Check if the modified input value exists in the phone_number column of the users table
    query = "SELECT * FROM users WHERE phone_number = %s"
    cursor.execute(query, (modified_input_value,))
    result = cursor.fetchone()

    # Update the most recent row in the detection table with the modified input value and count
    update_query = """
    UPDATE detection 
    SET phone_number = %s, sent_to_remote = '0', user_id = %s 
    WHERE no = (SELECT MAX(no) FROM detection)
    """
    cursor.execute(update_query, (modified_input_value, count))
    connection.commit()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Return the appropriate response along with the token
    if result:
        return f"[registered] (Token: {token})"
    else:
        return f"[not registered] (Token: {token})"

async def process_input(keyboard_input, token, count):
    # Check if the user is registered
    response = await check_user(keyboard_input, token, count)

    # Return the response
    return response
