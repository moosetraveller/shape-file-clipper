# Evan's script rewritten (idea courtesy goes to Evan)

import zipfile
import os
import glob

# root_directory = os.getcwd()  # <-- get current working directory
root_directory = os.path.dirname(os.path.abspath(__file__))  # <-- get directory where Python file located
unzipped = os.path.join(root_directory, "Unzipped Files")

if not os.path.exists(unzipped):
    os.mkdir(unzipped)

zip_files = glob.glob(os.path.join(root_directory, "*.zip"))

for file_path in zip_files:
    zip_file = zipfile.ZipFile(file_path)
    zip_file.extractall(unzipped)

print("Zip files successfully extracted to {}".format(unzipped))
input("Press Enter to continue...")
