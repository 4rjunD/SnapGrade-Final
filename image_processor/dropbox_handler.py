import dropbox
import requests
from config import Config

def get_file_from_dropbox(file_path):
    """
    Download a file from Dropbox.
    
    Args:
        file_path (str): The path to the file in Dropbox
        
    Returns:
        bytes: The file content as bytes
    """
    try:
        # Initialize Dropbox client
        dbx = dropbox.Dropbox(Config.DROPBOX_ACCESS_TOKEN)
        
        # Download the file
        metadata, response = dbx.files_download(file_path)
        
        # Return the file content
        return response.content
    except Exception as e:
        # Line 24 - Replace f-string with .format()
        raise Exception("Error downloading file from Dropbox: {}".format(str(e)))

def get_file_from_shared_link(shared_link):
    """
    Download a file from a Dropbox shared link.
    
    Args:
        shared_link (str): The Dropbox shared link
        
    Returns:
        bytes: The file content as bytes
    """
    try:
        # Initialize Dropbox client
        dbx = dropbox.Dropbox(Config.DROPBOX_ACCESS_TOKEN)
        
        # Get the shared link metadata
        shared_link_metadata = dbx.sharing_get_shared_link_metadata(shared_link)
        
        # Get the file path
        file_path = shared_link_metadata.path_lower
        
        # Download the file
        return get_file_from_dropbox(file_path)
    except Exception as e:
        # Try direct download if the Dropbox API approach fails
        try:
            # Convert shared link to direct download link
            dl_link = shared_link.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
            response = requests.get(dl_link)
            response.raise_for_status()
            return response.content
        except Exception as inner_e:
            # Line 57 - Replace f-string with .format()
            raise Exception("Error downloading file from shared link: {}. Direct download error: {}".format(str(e), str(inner_e)))