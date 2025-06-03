import streamlit as st

# from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from google.oauth2 import service_account
from googleapiclient import build
from googleapiclient.http import MediaIoBaseDownload

import os

creds = service_account.Credentials.from_service_account_info(
    st.secrets["labelling_ui_credentials"],
    scopes=["https://www.googleapis.com/auth/drive.readonly"],
)
IMAGE_FOLDER = "images"
ANNOTATION_FILE = "annotations.txt"
example_data = {
    "image1.jpg": [((50, 30, 150, 120), 1), ((160, 60, 250, 140), 2)],
    "image2.jpg": [((20, 20, 100, 100), 3)],
    "image3.jpg": [((20, 20, 100, 100), 4)],
}
FONT = ImageFont.load_default(size=18)

drive_service = build("drive", "v3", credentials=creds)


def find_folder_id(service, path):
    parts = path.strip("/").split("/")
    parent = "root"

    for part in parts:
        query = f"'{parent}' in parents and mimeType = 'application/vnd.google-apps.folder' and name = '{part}' and trashed = false"
        response = service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get("files", [])

        if not files:
            raise FileNotFoundError(
                f" Folder '{part}' not found under parent ID '{parent}'"
            )
        parent = files[0]["id"]

    return parent


def list_images_in_folder(folder_id):
    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return results.get("files", [])


folder_id = find_folder_id(drive_service, "CS610/Project/Images")
image_files = list_images_in_folder(folder_id)
image_files.sort()

if "image_index" not in st.session_state:
    st.session_state.image_index = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = []


def save_annotation(image_name, boxes_with_labels):
    with open(ANNOTATION_FILE, "a") as f:
        for (x_min, y_min, x_max, y_max), label in boxes_with_labels:
            f.write(f"{image_name}, {x_min}, {y_min}, {x_max}, {y_max}, {label}\n")


def next_image():
    if st.session_state.image_index < len(image_files) - 1:
        st.session_state.image_index += 1


def prev_image():
    if st.session_state.image_index > 0:
        st.session_state.image_index -= 1


# Layout
st.title("Bounding Box Annotation Tool")

current_image_name = image_files[st.session_state.image_index]
image = Image.open(f"images/{current_image_name}").convert("RGB")

draw = ImageDraw.Draw(image)
for box, id in example_data[current_image_name]:
    draw.rectangle(box, outline="red", width=2)
    draw.text((box[2] - 2, box[3] - 2), str(id), fill="red", font=FONT)

st.image(image, caption=current_image_name, use_container_width=True)

st.subheader("Assign labels to the bounding boxes")
new_labels = []
for i, (box, num_label) in enumerate(example_data[current_image_name]):
    label = st.text_input(f"Label for box {i + 1}", key=f"box_{i}")
    if label:
        new_labels.append((box, label))

if st.button("Save Annotations", use_container_width=True):
    save_annotation(current_image_name, new_labels)
    st.success("Annotations saved!")

col1, col2 = st.columns(2)
with col1:
    if st.button("Previous", use_container_width=True):
        prev_image()
        st.rerun()

with col2:
    if st.button("Next", use_container_width=True):
        next_image()
        st.rerun()
