import streamlit as st
from PIL import ImageDraw, ImageFont
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gdrive_utils import find_folder_id, list_images_in_folder, get_image_from_drive
from st_utils import next_image, prev_image

creds = service_account.Credentials.from_service_account_info(
    st.secrets["labelling_ui_credentials"],
    scopes=["https://www.googleapis.com/auth/drive.readonly"],
)
ANNOTATION_FILE = "annotations.txt"
FONT = ImageFont.load_default(size=18)

drive_service = build("drive", "v3", credentials=creds)

folder_id = find_folder_id(drive_service, "CS610/Project/Images")
image_files = list_images_in_folder(drive_service, folder_id)

if "image_index" not in st.session_state:
    st.session_state.image_index = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = []


def save_annotation(image_name, boxes_with_labels):
    with open(ANNOTATION_FILE, "a") as f:
        for (x_min, y_min, x_max, y_max), label in boxes_with_labels:
            f.write(f"{image_name}, {x_min}, {y_min}, {x_max}, {y_max}, {label}\n")


# Layout
st.title("Bounding Box Annotation Tool")

current_image_id = image_files[st.session_state.image_index]["id"]
current_image_name = image_files[st.session_state.image_index]["name"]
image = get_image_from_drive(drive_service, current_image_id)

# draw = ImageDraw.Draw(image)
# for box, id in example_data[current_image_name]:
#     draw.rectangle(box, outline="red", width=2)
#     draw.text((box[2] - 2, box[3] - 2), str(id), fill="red", font=FONT)

st.image(image, caption=current_image_name, use_container_width=True)

# st.subheader("Assign labels to the bounding boxes")
# new_labels = []
# for i, (box, num_label) in enumerate(example_data[current_image_name]):
#     label = st.text_input(f"Label for box {i + 1}", key=f"box_{i}")
#     if label:
#         new_labels.append((box, label))
#
# if st.button("Save Annotations", use_container_width=True):
#     save_annotation(current_image_name, new_labels)
#     st.success("Annotations saved!")

col1, col2 = st.columns(2)
with col1:
    if st.button("Previous", use_container_width=True):
        prev_image()
        st.rerun()

with col2:
    if st.button("Next", use_container_width=True):
        next_image(image_files)
        st.rerun()
