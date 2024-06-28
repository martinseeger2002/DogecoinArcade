#assemble_data.py
import mimetypes

file_path = 'temp_scriptSig_list.txt'

def process_file(file_path):
    target_sequence = "6582895"
    with open(file_path, 'r') as file:
        data = file.read()
    parts = data.split()
    # Finding the target sequence in the file
    start_index = data.find(target_sequence)
    if start_index == -1:
        raise ValueError(f"Sequence '{target_sequence}' not found in the file")

    # Extracting data from after the sequence
    start_index_data = data[start_index + len(target_sequence):].strip()

    # Splitting the data by spaces
    index_parts = start_index_data.split()

    # Extracting the number of chunks
    num_chunks = int(index_parts[0])

    # Extracting the first chunk of data
    first_chunk_hex = index_parts[1]
    MIME_type = bytes.fromhex(first_chunk_hex).decode('utf-8', errors='replace')

    return num_chunks, parts, MIME_type


def assemble_data_string(parts, num_chunks):
    data_string = ''
    current_chunk = num_chunks - 1

    while current_chunk >= 0:
        # Search for the current chunk number in parts in each iteration
        for i in range(len(parts)):
            if parts[i] == str(current_chunk):
                # Append the next part to the data string
                if i + 1 < len(parts):
                    data_string += parts[i + 1]
                break

        # Decrease the chunk number for the next iteration
        current_chunk -= 1

    return data_string

def save_to_file(data, file_name):
    with open(file_name, 'w') as file:
        file.write(data)

def convert_and_save(data_hex, mime_type, output_filename):
    # Manually map certain MIME types to file extensions
    manual_mime_type_mapping = {
        'image/webp': '.webp'
    }

    # Strip off the charset part if present
    mime_type = mime_type.split(';')[0].strip()

    # Convert hex to bytes
    data_bytes = bytes.fromhex(data_hex)

    # Check if MIME type is in the manual mapping
    if mime_type in manual_mime_type_mapping:
        extension = manual_mime_type_mapping[mime_type]
    else:
        # Determine the file extension based on MIME type
        extension = mimetypes.guess_extension(mime_type)
        if not extension:
            raise ValueError(f"Unable to determine file extension for MIME type: {mime_type}")

    # Save the file with the appropriate extension
    full_output_filename = f"{output_filename}{extension}"
    with open(full_output_filename, 'wb') as file:
        file.write(data_bytes)
    return full_output_filename


def save_data_as_hex_txt(num_chunks, file_parts):
    data_string = assemble_data_string(file_parts, num_chunks)
    save_to_file(data_string, 'output.txt')
    return 'output.txt'  # Returning the name of the saved file


def save_file_as_file(num_chunks, file_parts, MIME_type):
    data_string = assemble_data_string(file_parts, num_chunks)
    output_filename = 'output'
    saved_file = convert_and_save(data_string, MIME_type, output_filename)
    return saved_file  # Returning the path of the saved file



