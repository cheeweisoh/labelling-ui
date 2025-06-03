import streamlit as st

# from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib import InstalledAppFlow
# from googleapiclient import build
# from googleapiclient.errors import HttpError
import os

# SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
IMAGE_FOLDER = "images"
ANNOTATION_FILE = "annotations.txt"
example_data = {
    "image1.jpg": [((50, 30, 150, 120), 1), ((160, 60, 250, 140), 2)],
    "image2.jpg": [((20, 20, 100, 100), 3)],
    "image3.jpg": [((20, 20, 100, 100), 4)],
}
FONT = ImageFont.load_default(size=18)


# def get_drive_service():
#     creds = None
#
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
#
#     try:
#         service = build("drive", "v3", credentials=creds)
#         return service
#     except HttpError as error:
#         print(f"An error occurred: {error}")
#
#
# def get_image_from_drive(service, file_id):
#     request = service.files().get_media(fileId=file_id)
#     fh = BytesIO()
#     downloader = MediaIoBaseDownload(fh, request)
#     done = False
#
#     while not done:
#         status, done = downloader.next_chunk()
#     fh.seek(0)
#     return Image.open(fh)


image_files = [
    f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".png", ".jpg", ",jpeg"))
]
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
