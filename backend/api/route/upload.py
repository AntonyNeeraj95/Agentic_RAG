from backend.models.document_handler import DocumentProcess
from fastapi import APIRouter, UploadFile, File
from backend.models.file_handler import FileHandler
from backend.models.visual_handler import process_image
from fastapi import HTTPException
import tempfile
import os
from uuid import uuid4
from langchain_core.documents import Document

router = APIRouter(tags=["upload"])

@router.post("/upload/pdf")
async def upload_file(
    file: UploadFile = File(media_type="application/pdf", description="The PDF file to upload"),
):
    from backend.server import app
    # Handle temp file
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Save uploaded PDF to disk
            file_location = os.path.join(temp_dir, file.filename)
            with open(file_location, "wb") as f:
                content = await file.read()
                f.write(content)

            # Initialize handler (replace these IDs as needed)
            handler = DocumentProcess(
                file_name=file.filename,
                doc_id=str(uuid4()),
                user_id="user_id",
                chunk_size=600,
                chunk_overlap=200,
                batch_size=100,
                embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )

            processor = app.state.processor

            upload_dir = f"uploads/{uuid4()}"
            os.makedirs(upload_dir, exist_ok=True)

            # Convert PDF to images
            images = FileHandler(file=content, file_path=file.filename).pdf_to_images()
            all_captions = []

            for i, image in enumerate(images):
                page_path = os.path.join(upload_dir, f"{i}.png")
                image.save(page_path)

                # Detect layout using SuryaProcessor
                print("detecting layout")
                layout_bboxes = processor.detect_layout(image)

                # Process text excluding figures and upsert
                process_text = processor.process_text(image, layout_bboxes)
                print("processing text")
                chunks = await handler.load_document_chunks(process_text)
                await handler.upsert_embeddings(chunks)

                # Process image for visual captioning
                image_captions = process_image(layout_bboxes, image)
                all_captions.extend(image_captions)
                for caption in image_captions:
                    doc = [Document(page_content=caption)]
                    await handler.upsert_embeddings(doc)

            return {"status": "success", "image_dir": upload_dir, "captions": all_captions}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))