import pygame
import sys
import requests
import os
import socket
from io import BytesIO

class ButtonExample:
    def __init__(self):
        # Initialize pygame
        pygame.init()

        # Set up the window
        self.window_size = (480, 800)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Button Example")

        # Colors
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)

        # Fonts
        self.font = pygame.font.Font(None, 36)

        # Button dimensions
        self.button_width = 300
        self.button_height = 70

        # Load the images
        self.screen1_image = self.load_image("https://api.circularityspace.com/preload/1.jpg")
        self.screen2_image = self.load_image("https://api.circularityspace.com/preload/4.jpg")
        self.screen3_image = self.load_image("https://api.circularityspace.com/preload/2.jpg")
        self.screen4_image = self.load_image("https://api.circularityspace.com/preload/3.jpg")

        # Create the "Tap to Drop E-Waste" button
        self.drop_button_rect = pygame.Rect((self.window_size[0] - self.button_width) // 2, 600, self.button_width, self.button_height)

        # Create the "Finish" button on the verified image
        self.finish_button_rect = pygame.Rect(100, 700, self.button_width, self.button_height)

        # Create the "Drop Another" button on the verified image
        self.drop_another_button_rect = pygame.Rect(100, 800, self.button_width, self.button_height)

        # Initialize state variables
        self.current_screen = "screen1"
        self.keypad_open = False
        self.keypad_open_duration = 0
        self.pressed_keys = ""
        self.keypad_display_time = 0
        self.keypad_display_duration = 30  # Display keypad for 30 seconds

        # Set up socket for receiving prompts
        self.setup_socket()

    def load_image(self, image_url):
        response = requests.get(image_url)
        image_data = BytesIO(response.content)
        image = pygame.image.load(image_data)
        
        # Scale the image to fit within the window while preserving aspect ratio
        aspect_ratio = image.get_width() / image.get_height()
        new_width = min(image.get_width(), self.window_size[0])
        new_height = int(new_width / aspect_ratio)
        image = pygame.transform.scale(image, (new_width, new_height))
        
        return image

    def setup_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('127.0.0.1', 12345))
        self.socket.listen(1)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.keypad_open:
                        self.check_keypad_click(event.pos)
                    elif self.current_screen == "screen1":
                        if self.drop_button_rect.collidepoint(event.pos):
                            self.current_screen = "screen2"
                            print("Transitioning to Screen 2")
                            self.write_to_bin_txt("[user detected]\n")
                    elif self.current_screen == "screen4":
                        if self.finish_button_rect.collidepoint(event.pos):
                            self.current_screen = "keyboard"
                            self.keypad_open = True
                            self.keypad_open_duration = 30  # Open keypad for 30 seconds
                            print("Transitioning to Keypad")
                        elif self.drop_another_button_rect.collidepoint(event.pos):
                            self.write_to_bin_txt("[user detected]\n")

            if self.keypad_open_duration > 0:
                self.keypad_open_duration -= 1
                if self.keypad_open_duration == 0:
                    self.keypad_open = False

            verified = self.check_bin_txt()
            if verified is not None:
                if verified:
                    self.current_screen = "screen3"
                    print("Transitioning to Screen 3")
                else:
                    self.current_screen = "screen4"
                    print("Transitioning to Screen 4")

            self.window.fill(self.WHITE)
            if self.current_screen == "screen1":
                self.window.blit(self.screen1_image, (0, 0))
                pygame.draw.rect(self.window, self.GREEN, self.drop_button_rect)
                drop_text = self.font.render("Tap to Drop E-Waste", True, self.WHITE)
                self.window.blit(drop_text, (int(self.drop_button_rect.centerx - drop_text.get_width() / 2), int(self.drop_button_rect.centery - drop_text.get_height() / 2)))
            elif self.current_screen == "screen2":
                self.window.blit(self.screen2_image, (0, 0))
            elif self.current_screen == "screen3":
                self.window.blit(self.screen3_image, (0, 0))
            elif self.current_screen == "screen4":
                self.window.blit(self.screen4_image, (0, 0))
                pygame.draw.rect(self.window, self.GREEN, self.finish_button_rect)
                finish_text = self.font.render("Finish", True, self.WHITE)
                self.window.blit(finish_text, (int(self.finish_button_rect.centerx - finish_text.get_width() / 2), int(self.finish_button_rect.centery - finish_text.get_height() / 2)))

                pygame.draw.rect(self.window, self.GREEN, self.drop_another_button_rect)
                drop_another_text = self.font.render("Drop Another", True, self.WHITE)
                self.window.blit(drop_another_text, (int(self.drop_another_button_rect.centerx - drop_another_text.get_width() / 2), int(self.drop_another_button_rect.centery - drop_another_text.get_height() / 2)))
            elif self.current_screen == "keyboard":
                self.draw_keypad()

            if self.current_screen != "keyboard":
                self.keypad_open = False

            pygame.display.update()  # Update the display

        pygame.quit()  # Make sure to quit pygame when the loop exits

    def draw_keypad(self):
        keys = []
        key_width = 100
        key_height = 100
        key_x, key_y = (self.window_size[0] - 3 * key_width) / 2, (self.window_size[1] - 5 * key_height) / 2 + 100

        key_rows = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['del', '0', 'enter']
        ]

        for row in key_rows:
            key_row = []
            for key in row:
                key_rect = pygame.Rect(int(key_x), int(key_y), key_width, key_height)
                pygame.draw.rect(self.window, self.WHITE, key_rect)

                text_surface = self.font.render(key, True, self.WHITE)
                text_rect = text_surface.get_rect(center=key_rect.center)
                self.window.blit(text_surface, text_rect)

                key_row.append((key, key_rect))
                key_x += key_width + 20

            keys.append(key_row)
            key_x = (self.window_size[0] - 3 * key_width) / 2
            key_y += key_height + 20

        # Display the entered keys above the keypad
        text_surface = self.font.render(self.pressed_keys, True, self.WHITE)
        text_rect = text_surface.get_rect(center=(self.window_size[0] / 2, self.window_size[1] / 4))
        self.window.blit(text_surface, text_rect)

    def check_keypad_click(self, pos):
        mouse_x, mouse_y = pos
        keys = self.get_keypad_keys()

        for key_row in keys:
            for key, key_rect in key_row:
                if key_rect.collidepoint(mouse_x, mouse_y):
                    if key == 'del':
                        self.pressed_keys = self.pressed_keys[:-1]
                    elif key == 'enter':
                        self.keypad_open = False
                        if self.current_screen == "keyboard":
                            print("Entered:", self.pressed_keys)
                            if self.pressed_keys == "1234":  # Example code
                                self.current_screen = "screen4"
                                print("Transitioning to Screen 4")
                            else:
                                self.current_screen = "screen1"
                                print("Transitioning to Screen 1")
                    else:
                        self.pressed_keys += key

    def get_keypad_keys(self):
        key_width = 100
        key_height = 100
        key_x, key_y = (self.window_size[0] - 3 * key_width) / 2, (self.window_size[1] - 5 * key_height) / 2 + 100

        key_rows = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['del', '0', 'enter']
        ]

        keys = []
        for row in key_rows:
            key_row = []
            for key in row:
                key_rect = pygame.Rect(int(key_x), int(key_y), key_width, key_height)
                key_row.append((key, key_rect))
                key_x += key_width + 20

            keys.append(key_row)
            key_x = (self.window_size[0] - 3 * key_width) / 2
            key_y += key_height + 20

        return keys

    def write_to_bin_txt(self, message):
        file_path = os.path.join("/home/cir/Documents/app/py/bin/", "bin.txt")
        with open(file_path, "w") as file:
            file.write(message)

    def receive_prompt(self):
        data = self.socket.recv(1024)
        prompt = data.decode("utf-8")
        print("Received Prompt:", prompt)

        # Determine the next screen based on the received prompt
        if prompt == "1":
            self.current_screen = "screen1"
        elif prompt == "2":
            self.current_screen = "screen2"
        elif prompt == "3":
            self.current_screen = "screen3"
        elif prompt == "4":
            self.current_screen = "screen4"
        elif prompt == "keypad":
            self.current_screen = "keyboard"
            
    def check_bin_txt(self):
        file_path = os.path.join("/home/cir/Documents/app/py/bin/", "bin.txt")
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
                # Filter out commented lines and process the remaining lines
                lines = [line.strip() for line in lines if not line.strip().startswith("#")]
                if lines:
                    last_line = lines[-1]
                    if "[Not Verified Object]" in last_line:
                        return True
                    elif "[Verified Object]" in last_line:
                        return False
        except FileNotFoundError:
            pass
        return None

if __name__ == "__main__":
    app = ButtonExample()
    app.run()
