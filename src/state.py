import random
import gspread
from google.oauth2 import service_account
from src.utils.google_drive import (
    get_drive_service,
    find_folder_id,
    list_images_in_folder,
)
from src.utils.face_detection import load_model


def init_state(st):
    if "remaining_images" in st.session_state:
        return

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["labelling_ui_credentials"],
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://spreadsheets.google.com/feeds",
        ],
    )

    drive_service = get_drive_service(creds)
    sheet_client = gspread.authorize(creds)

    image_folder_id = find_folder_id(drive_service, "CS610_AML")
    image_files = list_images_in_folder(drive_service, image_folder_id)

    output = sheet_client.open_by_key(
        st.secrets["output_sheet"]["output_sheet_id"]
    ).sheet1
    labelled_images = set([x[0] for x in output.get_all_values()[1:]])
    remaining_images = [x for x in image_files if x["name"] not in labelled_images]
    random.shuffle(remaining_images)

    st.session_state.remaining_images = remaining_images
    st.session_state.image_index = 0
    st.session_state.drive_service = drive_service
    st.session_state.face_app = load_model()
    st.session_state.output = output
    st.session_state.metrics_total_images = len(image_files)
    st.session_state.metrics_labelled_images = len(labelled_images)
