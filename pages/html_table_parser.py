import streamlit as st
import pandas as pd
import json
import re
import io
from bs4 import BeautifulSoup
import numpy as np
import random
import plotly.graph_objects as go
import ast 

# 여기에 제공된 함수들을 붙여넣습니다 (space_norm, parse_html_to_json, process_innermost_tables, substitute_function_convert, process_nested_tables)

space_norm = re.compile("[ ]{2,}")

def parse_html_to_json(html_table_str):
    """
    HTML 형식의 "단일" 표를 찾아서 JSON으로 파싱하는 함수
    """
    soup = BeautifulSoup(html_table_str, "html.parser")
    soup_table_tag = soup.find("table")
    tr_tag_ls = soup_table_tag.find_all("tr")

    # 빈 테이블(<table></table>)이나 thead가 있는 데이터는 처리하지 않음   
    if (not tr_tag_ls) or ("<thead>" in html_table_str): 
        if "<thead>" in html_table_str:
            return html_table_str
        return ""

    # 테이블 정규화
    fisrt_row_tag, table_row_num = (tr_tag_ls[0], len(tr_tag_ls))
    df_table = pd.read_html(io.StringIO(str(soup_table_tag)), keep_default_na=False)[0]
    # 아래 코드는 applymap으로 대체
    # df_table = df_table.apply(lambda row: row.map(lambda cell: space_norm.sub(" ", cell.strip())))
    def normalize_cell(cell):
        if isinstance(cell, str):
            return space_norm.sub(" ", cell.strip())
        return str(cell)
    df_table = df_table.applymap(normalize_cell)

    norm_table_tag = BeautifulSoup(df_table.to_html(index=False), "html.parser")
    thead_tag = norm_table_tag.find("thead")
    thead_tag.decompose()
    
    # 표의 형태에 따라서 특수 케이스는 따로 분리해서 처리한다.
    row_n, col_n = df_table.shape

    # 특수 케이스 1: 열이 하나이거나, 행이 하나인 표
    # 이 경우 표의 값들을 순서대로 나열하고, 개행 문자로 각 값들을 구분하도록 변경된다.
    if row_n == 1 or col_n == 1:
        tr_ls = (df_table.values.T if col_n == 1 else df_table.values).tolist()
        tr_ls = sum(tr_ls, [])
        return "\n".join(dict.fromkeys(tr_ls))
    
    # 득수 케이스 2: 
    # 표의 열이 총 2개이고, 두번째 열의 첫번째 셀 길이가 70 이상일 경우 특수 케이스 2에 해당된다.
    # 예시: 
    # | 법률 | 대충법률에대한아주긴내용... |
    # | 시행 | 대충시행에대한아주긴내용... |
    # | 지침 | 대충지침에대한아주긴내용... |

    # 먼저 첫번째 열에 rowspan이 있는지 확인하는 rowspan_ls 리스트를 만든다.
    td_ls = fisrt_row_tag.find_all("td")
    rowspan_ls = [-100]
    for td in td_ls:
        rowspan = td.get("rowspan")
        if not (rowspan and (int(rowspan) < table_row_num)):
            rowspan_ls.append(-100)
            continue
        rowspan_ls.append(int(rowspan))
    
    # 첫번째 열에 rowspan이 하나라도 있을 경우 특수 케이스 2로 분류되지 않는다.
    if -100 == max(rowspan_ls):
        row_n, col_n = df_table.shape
        # second_column_lengths = df_table.iloc[:, -1].astype(str).apply(len)
        # 표에 열이 총 2개이며, 두번째 열의 첫번째 셀 길이가 70 이상인지 감지한다.
        if col_n == 2 and len(df_table.iloc[0, -1]) >= 70:
            columns_ls = [row[0] for row in df_table.values.tolist()]
            content_ls = [row[1] for row in df_table.values.tolist()]
            output_dict = dict()
            for col_name, con in zip(columns_ls, content_ls):
                if col_name not in output_dict:
                    output_dict[col_name] = []
                output_dict[col_name].append(con)
            output_dict = {k: v for k, v in output_dict.items() if v[0]}
            return json.dumps(output_dict, ensure_ascii=False)
        rowspan_ls.append(1)
    
    # 그 외의 케이스를 처리한다.
    column_idx = max(rowspan_ls)
    table_ls = [[x.text for x in tr.find_all("td")] for tr in norm_table_tag.find_all("tr")]
    columns_ls = np.array(table_ls[:column_idx]).T
    table_ls = table_ls[column_idx:]
    norm_columns = [".".join(dict.fromkeys(col_ls)) for col_ls in columns_ls]
    output_list = []
    for row in table_ls:
        row_dict = {}
        for col, cell in zip(norm_columns, row):
            if cell:
                # 이미 col 값이 row_dict에 존재하는 경우, 이미 존재하는 값 뒤에 합친다.
                # 두 값은 ,로 구분한다.
                if col in row_dict:
                    # 만약 이미 존재하는 값이 cell 값으로 끝나면, 또 붙일 필요가 없으므로 패스한다.
                    if not row_dict[col].endswith(cell):
                        row_dict[col] += f", {cell}"
                else:
                    row_dict[col] = cell
        if row_dict:
            output_list.append(row_dict)
    return json.dumps(output_list, ensure_ascii=False)


def process_innermost_tables(input_string):
    """
    입력된 문자열 중 가장 안쪽에 있는 <table></table>을 감지하여, 감지된 부분을 substitute_function_convert 함수의 리턴값으로 대체한다.
    정확히는, 문자열에서 가장 마지막에 존재하는 <table>과 그 뒤에 있는 첫번째 </table>을 감지한다.
    """
    try:
        return re.sub(r'<table>(?![^<]*<table)[^<]*(?:<(?!table)[^<]*)*?</table>', substitute_function_convert, input_string)
    except:
        print("============================================")
        print("something went wrong here: ")
        print(input_string)
        return input_string

def substitute_function_convert(match):
    """
    process_innermost_tables에서 매치된 부분을 parse_html_to_json 함수에 집어넣는다.
    """
    table_content = match.group(0)
    return parse_html_to_json(table_content)

def process_nested_tables(input_string):
    """
    문자열 안에 <table>이 더 이상 남지 않을 때 까지 process_innermost_tables를 통과시킨다.
    """
    if type(input_string) != type("string"):
        return input_string
    
    MAX_NEST_COUNT = 10
    curr = 0
    while '<table>' in input_string and curr < MAX_NEST_COUNT:
        input_string = process_innermost_tables(input_string)
        curr += 1
    return input_string


import streamlit as st
import pandas as pd
import random
from bs4 import BeautifulSoup

def display_html_table(html_string):
    """
    Display an HTML table string as an actual table in Streamlit
    """
    st.markdown(html_string, unsafe_allow_html=True)

def main():
    st.title('HTML Table Extractor and Display')

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        
        st.subheader("Original Data")
        st.dataframe(df)

        # Find columns containing "<tr>"
        columns_with_tables = [col for col in df.columns if df[col].astype(str).str.contains("<tr>").any()]
        
        if columns_with_tables:
            selected_column = st.selectbox("Select a column containing HTML tables", columns_with_tables)
            
            # Filter rows containing "<tr>" in the selected column
            rows_with_tables = df[df[selected_column].astype(str).str.contains("<tr>")]
            
            if not rows_with_tables.empty:
                # Randomly select up to 5 rows
                sample_size = min(5, len(rows_with_tables))
                random_rows = rows_with_tables.sample(n=sample_size)
                
                st.subheader(f"Randomly Selected HTML Tables from '{selected_column}'")
                for index, row in random_rows.iterrows():
                    html_content = row[selected_column]
                    
                    # Clean and format the HTML content
                    soup = BeautifulSoup(html_content, 'html.parser')
                    table = soup.find('table')
                    if table:
                        # Add Bootstrap classes for better styling
                        table['class'] = table.get('class', []) + ['table', 'table-bordered', 'table-striped']
                        formatted_html = str(table)
                        
                        st.subheader(f"Table {index + 1}")
                        display_html_table(formatted_html)
                    else:
                        st.warning(f"No valid table found in row {index}")
            else:
                st.warning(f"No rows containing HTML tables found in the selected column '{selected_column}'")
        else:
            st.warning("No columns containing HTML tables found in the uploaded file")

if __name__ == "__main__":
    main()