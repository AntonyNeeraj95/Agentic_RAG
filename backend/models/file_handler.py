from pdf2image import convert_from_bytes

class FileHandler:
    def __init__(self, file_path:str, file):
        self.file_path = file_path
        self.file = file
   
    def pdf_to_images(self):
        if self.file_path.endswith('.pdf'):
            images = convert_from_bytes(self.file)
            
            return images
        else:
            raise ValueError("Unsupported file type")