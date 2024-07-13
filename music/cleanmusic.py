import os
path = "music"

try:
    files = os.listdir(path)
    for file in files:
        if file not in (".placeholder", "cleanmusic.py"):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path) or os.path.isdir(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    os.rmdir(file_path)
    print('All files except ".placeholder" and "cleanmusic.py" have been deleted')
except Exception as e:
    print(f"An error occurred: {e}")