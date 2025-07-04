import streamlit as st
import gc
from collections import OrderedDict
from zoneinfo import ZoneInfo
from datetime import datetime

from src.utils.google_drive import (
    get_image_from_drive,
    write_label_to_sheet,
)
from src.utils.face_detection import (
    get_bounding_boxes,
    progress_bar_with_text,
)
from src.state import init_state

MAX_BBOX_CACHE_SIZE = 10


def main():
    init_state(st)

    st.markdown(
        "<h3 style='text-align: center;'>Bounding Box Annotation Tool</h1>",
        unsafe_allow_html=True,
    )

    progress_bar_with_text(
        st.session_state.metrics_labelled_images, st.session_state.metrics_total_images
    )

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

    if st.session_state.image_index < len(st.session_state.remaining_images):
        current_image = st.session_state.remaining_images[st.session_state.image_index]
        current_image_id = current_image["id"]
        current_image_name = current_image["name"]
        image = get_image_from_drive(st.session_state.drive_service, current_image_id)

        if "bbox_cache" not in st.session_state:
            st.session_state.bbox_cache = OrderedDict()

        if current_image_name not in st.session_state.bbox_cache:
            vis_img, bbox_list = get_bounding_boxes(
                image, current_image_name, st.session_state.face_app
            )
            st.session_state.bbox_cache[current_image_name] = (vis_img, bbox_list)

            if len(st.session_state.bbox_cache) > MAX_BBOX_CACHE_SIZE:
                st.session_state.bbox_cache.popitem(last=False)
        else:
            vis_img, bbox_list = st.session_state.bbox_cache[current_image_name]

        st.image(vis_img, caption=current_image_name, use_container_width=True)

        st.subheader("Select the main character")
        form = st.form("checkboxes", clear_on_submit=True)
        new_labels = []
        with form:
            for idx, x1, y1, x2, y2 in bbox_list:
                checked = st.checkbox(f"Box {idx}", key=f"box_{idx}")
                label = 0 if checked else 1
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

            submitted_sure = st.form_submit_button("I'm sure", use_container_width=True)
            submitted_notsure = st.form_submit_button(
                "I'm not sure", use_container_width=True
            )

        if submitted_sure or submitted_notsure:
            flag = "y" if submitted_sure else "n"
            new_labels = [x + [flag] for x in new_labels]
            write_label_to_sheet(st.session_state.output, new_labels)
            st.success("Annotations saved!")
            st.session_state.image_index += 1
            st.session_state.metrics_labelled_images += 1
            del new_labels, image
            gc.collect()
            st.rerun()

    else:
        st.success("🎉 We're Done! 🎉")


if __name__ == "__main__":
    main()
