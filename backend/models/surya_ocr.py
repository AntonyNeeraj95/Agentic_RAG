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

