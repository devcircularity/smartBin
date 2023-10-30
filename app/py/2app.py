import pygame
import os
import time
import threading
import requests
import db
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



os.environ['SDL_VIDEO_WINDOW_POS'] = "center"
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Initialize Pygame
pygame.init()

# Lock to avoid race condition
file_lock = threading.Lock()

# Constants
WIDTH, HEIGHT = 480, 800
BIN_FILE_PATH = "/home/cir/Documents/app/py/bin/bin.txt"
KEYBOARD_LAYOUT = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["del", "0", "enter"],
]

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (192, 192, 192)
BLUE_RED = (128, 0, 128)  # Halfway between pure red and pure blue


os.makedirs(os.path.dirname(BIN_FILE_PATH), exist_ok=True)
os.makedirs("images", exist_ok=True)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("E-Waste App")

image_urls = [
    "https://api.circularityspace.com/preload/1.jpg",
    "https://api.circularityspace.com/preload/4.jpg",
    "https://api.circularityspace.com/preload/3.jpg",
    "https://api.circularityspace.com/preload/2.jpg",
]

font = pygame.font.Font(None, 36)
user_detected_count = 0

#user_detected_count = 0
def write_to_bin_file(data):
    global user_detected_count  # Add this line
    with open(BIN_FILE_PATH, "a") as f:
        f.write(data)
    if "[user detected]" in data:
        user_detected_count += 1



def read_last_line_from_bin_file():
    with open(BIN_FILE_PATH, "r") as file:
        lines = file.readlines()
        if lines:
            return lines[-1].strip()  # Return the last line, without any trailing whitespace
        else:
            return None

        
        
def should_switch_due_to_inactivity(last_activity_time, timeout_duration=30000):
    if last_activity_time:
        return pygame.time.get_ticks() - last_activity_time > timeout_duration
    return False


def scale_image(image, target_width, target_height):
    return pygame.transform.scale(image, (target_width, target_height))

def draw_3d_button(text, x, y, width, height, active=False, shadow_offset=4):
    button_color = GRAY if active else BLACK
    text_color = BLACK if active else WHITE
    pygame.draw.rect(screen, button_color, (x, y, width, height))
    button_text = font.render(text, True, text_color)
    button_rect = button_text.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(button_text, button_rect)

def draw_error_message(message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, True, WHITE)
    
    # Position the error message just above the keyboard
    rect = text.get_rect(center=(WIDTH / 2, 250))
    
    # Draw a BLUE_RED background behind the text
    pygame.draw.rect(screen, BLUE_RED, rect.inflate(20, 20))
    
    # Display the error text
    screen.blit(text, rect)


def handle_keyboard_input(event, keyboard_input, keyboard_buttons):
    global show_error, error_start_time, last_key_press_time, user_detected_count
    if event.type == pygame.MOUSEBUTTONDOWN:
        last_key_press_time = pygame.time.get_ticks()  # Update the last key press time when a virtual key is pressed
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            for button_text, button_rect in keyboard_buttons:
                if button_rect.collidepoint(x, y):
                    key = button_text
                    if key == "del":
                        keyboard_input = keyboard_input[:-1]
                    elif key == "enter":
                        if len(keyboard_input) < 10:
                            show_error = True
                            error_start_time = pygame.time.get_ticks()
                            # Send the user_detected_count to db.py
                            db.save_user_detected_count(user_detected_count)
            
                            # Reset the user_detected_count for the next cycle
                            user_detected_count = 0
                        elif len(keyboard_input) == 10:
                            # Generate a new token
                            token = db.generate_token()
                            # Asynchronously process the input value with the token
                            loop = asyncio.get_event_loop()
                            response = loop.run_until_complete(db.process_input(keyboard_input, token, user_detected_count))
                            # Send the user_detected_count to db.py
                            db.save_user_detected_count(user_detected_count)
                            # Reset the user_detected_count for the next cycle
                            user_detected_count = 0
                            # Display the success message and wait for 5 seconds
                            draw_success_message()
                            pygame.display.flip()
                            pygame.time.wait(5000)  # Wait for 5 seconds
                            #print("Phone number sent to DB:", keyboard_input)
                            return "", 0  # Here, current_screen is set to 0 to take the user back to the initial screen
                    else:
                        keyboard_input += key
                    return keyboard_input, 4
    return keyboard_input, 4




# Global Variables
show_error = False
error_start_time = None

def draw_keyboard_input_display(input_text):
    # y-coordinate changed to 150 to move display up
    input_display_rect = pygame.Rect(40, 150, 400, 50)
    
    pygame.draw.rect(screen, BLACK, input_display_rect)
    
    # centering text horizontally and vertically
    text = font.render(input_text, True, WHITE)
    text_rect = text.get_rect(center=input_display_rect.center)
    
    screen.blit(text, text_rect)


last_activity_time = None  # New global variable to track the last activity

def draw_success_message():
    font = pygame.font.Font(None, 50)
    
    # First message
    message1 = "Successful"
    text1 = font.render(message1, True, WHITE)
    rect1 = text1.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30))  # Position slightly above the center
    
    # Second message
    message2 = "Welcome to Weee Centre!"
    text2 = font.render(message2, True, WHITE)
    rect2 = text2.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 30))  # Position slightly below the center

    # Drawing the background for the messages
    combined_rect = rect1.union(rect2).inflate(20, 40)
    pygame.draw.rect(screen, BLUE_RED, combined_rect)

    # Displaying the messages
    screen.blit(text1, rect1)
    screen.blit(text2, rect2)


def reset_activity_timers(last_activity_time, screen2_last_activity_time, screen3_last_activity_time):
    """Reset all activity-related timers."""
    last_activity_time = pygame.time.get_ticks()
    screen2_last_activity_time = None
    screen3_last_activity_time = None
    return last_activity_time, screen2_last_activity_time, screen3_last_activity_time




def main():
    global running, show_error, error_start_time

    # These are local to the 'main' function now.
    user_detected_count = 0
    last_key_press_time = None

    def initialize_state():
        """Initializes all states and variables to start afresh."""
        nonlocal current_screen, button_pressed, keyboard_input, screen2_last_activity_time, screen3_last_activity_time
        nonlocal popup_message, popup_start_time, last_activity_time, user_detected_count, last_key_press_time
        # Initialize state variables
        current_screen = 0
        button_pressed = False
        keyboard_input = ""
        screen2_last_activity_time = None  
        screen3_last_activity_time = None  
        popup_message = None
        popup_start_time = None
        last_activity_time = pygame.time.get_ticks()
        user_detected_count = 0
        last_key_press_time = None
        # Clear bin.txt contents
        with open(BIN_FILE_PATH, 'w') as f:
            f.write("")
        
    # Initialize last_key_press_time to None
    #global last_key_press_time
    last_key_press_time = None
    last_activity_time = None
    screen2_last_activity_time = None
    screen3_last_activity_time = None

    # Initialize user_detected_count to 0
    #global user_detected_count
    #user_detected_count = 0
    
    clock = pygame.time.Clock()
    running = True
    current_screen = 0
    button_pressed = False
    keyboard_input = ""
    screen2_last_activity_time = None  # New variable to track last activity time on screen 2
    screen3_last_activity_time = None  # New variable to track last activity time on screen 3


    popup_message = None
    popup_start_time = None

    button_width, button_height = 130, 80
    button_spacing_x, button_spacing_y = 20, 20
    keyboard_start_x = (WIDTH - (3 * button_width + 2 * button_spacing_x)) // 2
    
    # Moved the keyboard up by decreasing the keyboard_start_y value
    keyboard_start_y = 300  # Bringing the keys up some more
    
    keyboard_buttons = []
    for row in range(4):
        for col in range(3):
            button_x = keyboard_start_x + col * (button_width + button_spacing_x)
            button_y = keyboard_start_y + row * (button_height + button_spacing_y)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            keyboard_buttons.append((KEYBOARD_LAYOUT[row][col], button_rect))
    
    images = []
    for url in image_urls:
        response = requests.get(url)
        image_path = f"images/{os.path.basename(url)}"
        with open(image_path, "wb") as f:
            f.write(response.content)
        images.append(pygame.image.load(image_path))

    class BinFileEventHandler(FileSystemEventHandler):
        def on_modified(self, event):
            nonlocal current_screen

            # Ignore the file changes when the current_screen is set to 0 or 4
            # Ignore the file changes when the current_screen is set to 0 or 4
            if current_screen == 0 or current_screen == 4:
                return

            if event.src_path == BIN_FILE_PATH:
                last_line = read_last_line_from_bin_file()
                if last_line == "[Verified Object]":
                    current_screen = 2
                    screen2_last_activity_time = current_time
                    last_activity_time = current_time  # Reset the general activity timer
                elif last_line == "[not electronic]":
                    current_screen = 3
                    screen3_last_activity_time = current_time
                    last_activity_time = current_time  # Reset the general activity timer


                

    
    
        




    event_handler = BinFileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(BIN_FILE_PATH), recursive=False)
    observer.start()

    def reset_state():
        """Resets all states and external influences."""
        nonlocal last_activity_time, screen2_last_activity_time, screen3_last_activity_time
        last_activity_time = None
        screen2_last_activity_time = None
        screen3_last_activity_time = None
        # Clear bin.txt contents
        with open(BIN_FILE_PATH, 'w') as f:
            f.write("")
    
    while running:
        current_time = pygame.time.get_ticks()
        screen.fill(WHITE)

        # Button press simulation (you'd replace this with your actual button detection mechanism)
        if button_pressed:
            last_activity_time = current_time  # Update the last activity time on button press
            if current_screen == 0:
                reset_state()
                last_activity_time = current_time
                screen2_last_activity_time = None
                screen3_last_activity_time = None
                current_screen = 1
            elif current_screen == 1:
                current_screen = 2
                screen2_last_activity_time = current_time
            elif current_screen == 2:
                current_screen = 3
                screen2_last_activity_time = None
            elif current_screen == 3:
                current_screen = 0
                screen3_last_activity_time = None
        
        # Check for timeout due to general inactivity
        if current_screen in [1, 2, 3] and should_switch_due_to_inactivity(last_activity_time):
            current_screen = 0
            #print(f"No activity for 30 seconds on screen {current_screen}, moved back to screen 0")
            last_activity_time = current_time  # Reset the activity timer here
            screen2_last_activity_time = None
            screen3_last_activity_time = None

        # Check for timeout specific to screen2
        elif current_screen == 2 and should_switch_due_to_inactivity(screen2_last_activity_time):
            current_screen = 0
            #print("No activity for 30 seconds on screen 2, moved back to screen 0")
            last_activity_time = current_time  # Reset the general activity timer here
            screen2_last_activity_time = None

        # Check for timeout specific to screen3
        elif current_screen == 3 and should_switch_due_to_inactivity(screen3_last_activity_time):
            current_screen = 0
            #print("No activity for 30 seconds on screen 3, moved back to screen 0")
            last_activity_time = current_time  # Reset the general activity timer here
            screen3_last_activity_time = None


        if show_error:
            if current_time - error_start_time < 1000:  
                draw_error_message("Enter full number")
            else:
                show_error = False  # Hide the error message after 3 seconds

        if 0 <= current_screen < len(images):
            scaled_image = scale_image(images[current_screen], WIDTH, HEIGHT)
            screen.blit(scaled_image, (0, 0))

        drop_ewaste_button = pygame.Rect(150, 600, 180, 60)
        finish_button = pygame.Rect(50, 600, 150, 60)
        drop_more_button = pygame.Rect(250, 600, 150, 60)

        # Draw the "Drop E-waste" button when on the initial screen
        if current_screen == 0:
            draw_3d_button("Drop E-waste", 150, 600, 180, 60)

        # Draw and handle "Finish" and "Drop more" buttons on screen 2
        if current_screen == 2:
            draw_3d_button("Finish", 50, 600, 150, 60, active=True)
            draw_3d_button("Drop more", 250, 600, 150, 60, active=True)

        # Draw and handle "Finish" and "Drop more" buttons on screen 3 (New Addition)
        if current_screen == 3:
            draw_3d_button("Finish", 50, 600, 150, 60, active=True)
            draw_3d_button("Drop more", 250, 600, 150, 60, active=True)

        if current_screen == 4:
            # Display the keyboard and input display
            for button_text, button_rect in keyboard_buttons:
                draw_3d_button(button_text, button_rect.x, button_rect.y, button_rect.width, button_rect.height)
            draw_keyboard_input_display(keyboard_input)  # Display input keys
        
        for event in pygame.event.get():
            last_activity_time = current_time
            if event.type == pygame.QUIT:
            
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if current_screen == 0 and drop_ewaste_button.collidepoint(event.pos):
                    write_to_bin_file("[user detected]\n")
                    current_screen = 1
                    #print("Switched to screen 1")  # Debug print

                elif current_screen == 2:
                    screen2_last_activity_time = current_time  # Update last activity time on button press

                    if finish_button.collidepoint(event.pos):
                        last_button_press_time = pygame.time.get_ticks()  # Update the last button press time
                        keyboard_input = ""
                        current_screen = 4  # Go to the keyboard screen
                        last_activity_time, screen2_last_activity_time, screen3_last_activity_time = reset_activity_timers(last_activity_time, screen2_last_activity_time, screen3_last_activity_time)

                        #print("Switched to screen 4 (keyboard screen)")  # Debug print


                    elif drop_more_button.collidepoint(event.pos):
                        last_button_press_time = pygame.time.get_ticks()  # Update the last button press time
                        write_to_bin_file("[user detected]\n")
                        current_screen = 1  # Go back to screen 1
                        last_activity_time, screen2_last_activity_time, screen3_last_activity_time = reset_activity_timers(last_activity_time, screen2_last_activity_time, screen3_last_activity_time)

                        #print("Switched to screen 1")  # Debug print


                elif current_screen == 3:
                    # Reset the activity time on any button press in screen 3
                    screen3_last_activity_time = current_time  # Update last activity time on button press
            
                    if finish_button.collidepoint(event.pos):
                        last_button_press_time = pygame.time.get_ticks()  # Update the last button press time
                        keyboard_input = ""
                        current_screen = 4  # Go to the keyboard screen
                        print("Switched to screen 4 (keyboard screen) from screen 3")  # Debug print
                    elif drop_more_button.collidepoint(event.pos):
                        last_button_press_time = pygame.time.get_ticks()  # Update the last button press time
                        write_to_bin_file("[user detected]\n")
                        current_screen = 1  # Go back to screen 1
                        last_activity_time, screen2_last_activity_time, screen3_last_activity_time = reset_activity_timers(last_activity_time, screen2_last_activity_time, screen3_last_activity_time)

                        #print("Switched to screen 1 from screen 3")  # Debug print
                        #print("[user detected] written to bin.txt")  # Debug print: To confirm that it's working

                elif current_screen == 4:
                    keyboard_input, current_screen = handle_keyboard_input(event, keyboard_input, keyboard_buttons)
                    #print(f"Current input: {keyboard_input}")


        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    observer.stop()
    observer.join()

if __name__ == "__main__":
    main()