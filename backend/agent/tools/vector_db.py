import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# 1. Load and Split PDF
loader = PyPDFLoader("data/FIL_Stock Market.pdf")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunks")

# 2. Embedding model
print("Loading embedding model...")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# 3. Initialize Pinecone
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY") or os.environ.get("PINECONE_API"))
index = pc.Index("chat-bot")

# 4. Embed and build vectors
print("Embedding chunks...")
vectors = []
for i, chunk in enumerate(chunks):
    vector = embeddings.embed_query(chunk.page_content)
    vectors.append({
        "id": f"chunk-{i}",
        "values": vector,
        "metadata": {
            "text": chunk.page_content,
            "page": chunk.metadata.get("page"),
            "source": chunk.metadata.get("source"),
        }
    })

# 5. Upsert in batches
batch_size = 100
print(f"Upserting {len(vectors)} vectors to Pinecone...")
for i in range(0, len(vectors), batch_size):
    index.upsert(vectors=vectors[i:i+batch_size], namespace="default")
    print(f"  Uploaded batch {i//batch_size + 1}")

print("Upload Complete ✅")