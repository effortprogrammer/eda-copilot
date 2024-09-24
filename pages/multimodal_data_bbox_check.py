# input: compressed .zip file 
# output: image with bbox 

# zip 파일이 들어오면 형식이 잘 맞았다는 가정 하에 형식에 맞게 데이터 형식 맞춰서 딱딱딱 들어오고 이미지 딱 띄우고 본문 띄우면 
# 바운딩 박스 잘 들어와 있는지 바로 확인하는 프로그램 

import streamlit as st
import zipfile
import io
import os
from PIL import Image, ImageDraw

def extract_images(zip_file):
    image_files = []
    with zipfile.ZipFile(zip_file, 'r') as z:
        for file_name in z.namelist():
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(file_name)
    return image_files

def draw_bounding_box(image, bbox):
    draw = ImageDraw.Draw(image)
    draw.rectangle(bbox, outline="red", width=2)
    return image

st.title('Multimodal Data Bounding Box Check')

uploaded_file = st.file_uploader("Upload a ZIP file containing images", type="zip")

if uploaded_file is not None:
    image_files = extract_images(uploaded_file)
    
    if image_files:
        st.write(f"Found {len(image_files)} image(s) in the ZIP file.")
        
        selected_image = st.selectbox("Select an image to view", image_files)
        
        st.write("Enter bounding box coordinates in the following order:")
        st.write("[Top-X, Top-Y, Bottom-X, Bottom-Y]")
        
        bbox = st.text_input("Bounding Box Coordinates", "0,0,100,100")
        bbox = [int(coord.strip()) for coord in bbox.split(',')]
        
        if len(bbox) == 4:
            with zipfile.ZipFile(uploaded_file, 'r') as z:
                image_data = z.read(selected_image)
                image = Image.open(io.BytesIO(image_data))
                
                image_with_bbox = draw_bounding_box(image.copy(), bbox)
                st.image(image_with_bbox, caption=f"Image: {selected_image} with Bounding Box")
        else:
            st.error("Please enter 4 coordinates for the bounding box.")
    else:
        st.write("No image files found in the uploaded ZIP file.")
else:
    st.write("Please upload a ZIP file containing images.")
