import face_recognition
import cv2
import os
import glob     #unixstyle pathnames
import numpy as np
import csv

class FaceEncode:
    def __init__(self):
        # Storing data
        self.known_face_encodings = []
        self.known_face_names = []
        self.data_path = "data.csv"

        # Resize frame for a faster speed
        self.frame_resizing = 1

    # Encodes highquality images of faces from the bluecard
    def encode_bluecard_images(self, images_path):
        # Load Images
        images_path = glob.glob(os.path.join(images_path, "*.*"))

        print("{} encoding images found.".format(len(images_path)))

        # Store image encoding and names
        for img_path in images_path:
            img = cv2.imread(img_path)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Get the filename only from the initial file path.
            basename = os.path.basename(img_path)
            (filename, ext) = os.path.splitext(basename)
            # Get encoding
            img_encoding = face_recognition.face_encodings(rgb_img)[0]

            # Store file name and file encoding
            self.known_face_encodings.append(img_encoding)
            self.known_face_names.append(filename)

            # Add encoding to csv
            index = -1
            print(f"Next file: \"{filename}\"")
            with open(self.data_path, 'r') as file:
                reader = csv.reader(file, delimiter="\t")
                for i, row in enumerate(reader):
                    if row:
                        if row[0] == filename:
                            print(f"Data for \"{filename}\" found in row {i}.")
                            index = i
                            break
            if index != -1:
                # Person already exists, add encoding in cell 4
                with open(self.data_path, 'r') as file:
                    rows = list(csv.reader(file, delimiter="\t"))
                    try:
                        rows[index][3] = img_encoding
                    except:
                        rows[index].append(img_encoding)
                with open(self.data_path, 'w', newline='') as file:
                    writer = csv.writer(file, delimiter="\t")
                    writer.writerows(rows)
                print(f"Encoding added to student with MATR.-NR. \"{filename}\".")
            else:
                # Person does not exist, append new row
                with open(self.data_path, 'a', newline='') as file:
                    writer = csv.writer(file, delimiter="\t")
                    writer.writerow([filename, '', '', img_encoding])
                print("Person not registered yet, encoding added anyway.")
        print("Encoding images loaded\n")
    
        return len(images_path)

    # Retrieve known encodings from csv
    # Returns encodings and their names
    def load_known_encodings(self):
        encodings = []
        names = []
        with open("data.csv", 'r') as file:
            reader = csv.reader(file, delimiter="\t")
            for row in reader:
                if len(row) >= 4 and row[3]:
                    cell = np.fromstring(row[3][1:-1], sep=' ')
                    names.append(row[0])
                    encodings.append(cell)
        print(encodings[3])
        return encodings, names

    # Detect known faces in given frame
    # Returns their location and matr.-nr. (name)
    def detect_known_faces(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resizing, fy=self.frame_resizing)
        # Find all the faces and face encodings in the current frame of video
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        self.known_face_encodings , self.known_face_names = self.load_known_encodings()

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
            face_names.append(name)

        # Convert to numpy array to adjust coordinates with frame resizing quickly
        face_locations = np.array(face_locations)
        face_locations = face_locations / self.frame_resizing
        return face_locations.astype(int), face_names

    # Show case for facial recognition
    # Creates image collage of all processes
    def detection_sample(self, frame):
        # Detect Faces
        face_locations, face_names = self.detect_known_faces(frame)
        for face_loc, name in zip(face_locations, face_names):
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

            cv2.putText(frame, name,(x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 255), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.imwrite("assets/detected_face.jpg", frame)
        print("frame saved\n")

        if face_names:
            print("Creating sample...")
            pos1 = cv2.imread(f"faces/{face_names[0]}.jpg")
            pos2 = cv2.imread("assets/id_photo.jpg")
            pos3 = cv2.imread("assets/detected_face.jpg")

            pos1 = cv2.resize(pos1, (300,300))
            pos2 = cv2.resize(pos2, (300,300))
            pos3 = cv2.resize(pos3, (300,300))

            v_stack1 = cv2.vconcat([pos1, pos2, pos3])
            print(type(v_stack1))

            cv2.imwrite(f"rec_samples/{face_names[0]}_collage.jpg", v_stack1)


            

            