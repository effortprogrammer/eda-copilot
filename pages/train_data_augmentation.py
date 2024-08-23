import streamlit as st
import pandas as pd
import io
from transformers import AutoTokenizer

def duplicate_excel(df):
    return df.copy(), df.copy()

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title('Excel File Duplicator and Column Selector')

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    model_name = st.text_input("Enter the model name for AutoTokenizer")
    hf_token = st.text_input("Enter the huggingface token for gated Models")


    if uploaded_file is not None and model_name:
        # Read the original file
        df_original = pd.read_excel(uploaded_file)
        
        # Create two duplicates
        df_copy1, df_copy2 = duplicate_excel(df_original)

        st.success("Excel file duplicated successfully!")

        # Display original and duplicated dataframes
        st.subheader("Original DataFrame")
        st.dataframe(df_original)

        st.subheader("Duplicate 1")
        st.dataframe(df_copy1)

        st.subheader("Duplicate 2")
        st.dataframe(df_copy2)

        # Column selection
        st.subheader("Column Selection")
        all_columns = df_original.columns.tolist()
        selected_columns = st.multiselect("Select columns to display", all_columns)

        if selected_columns:
            st.subheader("Selected Columns from All DataFrames")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("Original")
                st.dataframe(df_original[selected_columns])
            
            with col2:
                st.write("Duplicate 1")
                st.dataframe(df_copy1[selected_columns])
            
            with col3:
                st.write("Duplicate 2")
                st.dataframe(df_copy2[selected_columns])

            # Tokenizer and token length calculation
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
            token_lengths = df_original[selected_columns].map(lambda x: len(tokenizer.tokenize(str(x))))
            
            # if token_lengths are longer than 1000, print the entry
            st.subheader("Entries with token length over 1000")
            st.write(df_original[selected_columns][token_lengths > 1000])
            avg_token_length = token_lengths.mean()
            over_1000_token_ratio = (token_lengths > 1000).mean()

            st.subheader("Token Length Analysis")
            st.write(f"Average token length: {avg_token_length}")
            st.write(f"Ratio of entries with token length over 1000 token: {over_1000_token_ratio}")

        # Download options
        st.subheader("Download Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="Download Original",
                data=to_excel(df_original),
                file_name="original.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col2:
            st.download_button(
                label="Download Duplicate 1",
                data=to_excel(df_copy1),
                file_name="duplicate1.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col3:
            st.download_button(
                label="Download Duplicate 2",
                data=to_excel(df_copy2),
                file_name="duplicate2.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()