import socket
import time
import os
import subprocess



# Helper function to write to bin.txt, ensuring new lines
def write_to_bin(content):
    with open(bin_file_path, 'a+') as file:
        # Check if the file is empty, if not, prepend with newline
        file.seek(0)  # move cursor to the start of the file
        data = file.read(100)  # read the first 100 characters
        if len(data) > 0:
            content = '\n' + content
        file.write(content)

# Get the current directory path
current_directory = os.path.dirname(os.path.abspath(__file__))

# Example usage:
if __name__ == "__main__":
    prompt_list = ['screen1', 'screen2', 'screen3', 'screen4', 'keypad']

    # Define bin_file_path
    bin_file_path = os.path.join(current_directory, 'bin', 'bin.txt')

    # Launch syncdb.py
    syncdb_path = os.path.join(current_directory, 'syncdb.py')
    syncdb_process = subprocess.Popen(['python', syncdb_path])

    # Launch db.py
    db_path = os.path.join(current_directory, 'db.py')
    db_process = subprocess.Popen(['python', db_path])


    while True:

        # Read all lines from bin.txt
        with open(bin_file_path, 'r') as file:
            lines = file.readlines()

        # Get the last line from the file (if any)
        last_line = lines[-1].strip() if lines else ''

        if '[user detected]' in last_line:
            # Run stream.py without passing the token
            print('Running stream.py')
            stream_path = os.path.join(current_directory, 'stream.py')
            output = subprocess.Popen(['python', stream_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for stdout_line in iter(output.stdout.readline, b''):
                output_text = stdout_line.decode().strip()
                print('Received from stream.py:', output_text)

                if output_text == '[electronic]':
                    write_to_bin('[Verified Object]')
                    print('Written to bin.txt: [Verified Object]')

                elif output_text == '[not-electronic]':
                    write_to_bin('[Not Verified Object]')
                    print('Written to bin.txt: [Not Verified Object]')
                    write_to_bin('[not electronic]')
                    print('Written to bin.txt: [not electronic]')


        # Add a delay before checking for new data in bin.txt
        time.sleep(0.1)
