import streamlit as st
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_info(
    st.secrets["labelling_ui_credentials"],
    scopes=["https://www.googleapis.com/auth/drive.readonly"],
)
ANNOTATION_FILE = "annotations.txt"
FONT = ImageFont.load_default(size=18)

drive_service = build("drive", "v3", credentials=creds)


def test_connection(service):
    try:
        about = service.about().get(fields="user, storageQuota").execute()
        user_email = about["user"]["emailAddress"]
        st.success(f"✅ Connected to Google Drive as: {user_email}")
        return True
    except Exception as e:
        st.error(f"❌ Failed to connect to Google Drive:\n{e}")
        return False


test_connection(drive_service)


def find_folder_id(service, path):
    parts = path.split("/")
    parent = None

    for part in parts:
        print(f"PART: {part} in {parent}")
        if parent is None:
            query = "mimeType = 'application/vnd.google-apps.folder' and sharedWithMe and trashed = false"
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


def next_image():
    if st.session_state.image_index < len(image_files) - 1:
        st.session_state.image_index += 1


def prev_image():
    if st.session_state.image_index > 0:
        st.session_state.image_index -= 1


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
        next_image()
        st.rerun()
