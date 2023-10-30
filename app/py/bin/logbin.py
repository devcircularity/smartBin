import socket
import time

# Connect to the main script
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10000)
sock.connect(server_address)

try:
    while True:
        # Open the text file to read lines
        with open("/home/cir/Documents/app/py/bin/bin.txt", "r+") as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()  # Clear the file to write modified lines back
            
            for line in lines:
                # Check if the line is not already commented out
                if line.strip().startswith("#"):
                    file.write(line)  # Write the commented line back to file
                    continue
                
                if "[Verified Object]" in line.strip():
                    print("Verified Object found. Sending to main script.")
                    sock.sendall("[Verified Object]".encode('ascii'))
                    line = "#" + line  # Comment out the line
                
                file.write(line)  # Write the modified line back to file
        
        # Wait for a while before checking the file again
        time.sleep(1)

except KeyboardInterrupt:
    print("Closing the program.")
    sock.close()
