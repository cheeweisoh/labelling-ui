import streamlit as st
from io import BytesIO, StringIO
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
import numpy as np


def test_connection(service):
    try:
        about = service.about().get(fields="user, storageQuota").execute()
        user_email = about["user"]["emailAddress"]
        st.success(f"Connected to Google Drive as: {user_email}")
        return True
    except Exception as e:
        st.error(f"Failed to connect to Google Drive:\n{e}")
        return False


def find_folder_id(service, path):
    parts = path.split("/")
    parent = None

    for part in parts:
        if parent is None:
            query = f"mimeType = 'application/vnd.google-apps.folder' and sharedWithMe and name = '{part}' and trashed = false"
        else:
            query = f"mimeType = 'application/vnd.google-apps.folder' and '{parent}' in parents and name = '{part}' and trashed = false"
        response = service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get("files", [])

        if not files:
            raise FileNotFoundError(
                f" Folder '{part}' not found under parent ID '{parent}'"
            )
        parent = files[0]["id"]

    return parent


def list_images_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get("files", [])


def get_image_from_drive(service, file_id):
    try:
        request = service.files().get_media(fileId=file_id)
        file_content = request.execute()

        image = Image.open(BytesIO(file_content))
        return image

    except Exception as e:
        st.error(f"Error downloading image: {str(e)}")
        return None


def write_label_to_sheet(worksheet, data):
    for row in data:
        row = [int(x) if isinstance(x, (np.integer,)) else x for x in row]
        worksheet.append_row(row)
