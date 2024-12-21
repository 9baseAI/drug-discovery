import glob
import os
from typing import List, Dict

from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams
from tqdm import tqdm

from llms.llm import embedding_model


class PDFProcessor:
    def __init__(
            self,
            embedding_model: OpenAIEmbeddings,
            qdrant_client: QdrantClient,
            collection_name: str,
            text_splitter: RecursiveCharacterTextSplitter,
    ):
        self.embedding_model = embedding_model
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.text_splitter = text_splitter

        # Initialize Qdrant collection
        self._initialize_qdrant_collection()

    def _initialize_qdrant_collection(self):
        # Recreate the collection to ensure it's fresh
        self.qdrant_client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=1536,  # Ensure this matches the embedding size
                distance="Cosine",
            ),
        )
        print(f"Qdrant collection '{self.collection_name}' is set up.")

    def process_pdf(self, file_path: str) -> List[Document]:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        processed_pages = []

        for page in pages:
            # Ensure 'source' and 'page_number' are in metadata
            metadata = page.metadata.copy() if page.metadata else {}
            metadata['source'] = metadata.get('source', file_path)
            metadata['page_number'] = metadata.get('page', None)
            processed_page = Document(page_content=page.page_content, metadata=metadata)
            processed_pages.append(processed_page)

        return processed_pages

    def process_folder(self, folder_path: str) -> List[Document]:
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        all_processed_pages = []

        if pdf_files:
            print(f"Found {len(pdf_files)} PDF file(s).")
            for file in tqdm(pdf_files, desc="Processing PDF files"):
                print(f"Processing file: {file}")
                processed_pages = self.process_pdf(file)
                all_processed_pages.extend(processed_pages)
        else:
            print("No PDF files found in the specified folder.")

        return all_processed_pages

    def split_text(self, documents: List[Document]) -> List[Document]:
        splits = []
        for doc in tqdm(documents, desc="Splitting documents into chunks"):
            split_docs = self.text_splitter.split_documents([doc])
            splits.extend(split_docs)
        return splits

    def insert_documents(self, documents: List[Dict], embedder: OpenAIEmbeddings):
        points = []
        for idx, doc in enumerate(tqdm(documents, desc="Embedding and preparing points")):
            vector = embedder.embed_query(doc['content'])  # Generate embedding
            point = PointStruct(
                id=idx,  # Unique ID for each chunk
                vector=vector,
                payload={
                    'source': doc['source'],
                    'page_number': doc['page_number'],
                    'page_content': doc['content'],

                }
            )
            points.append(point)

        batch_size = 100
        for i in tqdm(range(0, len(points), batch_size), desc="Uploading points to Qdrant"):
            batch = points[i: i + batch_size]
            try:
                self.qdrant_client.upsert(collection_name=self.collection_name, points=batch)
            except Exception as e:
                print(f"Error upserting batch starting at index {i}: {e}")

        print("All data has been successfully saved to Qdrant!")

    def run(self, folder_path: str):
        processed_pages = self.process_folder(folder_path)

        if not processed_pages:
            print("No pages to process. Exiting.")
            return

        splits = self.split_text(processed_pages)

        if not splits:
            print("No splits generated. Exiting.")
            return

        dict_documents = []
        for split in splits:
            doc_dict = {
                'source': split.metadata.get('source', 'unknown'),
                'page_number': split.metadata.get('page_number', 'unknown'),
                'content': split.page_content,
            }
            dict_documents.append(doc_dict)

        if not dict_documents:
            print("No documents to insert. Exiting.")
            return

        # Step 5: Embed and upload to Qdrant
        self.insert_documents(dict_documents, self.embedding_model)


if __name__ == "__main__":
    base_url = "https://api.avalai.ir/v1"
    model_name = "gpt-4o-mini"
    openai_api_key = "aa-prdbCYMqioSYLjEbugKyHLXhiEveo11mYUptKbhX0XQjkUqp"
    qdrant_host = "localhost"
    qdrant_port = 6333

    folder_path = "."

    qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=300,
        length_function=len,
        is_separator_regex=False,
    )

    pdf_processor = PDFProcessor(
        embedding_model=embedding_model,
        qdrant_client=qdrant_client,
        collection_name='medicinal_chemistry_docs',
        text_splitter=text_splitter,
    )

    pdf_processor.run(folder_path)
