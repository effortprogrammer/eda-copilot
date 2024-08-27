import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

def read_excel(file, sheet_name=None):
    if sheet_name:
        return pd.read_excel(file, sheet_name=sheet_name)
    return pd.read_excel(file)

def get_column_names(df):
    return df.columns.tolist()

def get_sheet_names(file):
    return pd.ExcelFile(file).sheet_names

st.title('Excel Table Viewer')

uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    sheet_names = get_sheet_names(uploaded_file)
    
    if len(sheet_names) > 1:
        selected_sheet = st.selectbox("Select a sheet", sheet_names)
        df = read_excel(uploaded_file, sheet_name=selected_sheet)
    else:
        df = read_excel(uploaded_file)
    
    columns = get_column_names(df)
    
    selected_column = st.selectbox("Select a column to view", columns)
    
    if selected_column:
        st.subheader(f"HTML Tables in column: {selected_column}")
        
        tables_found = False
        for index, value in df[selected_column].items():
            if isinstance(value, str) and "<table>" in value.lower():
                st.write(f"Row {index}:")
                st.markdown(value, unsafe_allow_html=True)
                tables_found = True
        
        if not tables_found:
            st.write("No HTML tables found in the selected column.")

st.markdown("---")
st.write("Note: Only HTML tables will be displayed if present in the selected column.")
