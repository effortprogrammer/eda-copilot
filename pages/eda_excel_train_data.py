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

def compare_and_modify_columns(df, answer_col, candidate_cols, output_col):
    number_columns = {1: [], 2: [], 3: []}

    for col in df.columns:
        if '1' in col: 
            number_columns[1].append(col)
        if '2' in col: 
            number_columns[2].append(col)
        if '3' in col: 
            number_columns[3].append(col)
    
    # Let user select columns for each number
    selected_columns = {}
    for num, cols in number_columns.items():
        if cols:
            selected_col = st.selectbox(f"Select column for number {num}", cols)
            selected_columns[num] = selected_col
    
    for idx, row in df.iterrows():
        answer = row[answer_col]
        for candidate_col in candidate_cols:
            if row[candidate_col] == answer:
                # Check if the candidate_col contains 1, 2, or 3
                for num in [1, 2, 3]:
                    if str(num) in candidate_col and num in selected_columns:
                        # Move the answer to the selected column
                        tmp = df.at[idx, selected_columns[num]]
                        df.at[idx, selected_columns[num]] = answer
                        df.at[idx, candidate_col] = tmp       
                break
        else:
            # If no match found, add answer to the output column
            df.at[idx, output_col] = row[answer_col]
    return df

def main():
    st.title('Excel File Processor with Column Comparison')

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    model_name = st.text_input("Enter the model name for AutoTokenizer")
    sheet_name = st.text_input("Enter sheet name of the excel file if excel file has multiple sheets")
    hf_token = st.text_input("Enter the huggingface token for gated Models")

    if uploaded_file is not None and model_name:
        # Read the original file
        df_original = pd.read_excel(uploaded_file, sheet_name = sheet_name if sheet_name else 0)

        # Display original dataframe
        st.subheader("Original DataFrame")
        st.dataframe(df_original)

        st.success("Excel file uploaded successfully!")

        # Column selection for comparison
        all_columns = df_original.columns.tolist()
        st.subheader("Column Selection for Comparison")
        answer_column = st.selectbox("Select the answer column", all_columns)
        candidate_columns = st.multiselect("Select the candidate columns (3)", all_columns, max_selections=3)
        output_column = st.selectbox("Select the output column", all_columns)

        if st.button("Compare and Modify Columns"):
            if len(candidate_columns) <= 3:
                df_modified = compare_and_modify_columns(df_original.copy(), answer_column, candidate_columns, output_column)
                st.subheader("Modified DataFrame")
                st.dataframe(df_modified)

                # Download option for modified dataframe
                st.download_button(
                    label="Download Modified DataFrame",
                    data=to_excel(df_modified),
                    file_name="modified_dataframe.xlsx",
                )
            else:
                st.error("Please select exactly 3 candidate columns.")

        # Column selection for display
        st.subheader("Column Selection for Display")
        selected_columns = st.multiselect("Select columns to display", all_columns)

        if selected_columns:
            # Tokenizer and token length calculation
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
            token_lengths = df_original[selected_columns].map(lambda x: len(tokenizer.tokenize(str(x))))
            
            avg_token_length = token_lengths.mean()
            over_1000_token_ratio = (token_lengths > 1000).mean()

            st.subheader("Token Length Analysis")
            st.write(f"Average token length: {avg_token_length}")
            
            # check if selected columns are more than 3
            if len(selected_columns) > 1:
                # Calculate token length for each selected column
                token_lengths = {}
                for column in selected_columns:
                    token_lengths[column] = df_original[column].apply(lambda x: len(tokenizer.tokenize(str(x))))
                
                # Add token lengths to the dataframe
                for column in selected_columns:
                    df_original[f'{column}_token_length'] = token_lengths[column]
                
                # Calculate total token length for each row
                df_original['total_token_length'] = df_original[[f'{col}_token_length' for col in selected_columns]].sum(axis=1)
                
                # Filter rows with total token length over 3000
                df_over_3000 = df_original[df_original['total_token_length'] > 3000]
                
                st.subheader("Rows with total token length over 3000")
                st.dataframe(df_over_3000)
                
                # Display updated dataframe with token lengths
                st.subheader("Updated DataFrame with Token Lengths")
                st.dataframe(df_original)
            st.write(f"Ratio of entries with token length over 1000 token: {over_1000_token_ratio}")
        
        # Create two duplicates
        df_copy1, df_copy2 = duplicate_excel(df_original)
        
        # Display the duplicated dataframes
        st.subheader("Duplicated DataFrame 1")
        st.dataframe(df_copy1)

        st.subheader("Duplicated DataFrame 2")
        st.dataframe(df_copy2)

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