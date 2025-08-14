from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime
from transformers import AutoTokenizer
from langchain_core.documents import Document
from backend.db.qdrant_db import add_documents

def sse_events(event: str, data: dict):
    return {
        "event": event,
        "data": data,
    }

class DocumentProcess:
    def __init__(
            self,
            file_name:str,
            doc_id: str,
            user_id: str,
            chunk_size: int = 600,
            chunk_overlap: int = 200,
            batch_size: int = 100,
            embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            # embedding_class: Literal["openai", "huggingface", "fake"] = "openai",
        ):
        self.file_name = file_name
        self.doc_id = doc_id
        self.user_id = user_id
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        self.embedding_model = embedding_model
        # self.embedding_class = embedding_class

    def document_loader(self,document):

        return [Document(page_content=document)]

    def document_splitter(self):
        tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
        splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=tokenizer,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return splitter

    @staticmethod
    def document_chunking(docs, splitter):
        # docs: List[Document]
        chunks = splitter.split_documents(docs)
        return chunks

    async def load_document_chunks(self,document):
        docs = self.document_loader(document)
        splitter = self.document_splitter()
        chunks = self.document_chunking(docs, splitter)
        return chunks

    async def upsert_embeddings(self, chunks):

        document_metadata = {
            "doc_id": self.doc_id,
            "user_id": self.user_id,
            "filename": self.file_name,
            "timestamp": datetime.now().isoformat(),
        }
        for chunk in chunks:
            chunk.metadata = document_metadata
        await add_documents(chunks)

    async def process_pdf(self,document):
        try:
            yield sse_events("processing", {"message": "completed", "progress": 25})
            chunks = await self.load_document_chunks(document)
            print("chunking done")
            yield sse_events("processing", {"message": "completed", "progress": 50})
            await self.upsert_embeddings(chunks)
            print("embedding done")
            yield sse_events("processing", {"message": "completed", "progress": 100})
            print("processing done")
        except Exception as e:
            print(f"Error processing PDF: {e}")