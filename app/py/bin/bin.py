import serial
import select
import sys
import mysql.connector
import re
import socket

# MySQL database credentials
db_config = {
    "host": "localhost",
    "user": "CirAdmin",
    "password": "CircularityIQ",
    "database": "cirDB"
}

# Initialize the serial port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0)

# Initialize a buffer to store partial data from the Arduino
arduino_buffer = ""

# Connect to the MySQL database
db_conn = mysql.connector.connect(**db_config)
cursor = db_conn.cursor()

# Initialize the socket server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10000)
print('Starting up on', server_address)
sock.bind(server_address)
sock.listen(1)

# Wait for a connection
print('Waiting for a connection')
connection, client_address = sock.accept()

# Initialize variables to hold sensor data
weight, fill_level, fill_level_B = None, None, None

try:
    while True:
        # Check if data is available to read from the Arduino or stdin
        readable, _, _ = select.select([connection, ser, sys.stdin], [], [], 1)
        
        # If data is available from the Arduino, read it and print it
        if ser in readable:
            arduino_data = ser.read(ser.inWaiting()).decode('ascii')
            arduino_buffer += arduino_data
            
            # Check if we've received a complete line(s)
            while '\n' in arduino_buffer:
                line, arduino_buffer = arduino_buffer.split('\n', 1)
                line = line.strip()
                print(f"Received from Arduino: {line}")
                
                # Check the received message from Arduino and update the database
                if line == '[user]':
                    cursor.execute("UPDATE bin_data SET user_count = user_count + 1 WHERE no = (SELECT MAX(no) FROM bin_data)")
                    db_conn.commit()
                    
                elif 'Load Cell Value:' in line:
                    match = re.search(r':\s*([-]?\d+\.?\d*)', line)
                    if match:
                        weight = float(match.group(1))
                        print(f"Parsed Load Cell Value: {weight}")
                    else:
                        print(f"Could not parse Load Cell Value from: {line}")
                        
                elif 'New Ultrasonic Distance:' in line:
                    match = re.search(r':\s*([-]?\d+\.?\d*)', line)
                    if match:
                        fill_level = float(match.group(1))
                        print(f"Parsed New Ultrasonic Distance: {fill_level}")
                        
                elif 'Additional Ultrasonic Distance:' in line:
                    match = re.search(r':\s*([-]?\d+\.?\d*)', line)
                    if match:
                        fill_level_B = float(match.group(1))
                        print(f"Parsed Additional Ultrasonic Distance: {fill_level_B}")
                        
                    # Insert the values into a new row in the DB
                    if weight is not None and fill_level is not None and fill_level_B is not None:
                        print("Inserting new row into the DB...")
                        cursor.execute("INSERT INTO bin_data (total_weight, fill_level, fill_level_B) VALUES (%s, %s, %s)", (weight, fill_level, fill_level_B))
                        db_conn.commit()
                        print("New row inserted successfully.")
        
        # If data is available from the external script, read it and send it to Arduino
        if connection in readable:
            external_data = connection.recv(1024).decode('ascii').strip()
            if external_data:
                print(f"Received from External Script: {external_data}")
                ser.write(external_data.encode('ascii'))
                
        # If data is available from the keyboard (stdin), read it and send it to Arduino
        if sys.stdin in readable:
            user_input = input().strip()
            if user_input:
                ser.write(user_input.encode('ascii'))

except KeyboardInterrupt:
    print("Flushing and closing the serial port.")
    ser.flushInput()  # flush input buffer, discarding all its contents
    ser.flushOutput()  # flush output buffer, aborting current output
    ser.close()
    print("Closing the database connection.")
    db_conn.close()
    print("Closing the socket connection.")
    connection.close()
    print("Exiting the program.")

