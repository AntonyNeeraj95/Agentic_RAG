import base64
from io import BytesIO

import os
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

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

        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
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







