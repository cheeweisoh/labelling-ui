import streamlit as st
from PIL import ImageFont
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from gdrive_utils import (
    find_folder_id,
    list_images_in_folder,
    get_image_from_drive,
    write_label_to_sheet,
)
from st_utils import next_image, prev_image
from fd_utils import load_model, get_bounding_boxes
from datetime import datetime
from zoneinfo import ZoneInfo

creds = service_account.Credentials.from_service_account_info(
    st.secrets["labelling_ui_credentials"],
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://spreadsheets.google.com/feeds",
    ],
)
FONT = ImageFont.load_default(size=18)

drive_service = build("drive", "v3", credentials=creds)
sheet_client = gspread.authorize(creds)

folder_id = find_folder_id(drive_service, "CS610/Project")
image_folder_id = find_folder_id(drive_service, "CS610/Project/Images")
image_files = list_images_in_folder(drive_service, image_folder_id)

output = sheet_client.open_by_key("1GPb0IKBueSGMmpC2rjfCbnvBJlR99JdQK0g_0mGX-bM").sheet1

face_app = load_model()

if "image_index" not in st.session_state:
    st.session_state.image_index = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = []


# Layout
st.title("Bounding Box Annotation Tool")

current_image_id = image_files[st.session_state.image_index]["id"]
current_image_name = image_files[st.session_state.image_index]["name"]
image = get_image_from_drive(drive_service, current_image_id)

vis_img, bbox_list = get_bounding_boxes(image, current_image_name, face_app)

st.image(vis_img, caption=current_image_name, use_container_width=True)

st.subheader("Assign labels to the bounding boxes")
new_labels = []
for idx, x1, y1, x2, y2 in bbox_list:
    label = st.text_input(f"Label for box {idx}", key=f"box_{idx}")
    if label:
        new_labels.append(
            [
                idx,
                x1,
                y1,
                x2,
                y2,
                label,
                datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

if st.button("Save Annotations", use_container_width=True):
    write_label_to_sheet(output, new_labels)
    st.success("Annotations saved!")

col1, col2 = st.columns(2)
with col1:
    if st.button("Previous", use_container_width=True):
        prev_image()
        st.rerun()

with col2:
    if st.button("Next", use_container_width=True):
        next_image(image_files)
        st.rerun()
