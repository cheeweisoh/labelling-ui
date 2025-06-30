import streamlit as st
from io import BytesIO
from PIL import Image
import pillow_heif
import numpy as np
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import time

pillow_heif.register_heif_opener()


def test_connection(service):
    try:
        about = service.about().get(fields="user, storageQuota").execute()
        user_email = about["user"]["emailAddress"]
        st.success(f"Connected to Google Drive as: {user_email}")
        return True
    except Exception as e:
        st.error(f"Failed to connect to Google Drive:\n{e}")
        return False


@st.cache_resource
def get_drive_service(_creds):
    drive_service = build("drive", "v3", credentials=_creds)
    return drive_service


def retry(request_fn, max_retries=10):
    for i in range(max_retries):
        try:
            return request_fn()

        except HttpError as e:
            if e.resp.status == 403 and "userRateLimitExceeded" in str(e):
                time.sleep(2**i)
            else:
                raise

    raise RuntimeError("API request failed")


def find_folder_id(service, path):
    parts = path.split("/")
    parent = None

    for part in parts:
        if parent is None:
            query = f"mimeType = 'application/vnd.google-apps.folder' and sharedWithMe and name = '{part}' and trashed = false"
        else:
            query = f"mimeType = 'application/vnd.google-apps.folder' and '{parent}' in parents and name = '{part}' and trashed = false"
        response = retry(
            lambda: service.files().list(q=query, fields="files(id, name)").execute()
        )
        files = response.get("files", [])

        if not files:
            raise FileNotFoundError(
                f" Folder '{part}' not found under parent ID '{parent}'"
            )
        parent = files[0]["id"]

    return parent


def list_images_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents"
    results = retry(
        lambda: service.files()
        .list(q=query, fields="files(id, name)", pageSize=1000)
        .execute()
    )
    return results.get("files", [])


def get_image_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    file_content = BytesIO(retry(lambda: request.execute()))

    try:
        image = Image.open(file_content)
        return image

    except Exception as e:
        st.error(f"Error downloading image: {str(e)}")
        return None


def write_label_to_sheet(worksheet, data):
    for row in data:
        row = [int(x) if isinstance(x, (np.integer,)) else x for x in row]
        worksheet.append_row(row)
