import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import uuid

# Initialize Chroma client
client = chromadb.Client()

# Create or get a collection
collection_name = "my_embeddings_collection"
if collection_name in [col.name for col in client.list_collections()]:
    collection = client.get_collection(collection_name)
else:
    collection = client.create_collection(name=collection_name)

csv_files = [
    "sample1_embeddings_table.csv",
    "sample2_embeddings_table.csv",
    "sample3_embeddings_table.csv",
    "sample4_embeddings_table.csv"
]

for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    print(f"Processing {csv_file} with columns: {df.columns}")

    # Normalize column names to lowercase
    df.columns = [c.lower() for c in df.columns]

    ids = [str(uuid.uuid4()) for _ in range(len(df))]
    embeddings = df['embedding'].apply(eval).tolist()
    documents = df['text'].tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents
    )
    print(f"Added {len(df)} embeddings from {csv_file}.")

print("Total stored embeddings in collection:", collection.count())
