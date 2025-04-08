import streamlit as st
from snowflake.snowpark.context import get_active_session
from datetime import datetime, timedelta
import pandas as pd

# Get Snowflake session
session = get_active_session()

st.title("🛠 Course Admin")

# Section: Add New Course
with st.expander("➕ Add New Course"):
    name = st.text_input("Course Name", key="new_course_name")
    description = st.text_area("Course Description", key="new_course_desc")
    duration = st.number_input("Duration (days)", min_value=0.5, step=0.5, key="new_course_duration")
    course_type = st.selectbox("Course Type", ["Virtual", "In-person", "Bespoke"], key="new_course_type")
    status = st.selectbox("Status", ["WIP", "Live", "Feedback", "Backlog"], key="new_course_status")
    user = st.text_input("Your Name", key="new_course_user")

    if st.button("Add Course", key="add_course_btn"):
        now = datetime.now()
        next_review = now + timedelta(days=180)

        session.sql(f"""
            INSERT INTO COURSE_CATALOG (
                COURSE_NAME, COURSE_DESCRIPTION, COURSE_CREATED,
                COURSE_DURATION, COURSE_TYPE, NEXT_REVIEW_DATE,
                LAST_AMENDED_BY, LAST_AMENDED_DATE, COURSE_STATUS
            ) VALUES (
                '{name}', '{description}', CURRENT_TIMESTAMP,
                {duration}, '{course_type}', '{next_review.date()}',
                '{user}', CURRENT_TIMESTAMP, '{status}'
            )
        """).collect()
        st.success("✅ Course added!")

# Fetch and display courses
df = session.table("COURSE_CATALOG").sort("ID", ascending=False).to_pandas()

st.subheader("📋 Course List")
if df.empty:
    st.info("No courses found.")
else:

    with st.expander("📊 View All Courses"):
        st.dataframe(
        df[["COURSE_NAME", "COURSE_DURATION", "NEXT_REVIEW_DATE", "COURSE_TYPE", "COURSE_STATUS"]]
            .rename(columns={
                "COURSE_NAME": "Course",
                "COURSE_DURATION": "Duration (days)",
                "NEXT_REVIEW_DATE": "Next Review",
                "COURSE_TYPE": "Type",
                "COURSE_STATUS": "Status"
            }),
        use_container_width=True,  # optional: for full width
        hide_index=True            # ✅ this hides the row number
    )
    
    selected = st.selectbox("Select Course to Edit or Review", df["COURSE_NAME"].tolist(), key="course_selectbox")
    course = df[df["COURSE_NAME"] == selected].iloc[0]

    with st.expander("✏️ Edit Course"):
        course_id = course["ID"]

        new_desc = st.text_area("Course Description", value=course["COURSE_DESCRIPTION"], key=f"desc_{course_id}")
        new_dur = st.number_input("Duration (days)", min_value=0.5, step=0.5, value=float(course["COURSE_DURATION"]), key=f"dur_{course_id}")
        new_type = st.selectbox("Course Type", ["Virtual", "In-person"], 
                                index=["Virtual", "In-person"].index(course["COURSE_TYPE"]), 
                                key=f"type_{course_id}")
        new_status = st.selectbox("Status", ["WIP", "Live", "Feedback", "Backlog"], 
                                  index=["WIP", "Live", "Feedback", "Backlog"].index(course["COURSE_STATUS"]), 
                                  key=f"status_{course_id}")
        edit_user = st.text_input("Your Name (for audit)", key=f"edit_user_{course_id}")

        if st.button("Update Course", key=f"update_btn_{course_id}"):
            session.sql(f"""
                UPDATE COURSE_CATALOG
                SET COURSE_DESCRIPTION = '{new_desc}',
                    COURSE_DURATION = {new_dur},
                    COURSE_TYPE = '{new_type}',
                    COURSE_STATUS = '{new_status}',
                    LAST_AMENDED_BY = '{edit_user}',
                    LAST_AMENDED_DATE = CURRENT_TIMESTAMP
                WHERE ID = {course_id}
            """).collect()
            st.success("✅ Course updated.")

    with st.expander("✅ Mark as Reviewed"):
        reviewer = st.text_input("Reviewer Name", key=f"reviewer_{course_id}")
        if st.button("Approve Review", key=f"review_btn_{course_id}"):
            now = datetime.now()
            next_review = now + timedelta(days=180)
            session.sql(f"""
                UPDATE COURSE_CATALOG
                SET LAST_REVIEW_BY = '{reviewer}',
                    LAST_REVIEW_DATE = '{now.date()}',
                    NEXT_REVIEW_DATE = '{next_review.date()}'
                WHERE ID = {course_id}
            """).collect()
            st.success("✅ Course marked as reviewed.")


