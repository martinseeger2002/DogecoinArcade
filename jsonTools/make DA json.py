import json

# Predefined collection data
collection_data = {
    "name": "Dogecoin Arcade Founders Pass",
    "thumbnail": "05e19f46868c063528247ce67a47b584a0e59e2b4373d1ca338c62b69a220d03i0",
    "description": "The Dogecoin Arcade Founders Pass is a limited-edition collection of 200 exclusive passes, offering lifetime access to the Dogecoin Arcade. Holders receive early access to updates, secure local Doginals management, cost-effective inscription transfers, and future upgrades, including a built-in inscriber and a planned Dogecoin Arcade Metaverse.",
    "slug": "dafp",
    "html_inscriptionID": "",
    "xcom_user": "https://x.com/MartinSeeger2"
}

# Load DA.json
with open('DM.json', 'r') as da_file:
    da_data = json.load(da_file)

# Combine the JSON data
combined_data = {
    "collection": collection_data,
    "items": da_data
}

# Save the combined JSON data to a new file
with open('DA.json', 'w') as combined_file:
    json.dump(combined_data, combined_file, indent=4)

print("Combined JSON data has been saved to combined.json")
