import streamlit as st
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
import random


creds = service_account.Credentials.from_service_account_info(
    st.secrets["labelling_ui_credentials"],
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://spreadsheets.google.com/feeds",
    ],
)

drive_service = build("drive", "v3", credentials=creds)
sheet_client = gspread.authorize(creds)

folder_id = find_folder_id(drive_service, "CS610/Project")
image_folder_id = find_folder_id(drive_service, "CS610/Project/Images")
image_files = list_images_in_folder(drive_service, image_folder_id)

output = sheet_client.open_by_key(st.secrets["output_sheet"]["output_sheet_id"]).sheet1
labelled_images = [x[0] for x in output.get_all_values()[1:]]
remaining_images = [x for x in image_files if x["name"] not in labelled_images]
random.shuffle(remaining_images)

face_app = load_model()

st.title("Bounding Box Annotation Tool")

if remaining_images:
    current_image_id = remaining_images[0]["id"]
    current_image_name = remaining_images[0]["name"]
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
                    current_image_name,
                    idx,
                    x1,
                    y1,
                    x2,
                    y2,
                    label,
                    datetime.now(ZoneInfo("Asia/Singapore")).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                ]
            )

    if st.button("Save Annotations", use_container_width=True):
        write_label_to_sheet(output, new_labels)
        st.success("Annotations saved!")

        if st.button("Next", use_container_width=True):
            remaining_images = remaining_images[1:]
            st.rerun()

else:
    st.success("🎉 We're Done! 🎉")
