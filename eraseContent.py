import os

def delete_small_files(directory, size_limit_kb):
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) < size_limit_kb * 1024:
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    content_directory = "./content"
    size_limit_kb = 100  # size limit in KB
    delete_small_files(content_directory, size_limit_kb)
