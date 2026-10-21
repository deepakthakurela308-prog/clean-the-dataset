import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(
    page_title="Clean the Dataset",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 Clean the Dataset")
st.write("Upload, clean and analyze your dataset.")

# Database connection
conn = sqlite3.connect("cleaning_history.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS cleaning_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    original_rows INTEGER,
    cleaned_rows INTEGER,
    duplicates_removed INTEGER,
    missing_values_filled INTEGER,
    created_at TEXT
)
""")
conn.commit()

# Upload CSV file
uploaded_file = st.file_uploader(
    "Upload your CSV dataset",
    type=["csv"]
)

if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file)

        st.subheader("Original Dataset")
        st.dataframe(df, use_container_width=True)

        # Dataset statistics
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Rows", len(df))
        col2.metric("Total Columns", len(df.columns))
        col3.metric(
            "Missing Values",
            int(df.isna().sum().sum())
        )
        col4.metric(
            "Duplicate Rows",
            int(df.duplicated().sum())
        )

        # Data quality report
        st.subheader("Data Quality Report")

        report = pd.DataFrame({
            "Column": df.columns,
            "Data Type": [
                str(df[col].dtype) for col in df.columns
            ],
            "Missing Values": [
                int(df[col].isna().sum()) for col in df.columns
            ],
            "Unique Values": [
                int(df[col].nunique()) for col in df.columns
            ]
        })

        st.dataframe(report, use_container_width=True)

        # Cleaning options
        st.subheader("Cleaning Options")

        fill_missing = st.checkbox(
            "Fill missing values", value=True
        )

        remove_duplicates = st.checkbox(
            "Remove duplicate rows", value=True
        )

        normalize_text = st.checkbox(
            "Remove extra spaces and normalize text",
            value=True
        )

        numeric_method = st.selectbox(
            "Numeric missing values method",
            ["Median", "Mean", "Mode"]
        )

        if st.button("Clean Dataset", type="primary"):

            cleaned_df = df.copy()

            original_rows = len(cleaned_df)
            missing_filled = 0

            # Clean column names
            cleaned_df.columns = [
                str(col).strip()
                for col in cleaned_df.columns
            ]

            # Remove completely empty rows and columns
            cleaned_df = cleaned_df.dropna(how="all")
            cleaned_df = cleaned_df.dropna(
                axis=1, how="all"
            )

            # Remove duplicate rows
            duplicates_removed = 0

            if remove_duplicates:
                before = len(cleaned_df)

                cleaned_df = cleaned_df.drop_duplicates()

                duplicates_removed = (
                    before - len(cleaned_df)
                )

            # Normalize text
            if normalize_text:
                for col in cleaned_df.select_dtypes(
                    include=["object", "string"]
                ).columns:

                    cleaned_df[col] = cleaned_df[col].map(
                        lambda x: x.strip()
                        if isinstance(x, str) else x
                    )

                    if "email" in col.lower():
                        cleaned_df[col] = cleaned_df[col].map(
                            lambda x: x.lower()
                            if isinstance(x, str) else x
                        )

                    elif "city" in col.lower():
                        cleaned_df[col] = cleaned_df[col].map(
                            lambda x: x.title()
                            if isinstance(x, str) else x
                        )

            # Fill missing values
            if fill_missing:
                for col in cleaned_df.columns:

                    count = int(cleaned_df[col].isna().sum())

                    if count == 0:
                        continue

                    if pd.api.types.is_numeric_dtype(
                        cleaned_df[col]
                    ):

                        if numeric_method == "Median":
                            value = cleaned_df[col].median()

                        elif numeric_method == "Mean":
                            value = cleaned_df[col].mean()

                        else:
                            mode = cleaned_df[col].mode()
                            value = (
                                mode.iloc[0]
                                if not mode.empty else 0
                            )

                        if pd.isna(value):
                            value = 0

                    else:
                        mode = cleaned_df[col].mode()

                        value = (
                            mode.iloc[0]
                            if not mode.empty else "Unknown"
                        )

                    cleaned_df[col] = cleaned_df[col].fillna(
                        value
                    )

                    missing_filled += count

            # Display results
            st.subheader("Cleaning Results")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Original Rows", original_rows)
            col2.metric("Cleaned Rows", len(cleaned_df))
            col3.metric(
                "Duplicates Removed", duplicates_removed
            )
            col4.metric(
                "Missing Values Filled", missing_filled
            )

            st.success("Dataset cleaned successfully!")

            st.dataframe(
                cleaned_df,
                use_container_width=True
            )

            # Download cleaned dataset
            csv_data = cleaned_df.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "Download Cleaned Dataset",
                data=csv_data,
                file_name="cleaned_dataset.csv",
                mime="text/csv"
            )

            # Save history in database
            conn.execute("""
                INSERT INTO cleaning_history (
                    filename,
                    original_rows,
                    cleaned_rows,
                    duplicates_removed,
                    missing_values_filled,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                uploaded_file.name,
                original_rows,
                len(cleaned_df),
                duplicates_removed,
                missing_filled,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))

            conn.commit()

            st.success(
                "Cleaning history saved successfully!"
            )

    except Exception as e:
        st.error(f"Error processing dataset: {e}")

# Show cleaning history
st.divider()
st.subheader("Cleaning History")

history = pd.read_sql_query(
    "SELECT * FROM cleaning_history ORDER BY id DESC",
    conn
)

if not history.empty:
    st.dataframe(history, use_container_width=True)
else:
    st.info("No cleaning history available yet.")

conn.close()
