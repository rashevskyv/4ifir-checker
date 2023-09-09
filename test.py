import requests
from datetime import datetime

# Updated function to fetch the latest GitHub API data every time it runs.
def fetch_and_compare_github_file(last_modified_str, github_api_url, target_file_name):
    # Fetch the latest release data from GitHub API
    try:
        response = requests.get(github_api_url)
        if response.status_code != 200:
            return "Failed to fetch data from GitHub API"
        github_api_data = response.json()
    except Exception as e:
        return f"An error occurred while fetching data from GitHub API: {e}"
    
    # Find the 'updated_at' timestamp for the target file from the GitHub API data
    for asset in github_api_data['assets']:
        if asset['name'] == target_file_name:
            github_updated_at = asset['updated_at']
            download_url = asset['browser_download_url']
            break
    else:
        return "Target file not found in GitHub API data"
    
    # Convert 'last_modified_str' and 'github_updated_at' to datetime objects
    last_modified = datetime.fromisoformat(last_modified_str)
    github_updated_at = datetime.fromisoformat(github_updated_at[:-1])  # Remove the 'Z'
    
    # Check which file is newer and download if needed
    if last_modified >= github_updated_at:
        return "Local file is up to date"
    else:
        try:
            response = requests.get(download_url)
            if response.status_code != 200:
                return "Failed to download file"
            with open(target_file_name, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            return f"An error occurred while downloading the file: {e}"
        
        return "File updated successfully"

# Since I can't execute HTTP requests, you can test this function in your local environment.


# Test the function
last_modified_str = "2023-01-01T12:34:56"  # Example last modified timestamp
github_api_url = "https://api.github.com/repos/rashevskyv/DBI/releases/latest"
target_file_name = "DBI.nro"

fetch_and_compare_github_file(last_modified_str, github_api_url, target_file_name)
