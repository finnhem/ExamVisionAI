import cv2
import re
import easyocr
import csv
import sys
import time

class BlueCardOCR:
    def __init__(self):
        # Regex for extracting names and matr.-nr.
        self.name_pattern = r"\b[A-Z][a-z]{2,}(?: [A-Z][a-z]{2,}){0,2}\b"
        self.number_pattern = r"\b\d{6}\b"
        self.id_photo_path = "assets/id_photo.jpg"  # Path of bluecard image
        self.data_path = "data.csv"
        self.reader = easyocr.Reader(['en'])  # Languages

    # Returns names and numbers filtered by regex from ocr read
    def get_ocr_data(self):
        result = self.reader.readtext(self.id_photo_path)

        filtered_names = []
        filtered_numbers = []

        for detection in result:
            text = detection[1]
            confidence = detection[2]
            filtered_names += re.findall(self.name_pattern, text) # Extract names using regular expression 
            filtered_numbers += re.findall(self.number_pattern, text)  # Extract numbers using regular expression
        
        return filtered_names, filtered_numbers

    # Adds ocr data to data.csv for later use
    def add_bluecard_to_csv(self, row):
        # Check for existing data entry in csv
        index = self.check_matrnr_entry(row[0])
        if index == -1:
            # Append mode (MATR.-NR. unknown)
            with open(self.data_path, "a") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(row)
        else:
            # MATR.-NR. already exists, add data to second and third cell
            with open(self.data_path, 'r') as file:
                rows = list(csv.reader(file, delimiter="\t"))
                rows[index][1] = row[1]
                rows[index][2] = row[2]
            with open(self.data_path, 'w', newline='') as file:
                writer = csv.writer(file, delimiter="\t")
                writer.writerows(rows)
            print(f"First and last name added to MATR.-NR. \"{rows[index][0]}\".")

    # Check for duplicates in csv
    def check_matrnr_entry(self, matrnr):
        with open(self.data_path, 'r') as file:
            reader = csv.reader(file, delimiter="\t")
            for i, row in enumerate(reader):
                if row:
                    if row[0] == matrnr:
                        print(f"Data for \"{matrnr}\" already exists in row {i}.")
                        return i

        return -1
