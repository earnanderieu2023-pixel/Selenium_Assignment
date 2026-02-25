import pdfplumber
import os
import json

def extract_text_from_folder(folder_path):
    all_text = ""
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            with pdfplumber.open(os.path.join(folder_path, filename)) as pdf:
                for page in pdf.pages:
                    all_text += page.extract_text() + "\n"
    return all_text

# 1. Point this to your folder
my_data = extract_text_from_folder("/Users/estellearnander/sem4/OSPC/Powerpoints")

# 2. Print it to copy-paste into Gemini for the next step
print(my_data)