import streamlit as st
import pandas as pd
import io
def read_excel(file):
    return pd.read_excel(file)

def get_column_names(df):
    return df.columns.tolist()

def find_duplicates(df1, df2, column1, column2):
    """
    Find duplicates between two dataframes based on specified columns.

    Parameters:
    - df1 (pandas.DataFrame): First dataframe.
    - df2 (pandas.DataFrame): Second dataframe.
    - column1 (str): Name of the column in df1 to compare.
    - column2 (str): Name of the column in df2 to compare.

    Returns:
    - set: A set containing the values that are duplicates in both dataframes.
    """
    return set(df1[column1]).intersection(set(df2[column2]))

st.title('Excel File Analyzer')

# File uploader
uploaded_files = st.file_uploader("Choose Excel files", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 5:
        st.warning("Maximum 5 files allowed. Only the first 5 will be processed.")
        uploaded_files = uploaded_files[:5]

    # Store dataframes and their column names
    dfs = {}
    column_names = {}

    for file in uploaded_files:
        df = read_excel(file)
        dfs[file.name] = df
        column_names[file.name] = get_column_names(df)

    # Display column names for each file
    for filename, columns in column_names.items():
        st.subheader(f"Columns in {filename}:")
        st.write(", ".join(columns))

    # Duplicate value checker
    st.subheader("Check for duplicate values")
    if len(dfs) >= 2:
        file1 = st.selectbox("Select first file", list(dfs.keys()))
        column1 = st.selectbox("Select column from first file", column_names[file1])
        file2 = st.selectbox("Select second file", [f for f in dfs.keys() if f != file1])
        column2 = st.selectbox("Select column from second file", column_names[file2])

        if st.button("Find Duplicates"):
            duplicates = find_duplicates(dfs[file1], dfs[file2], column1, column2)
            if duplicates:
                st.write(f"Duplicate values found: {', '.join(map(str, duplicates))}")
            else:
                st.write("No duplicate values found.")
    else:
        st.write("Upload at least two files to check for duplicates.")
else:
    st.write("Please upload Excel files to begin analysis.")