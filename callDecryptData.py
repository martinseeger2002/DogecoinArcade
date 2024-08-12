import decryptData

if __name__ == "__main__":
    # Define only the file name
    file_name = "2e190183cd04de58667027545354a7df7a31d44548a3effffd436fe9973b5a15.txt"

    # Call the decryption function from the module
    decrypted_file_path = decryptData.decrypt_file(file_name)

    print(f"Decrypted data has been saved to {decrypted_file_path}")
