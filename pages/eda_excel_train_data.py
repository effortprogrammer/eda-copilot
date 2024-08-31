import streamlit as st
import pandas as pd
import io
from transformers import AutoTokenizer

def duplicate_excel(df):
    return df.copy(), df.copy()

def get_sheet_names(file):
    return pd.ExcelFile(file).sheet_names

def read_excel(file, sheet_name=None):
    if sheet_name:
        return pd.read_excel(file, sheet_name=sheet_name)
    return pd.read_excel(file)

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
    hf_token = st.text_input("Enter the huggingface token for gated Models")

    if uploaded_file is not None and model_name:
        sheet_names = get_sheet_names(uploaded_file)
    
        if len(sheet_names) > 1:
            selected_sheet = st.selectbox("Select a sheet", sheet_names)
            df = read_excel(uploaded_file, sheet_name=selected_sheet)
        else:
            df = read_excel(uploaded_file)

        # Display original dataframe
        st.subheader("Original DataFrame")
        st.dataframe(df)

        st.success("Excel file uploaded successfully!")

        # Column selection for comparison
        all_columns = df.columns.tolist()

        

        # Column selection for display
        st.subheader("Column Selection for Display")
        selected_columns = st.multiselect("Select columns to display", all_columns)
        # put desired token length here
        token_length = st.number_input("Enter the desired token length", value=3000)
        if selected_columns:
            # Tokenizer and token length calculation
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
            token_lengths = df[selected_columns].map(lambda x: len(tokenizer.tokenize(str(x))))
            
            avg_token_length = token_lengths.mean()
            over_1000_token_ratio = (token_lengths > 1000).mean()

            st.subheader("Token Length Analysis")
            st.write(f"Average token length: {avg_token_length}")
            
            if len(selected_columns) > 1:
                # Calculate token length for each selected column
                token_lengths = {}
                for column in selected_columns:
                    token_lengths[column] = df[column].apply(lambda x: len(tokenizer.tokenize(str(x))))
                
                # Add token lengths to the dataframe
                for column in selected_columns:
                    df[f'{column}_token_length'] = token_lengths[column]
                
                # Calculate total token length for each row
                df['total_token_length'] = df[[f'{col}_token_length' for col in selected_columns]].sum(axis=1)
                
                # Filter rows with total token length over specified token length
                if 'total_token_length' in df.columns:
                    df_over_token_length = df[df['total_token_length'] > token_length]
                    st.write(f"Number of rows with total token length over {token_length}: {len(df_over_token_length)}")
                else:
                    st.write("Total token length column not found in the DataFrame.")
                
                # Display dataframe that overpasses the token length
                st.subheader("DataFrame with Total Token Length Over Specified Token Length")
                st.dataframe(df_over_token_length)
            st.write(f"Ratio of entries with token length over 1000 token: {over_1000_token_ratio}")
            # I want to see the whole dataframe with the token length 
            st.subheader("DataFrame with Token Length")
            st.dataframe(df)
            
if __name__ == "__main__":
    main()