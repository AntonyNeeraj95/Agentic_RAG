from PIL import Image
from surya.layout import LayoutPredictor
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from typing import List


class SuryaProcessor:
    def __init__(self):
        # Initialize models ONCE
        self.layout_predictor = LayoutPredictor()
        self.foundation_predictor = FoundationPredictor()
        self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
        self.detection_predictor = DetectionPredictor()

    def detect_layout(self, image):
        """Run layout detection and return all bounding boxes."""
        return self.layout_predictor([image])[0].bboxes

    def process_text(self, image, layout_bboxes):
        """Extract text excluding 'Figure' regions."""

        non_figure_bboxes = [box for box in layout_bboxes if box.label not in ["Figure"]]

        # # Run OCR **once** on full image
        predictions = self.recognition_predictor(
            [image], det_predictor=self.detection_predictor
        )

        extracted_text = ""

        # Filter OCR lines that lie inside non-figure bboxes
        for page in predictions:
            for line in page.text_lines:
                # Line center point
                x_center = (line.bbox[0] + line.bbox[2]) / 2
                y_center = (line.bbox[1] + line.bbox[3]) / 2

                # Keep if inside any non-figure bbox
                if any(
                    (box.bbox[0] <= x_center <= box.bbox[2])
                    and (box.bbox[1] <= y_center <= box.bbox[3])
                    for box in non_figure_bboxes
                ):
                    extracted_text += "".join([c.text for c in line.chars]) + "\n"

        return extracted_text.strip()
    
    def extract_bboxes_polygons(self,layout_boxes) -> List[List[List[int]]]:
        bboxes: List[List[List[int]]] = []
        # polygons: List[List[List[List[int]]]] = []

        for box in layout_boxes:
            # Convert bbox values to integers
            bbox_int = [int(round(coord)) for coord in box.bbox]
            bboxes.append([bbox_int])  # shape: List[List[int]]

        return bboxes


if __name__ == "__main__":
    import time

    start_time = time.time()
    processor = SuryaProcessor()
    print("Loading models took:", time.time() - start_time, "seconds")
    image_path = r"C:\Users\antony.np\Downloads\text_image.jpg"
    image = Image.open(image_path).convert("RGB")
    layout_bboxes = processor.detect_layout(image)
    text_output = processor.process_text(image, layout_bboxes)
    print("Extracted Text (excluding Figures):\n", text_output)
    print("Total time taken:", time.time() - start_time, "seconds") 
        
        
        # Run table recognition
    # table_rec = TableRecPredictor()
    # ocr_rec = RecognitionPredictor(FoundationPredictor())
    # table_predictions = table_rec([image])
    # table_info = table_predictions[0]

    # # Example access:
    # print("Detected", len(table_info.rows), "rows and", len(table_info.cols), "columns.")
    # results = []
    # for cell in table_info.cells:
    #     bbox_list = [[cell.bbox[0], cell.bbox[1], cell.bbox[2], cell.bbox[3]]]

    #     ocr_result = ocr_rec([image], bboxes=[bbox_list])

    #     if ocr_result and ocr_result[0].text_lines:
    #         text = " ".join(line.text for line in ocr_result[0].text_lines).strip()
    #     else:
    #         text = ""

    #     results.append({
    #         "row": cell.row_id,
    #         "col": cell.col_id,
    #         "text": text
    #     })
    # # ===== Step 3: Save / print as JSON =====
    # print(json.dumps(results, indent=2, ensure_ascii=False))


    

