import base64
from typing import List, Union, Dict, Any
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

model = "gpt-4o-mini"
llm = ChatOpenAI(model=model)

# Read local image files directly
def read_image_file(file_path):
    """Read image file and convert to base64"""
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

# Image file paths
image_url = "document_analyzer/png_example-1.png"
image_url2 = "document_analyzer/png_example-2.png"
image_url3 = "document_analyzer/png_example-3.png"

# Read image files and convert to base64
image_data = read_image_file(image_url)
image_data2 = read_image_file(image_url2)
image_data3 = read_image_file(image_url3)

# Check if all files were read successfully
if not all([image_data, image_data2, image_data3]):
    print("Some image files could not be read. Please check the file paths.")
    exit(1)

message = "Can you resume the text of the images?"

# Create message with multiple images
content: List[Union[str, Dict[str, Any]]] = [{"type": "text", "text": message}]

# Add images to content if they exist
for i, img_data in enumerate([image_data, image_data2, image_data3], 1):
    if img_data:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_data}"},
        })

message = HumanMessage(content=content)

ai_msg = llm.invoke([message])
print(ai_msg.content)