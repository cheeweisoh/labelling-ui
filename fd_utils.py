import streamlit as st
from insightface.app import FaceAnalysis
import cv2
import numpy as np


@st.cache_resource
def load_model():
    face_app = FaceAnalysis(
        name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
    )
    face_app.prepare(ctx_id=0)
    return face_app


def get_bounding_boxes(img, img_path, face_app):
    np_img2 = np.array(img)
    print(type(np_img2))
    print(np_img2.dtype)
    print(np_img2.shape)
    rgb_img2 = cv2.cvtColor(np_img2, cv2.COLOR_BGR2RGB)
    faces = face_app.get(rgb_img2)

    if not faces:
        raise Exception("No Faces Found")

    vis_img = rgb_img2.copy()
    h, w = vis_img.shape[:2]
    bbox_list = []

    for idx, face in enumerate(faces):
        box = face.bbox.astype(int)

        x1 = max(0, box[0])
        y1 = max(0, box[1])
        x2 = min(w, box[2])
        y2 = min(h, box[3])

        if x2 <= x1 or y2 <= y1:
            continue

        cv2.rectangle(vis_img, (x1, y1), (x2, y2), (0, 255, 0), 1)

        label = f"{idx}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1

        cv2.putText(
            vis_img,
            label,
            (x1, y1 - 5),
            font,
            font_scale,
            (0, 0, 0),
            thickness + 2,
            cv2.LINE_AA,
        )
        cv2.putText(
            vis_img,
            label,
            (x1, y1 - 5),
            font,
            font_scale,
            (0, 255, 0),
            thickness,
            cv2.LINE_AA,
        )

        bbox_list.append([idx, x1, y1, x2, y2])

    vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
    return vis_img, bbox_list


def progress_bar_with_text(current, total):
    percentage = int((current / total) * 100)
    progress_text = f"{current}/{total}"

    # HTML/CSS progress bar with centered text
    st.markdown(
        f"""
        <div style="position: relative; height: 24px; background-color: #eee; border-radius: 8px;">
            <div style="
                width: {percentage}%;
                background-color: #4CAF50;
                height: 100%;
                border-radius: 8px;
                text-align: center;
                color: white;
                line-height: 24px;
                font-weight: bold;
            ">
            </div>
            <div style="
                position: absolute;
                top: 0;
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                color: black;
                font-weight: bold;
            ">
                {progress_text if percentage < 15 else ""}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
