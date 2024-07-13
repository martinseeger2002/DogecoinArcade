import os

def delete_small_files(directory, size_limit_bytes):
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) < size_limit_bytes:
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    content_directory = "./indexes"
    size_limit_bytes = 10  # size limit in bytes
    delete_small_files(content_directory, size_limit_bytes)
