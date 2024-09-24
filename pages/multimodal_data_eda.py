import streamlit as st
import zipfile
import io
import os
from PIL import Image, ImageDraw
import json

def extract_file_structure(zip_file):
    file_structure = {}
    with zipfile.ZipFile(zip_file, 'r') as z:
        for file_name in z.namelist():
            directory = os.path.dirname(file_name)
            if directory not in file_structure:
                file_structure[directory] = []
            file_structure[directory].append(os.path.basename(file_name))
    return file_structure

def draw_bounding_box(image, bbox):
    draw = ImageDraw.Draw(image)
    # Convert top-x, top-y, bottom-x, bottom-y to left, top, right, bottom
    left, top, right, bottom = bbox[0], bbox[1], bbox[2], bbox[3]
    draw.rectangle([left, top, right, bottom], outline="red", width=2)
    return image

def process_json_file(zip_file, json_path):
    with zipfile.ZipFile(zip_file, 'r') as z:
        json_data = json.loads(z.read(json_path))
    return json_data

def get_image_from_zip(zip_file, image_path):
    with zipfile.ZipFile(zip_file, 'r') as z:
        image_data = z.read(image_path)
        return Image.open(io.BytesIO(image_data))

def display_json_data(json_data, file_structure, uploaded_file):
    columns = list(json_data.keys())
    selected_column = st.selectbox("Select a column from JSON", columns)
    if selected_column:
        st.write(f"Value of '{selected_column}':")
        st.write(json_data[selected_column])
        if 'bounding_box' in json_data[selected_column]:
            bbox = json_data[selected_column]['bounding_box']
            if isinstance(bbox, list) and len(bbox) == 4:
                st.session_state.bbox = bbox
                st.success("Bounding box coordinates loaded from JSON.")
                
                # Ask the file directory again
                selected_directory = st.selectbox("Select a directory for images", list(file_structure.keys()))
                
                if selected_directory:
                    files = file_structure[selected_directory]
                    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    
                    # Let user choose image file
                    if image_files:
                        selected_image = st.selectbox("Select an image file", image_files)
                        image_path = os.path.join(selected_directory, selected_image)
                        
                        # Execute display_image_with_bbox function
                        display_image_with_bbox(uploaded_file, image_path)
                    else:
                        st.warning("No image files found in the selected directory.")
            else:
                st.warning("Invalid bounding box format in JSON.")

def display_image_with_bbox(zip_file, image_path):
    st.write("Enter bounding box coordinates in the following order:")
    st.write("[top-x, top-y, bottom-x, bottom-y]")
    
    default_bbox = ",".join(map(str, st.session_state.get('bbox', [0, 0, 100, 100])))
    bbox_input = st.text_input("Bounding Box Coordinates", value=default_bbox)
    
    try:
        bbox = [int(coord.strip()) for coord in bbox_input.split(',')]
        if len(bbox) != 4:
            raise ValueError
    except ValueError:
        st.error("Please enter 4 valid integer coordinates for the bounding box.")
        return

    image = get_image_from_zip(zip_file, image_path)
    image_with_bbox = draw_bounding_box(image.copy(), bbox)
    st.image(image_with_bbox, caption=f"Image: {image_path} with Bounding Box")

def main():
    st.title('Multimodal Data Bounding Box Check')

    if 'bbox' not in st.session_state:
        st.session_state.bbox = [0, 0, 100, 100]

    uploaded_file = st.file_uploader("Upload a ZIP file containing images", type="zip")

    if uploaded_file is not None:
        file_structure = extract_file_structure(uploaded_file)
        
        if file_structure:
            selected_directory = st.selectbox("Select a directory", list(file_structure.keys()))
            
            if selected_directory:
                files = file_structure[selected_directory]
                json_files = [f for f in files if f.endswith('.json')]
                
                if json_files:
                    selected_json = st.selectbox("Select a JSON file", json_files)
                    json_path = os.path.join(selected_directory, selected_json)
                    json_data = process_json_file(uploaded_file, json_path)
                    
                    if json_data:
                        display_json_data(json_data, file_structure, uploaded_file)
                else:
                    st.warning("No JSON files found in the selected directory.")
        else:
            st.write("No files found in the uploaded ZIP file.")
    else:
        st.write("Please upload a ZIP file.")

if __name__ == "__main__":
    main()