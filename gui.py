import tkinter as tk
import cv2
from PIL import Image, ImageTk
from easy_ocr import BlueCardOCR
from facerecognition import FaceEncode
import time
import threading
import os
from tkinter import scrolledtext
from tkinter import messagebox
import glob
import csv


# Custom Tkinter frame for displaying video
class ImageFrame(tk.Frame):
    def __init__(self, parent, image_width, image_height):
        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, width=image_width, height=image_height)
        self.canvas.pack()

    # Converting cv2 images to Tkinter format for constant display
    def update_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        image = image.resize((self.canvas.winfo_width(), self.canvas.winfo_height()), resample=Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(image)

        self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        self.canvas.image = img_tk  # Save a reference to avoid garbage collection


# Graphical user interface
class ImageProcessingApp:
    def __init__(self, image_width, image_height):
        self.root = tk.Tk()
        self.root.title("Image Processing Software Group One")

        # 4. Frame for displaying latest facerecognition sample
        self.face_rec_frame = tk.Frame(self.root, width=image_width*0.3, height=image_height)
        self.face_rec_frame.grid_propagate(0)
        self.face_rec_frame.grid(row=0, column=3, padx=10)

        self.face_rec_label = tk.Label(self.face_rec_frame, text="Last Facerecognition Sample")
        self.face_rec_label.grid(row=0, column=0, padx=5, pady=5)

        self.sample_label = tk.Label(self.face_rec_frame)
        self.sample_label.grid(row=1, column=0, padx=5, pady=5)

        self.display_latest_sample()
        

        # 3. Frame for registration validation
        self.bl_reg_frame = tk.Frame(self.root, width=image_width*0.3, height=image_height)
        self.bl_reg_frame.grid_propagate(0)
        self.bl_reg_frame.grid(row=0, column=2, padx=10)

        self.bl_reg_label = tk.Label(self.bl_reg_frame, text="Bluecard Registrations")
        self.bl_reg_label.grid(row=0, column=0, padx=5, pady=5, sticky="we")

        self.face_rec = FaceEncode()


        # 2. Frame for video stream
        self.image_frame = ImageFrame(self.root, image_width, image_height)
        self.image_frame.grid(row=0, column=1)

        self.cap = cv2.VideoCapture(0)
        self.frame_lock = threading.Lock()

        self.ocr = BlueCardOCR()
        self.frame = None


        # 1. Frame for control panel
        self.control_frame = tk.Frame(self.root, width=image_width*0.3, height=image_height)
        self.control_frame.grid_propagate(0)
        self.control_frame.grid(row=0, column=0, padx=10)

        self.control_label = tk.Label(self.control_frame, text="Control Panel")
        self.control_label.grid(row=0, column=0, padx=5, pady=5)


        # Buttons
        self.reg_bl_button = tk.Button(self.control_frame, text="Register new Bluecard", command=self.register_button)
        self.reg_bl_button.grid(row=1, column=0, padx=5, pady=5)

        self.flash = False
        self.check = tk.Button(self.control_frame, text="Camera Flash", command=self.check_button)
        self.check.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        self.enc_bl_button = tk.Button(self.control_frame, text="Encode Bluecard Portraits", command=self.enc_bl_portraits)
        self.enc_bl_button.grid(row=3, column=0, padx=5, pady=5)

        self.face_rec_button = tk.Button(self.control_frame, text="Facerecognition Sample", command=self.face_rec_sample)
        self.face_rec_button.grid(row=4, column=0, padx=5, pady=5)

        self.open_faces_button = tk.Button(self.control_frame, text="Open Bluecard Portraits", command=self.faces_button)
        self.open_faces_button.grid(row=5, column=0, padx=5, pady=5)

        self.open_collage_button = tk.Button(self.control_frame, text="Open Examinee Collages", command=self.collage_button)
        self.open_collage_button.grid(row=6, column=0, padx=5, pady=5)


    # Register new bluecard with OCR
    def register_button(self):
        # Stop camera thread for flash
        self.stop_capture.set()

        # Screen flash if activated
        if self.flash == True:
            flash_window = tk.Toplevel()
            flash_window.attributes('-fullscreen', True)
            flash_window.configure(bg='#FFFFFF')
            flash_window.lift()
            flash_window.after(3000, flash_window.destroy)
            time.sleep(2.5)
        
        ret, frame = self.cap.read()
        time.sleep(1)

        cv2.imwrite("assets/id_photo.jpg", frame)

        # Restart video thread
        self.start_capture_thread()

        # Run OCR on captured image
        names, numbers = self.ocr.get_ocr_data()

        confirmation = False

        # Letting user verify data from OCR
        if names and numbers:
            confirmation = messagebox.askyesno("Data Verification", 
                            f"Please check if your data is correct:\n\n"
                            f"First name:\t{names[0]}\n"
                            f"Last name:\t{names[1]}\n"
                            f"MATR.-NR.:\t{numbers[0]}\n\n"
                            f"Is the data correct?")

        if confirmation:
            row = [numbers[0], names[0], names[1]]
            messagebox.showinfo("Registration", "Data verified successfully!")
            self.ocr.add_bluecard_to_csv(row) # Data added to csv
        else:
            # User has to try again under better conditions
            messagebox.showinfo("Registration", "Registration failed, please try again.")

    # Toggle for screenfalsh
    def check_button(self):
        if self.flash == False:
            self.flash = True
            self.check.configure(bg="yellow", text="Flash on")
        elif self.flash == True:
            self.flash = False
            self.check.configure(bg="#d9d9d9", text="Camera Flash")

    # Displaying latest registrations
    def display_persons(self, rows):
        for i, row in enumerate(rows):
            # Create a frame for the person
            person_frame = tk.Frame(self.bl_reg_frame)
            person_frame.grid(row=i+1, column=0, padx=10, pady=10)

            # Create labels for the person's data
            label_first_name = tk.Label(person_frame, text="First Name:", anchor='w')
            label_first_name.grid(row=0, column=0, sticky="w")
            label_last_name = tk.Label(person_frame, text="Last Name:", anchor='w')
            label_last_name.grid(row=1, column=0, sticky="w")
            label_id = tk.Label(person_frame, text="ID:", anchor='w')
            label_id.grid(row=2, column=0, sticky="w")

            label_first_name_value = tk.Label(person_frame, text=row[1], anchor='e')
            label_first_name_value.grid(row=0, column=1, sticky="e")
            label_last_name_value = tk.Label(person_frame, text=row[2], anchor='e')
            label_last_name_value.grid(row=1, column=1, sticky="e")
            label_id_value = tk.Label(person_frame, text=row[0], anchor='e')
            label_id_value.grid(row=2, column=1, sticky="e")

    # Getting latest personal data from csv
    def get_latest_persons(self, csv_file, num_persons):
        persons = []
        with open(csv_file, 'r') as file:
            reader = csv.reader(file, delimiter="\t")
            data = list(reader)

            # Iterate over the rows in reverse order
            for row in reversed(data):
                if len(row) >= 3 and all(row):
                    persons.append(row[0:3])
                    if len(persons) == num_persons:
                        break
        return persons

    # Encoding Bluecard Portraits
    def enc_bl_portraits(self):
        self.enc_bl_button.config(state="disabled")
        messagebox.showinfo("Encoding Info", "This process may take some time, please be patient.")
        
        count = self.face_rec.encode_bluecard_images("faces/")

        messagebox.showinfo("Encoding Results", f"{count} BlueCard portraits could be encoded.")
        self.enc_bl_button.config(state="normal")

    # Displaying latest sample
    def display_latest_sample(self):
        folder = "rec_samples"  
        latest_image_path = self.get_latest_sample_path(folder)
        if latest_image_path:
            image = Image.open(latest_image_path)
            image = image.resize((150, 450)) # fitting sample to frame size
            photo = ImageTk.PhotoImage(image)

            self.sample_label.configure(image=photo)
            self.sample_label.image = photo
        else:
            self.sample_label.configure(text="No sample created yet", image="")

    # getting latest sample path from folder
    def get_latest_sample_path(self, folder):
        image_files = glob.glob(f"{folder}/*.jpg")
        if image_files:
            latest_image = max(image_files, key=os.path.getctime)
            return latest_image
        return None

    # Create face recognition sample
    def face_rec_sample(self):
        self.face_rec.detection_sample(self.frame)

    # Gallery display functions
    def faces_button(self):
        self.open_image_window("Bluecard Protraits","faces/", 100, 120, 389, 400)

    def collage_button(self):
        self.open_image_window("Examinee Collage","rec_samples/", 300, 900, 930, 600)

    # Image gallery window
    def open_image_window(self, title , img_path, img_X, img_Y, window_X, window_Y):
        image_window = tk.Toplevel(self.root)
        image_window.title(title)
        image_window.geometry(f"{window_X}x{window_Y}")

        image_folder = img_path
        images = os.listdir(image_folder)

        text_frame = tk.Frame(image_window)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_canvas = tk.Canvas(text_frame)
        text_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollable window feature
        scrollbar = tk.Scrollbar(text_frame, command=text_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_canvas.configure(yscrollcommand=scrollbar.set)
        text_canvas.bind("<Configure>", lambda e: text_canvas.configure(scrollregion=text_canvas.bbox("all")))

        inner_frame = tk.Frame(text_canvas)
        text_canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)

        row = 0
        column = 0

        # Enabling mousewheel on scrollbar
        # Must be declared before binding
        def on_mousewheel(event):
            text_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


        # Picking and displaying images in frame
        for index, image_file in enumerate(images):
            image_path = os.path.join(image_folder, image_file)
            img = Image.open(image_path)
            img = img.resize((img_X, img_Y), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)

            label = tk.Label(inner_frame, image=img_tk)
            label.image = img_tk
            label.grid(row=row, column=column, padx=5, pady=5)
            label.bind("<MouseWheel>", on_mousewheel)

            filename_label = tk.Label(inner_frame, text=image_file)
            filename_label.grid(row=row+1, column=column, padx=5)

            column += 1
            if column == 3:
                column = 0
                row += 2

        # Attempt to bring scroll feature to whole window
        def on_inner_frame_configure(event):
            text_canvas.configure(scrollregion=text_canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_inner_frame_configure)


    # Multithreading functions for smooth performance
    def start_capture_thread(self):
        self.stop_capture = threading.Event()
        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.capture_thread.daemon = True # Thread runs in the background
        self.capture_thread.start()

    # Capturing frames from webcam
    def capture_frames(self):
        while self.stop_capture:
            ret, self.frame = self.cap.read()

            if ret:
                with self.frame_lock:
                    self.image_frame.update_image(self.frame)

    # Thread for refreshing data on mainwindow
    def start_page_refresher_thread(self):
        self.refresher_thread = threading.Thread(target=self.refresh_data)
        self.refresher_thread.daemon = True
        self.refresher_thread.start()

    def refresh_data(self):
        while True:
            persons = self.get_latest_persons("data.csv", 6)
            self.display_persons(persons) # refreshing personal data
            self.display_latest_sample() # refreshing sample
            time.sleep(2) # every two seconds

    # Application starter function
    def run(self):
        self.root.bind('<Escape>', lambda e: self.root.quit())  # Bind Escape key to exit the application
        self.start_capture_thread()  # Start the frame capture thread
        self.start_page_refresher_thread()  # Start the refresher thread
        self.root.mainloop()  # Start the Tkinter event loop