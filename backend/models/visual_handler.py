import base64
from io import BytesIO
from langchain_core.messages import HumanMessage
# from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

class VisionProcessor:

    def convert_to_base64(self,pil_image):
        """
        Convert PIL images to Base64 encoded strings

        :param pil_image: PIL image
        :return: Re-sized Base64 string
        """

        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")  # You can change the format if needed
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    
    # def build_message(self, text, image_b64):
    #     return [
    #         {
    #             "role": "user",
    #             "content": [
    #                 {"type": "text", "text": text},
    #                 {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
    #             ]
    #         }
    #     ]

    # def prompt_func(self,data):
    #     text = data["text"]
    #     image = data["image"]

    #     image_part = {
    #         "type": "image_url",
    #         "image_url": f"data:image/jpeg;base64,{image}",
    #     }

    #     content_parts = []

    #     text_part = {"type": "text", "text": text}

    #     content_parts.append(image_part)
    #     content_parts.append(text_part)

    #     return [HumanMessage(content=content_parts)]
    
  
    
    def caption_image(self, image):
#     """Process the image and return the response from the VLM."""
        import requests
        image = image.convert("RGB")

        image_b64 = self.convert_to_base64(image)

        # Prepare the prompt
        prompt = f"<image>\n\nExtract only the information that is visibly present in the image. Strictly Do not hallucinate or infer anything that is not clearly shown."

        # Send the request to the model
        payload = {
            "model": "qwen2.5vl:3b",
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "temperature": 0,
        }

        response = requests.post("http://localhost:11434/api/generate", json=payload)
        return response.json().get("response", "No response received.")


vision_processor = VisionProcessor()
def process_image(layout_boxes, image):
    figure_bboxes = [box for box in layout_boxes if box.label in ["Figure", "Picture"]]
    image_captions = []
    for element in figure_bboxes:
        bbox = element.bbox  # Extract the bounding box
        cropped_image = image.crop(bbox)  # Crop the image
        vlm_response = vision_processor.caption_image(cropped_image)  # Process with VLM
        image_captions.append(vlm_response)
    return image_captions  # Return the list of captions



# if __name__ == "__main__":
#     from PIL import Image
#     image_path = r"C:\Users\antony.np\Downloads\test_image.PNG"  # Path to your image
#     image = Image.open(image_path).convert("RGB")
#     vlm_pipeline = VisionProcessor()
#     caption = vlm_pipeline.caption_image(image)
#     print(caption)








