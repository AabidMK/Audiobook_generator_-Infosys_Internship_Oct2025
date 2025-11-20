# analyze_embeddings.py
import pandas as pd
import numpy as np
import os

def analyze_embedding_file(csv_file_path):
    """Analyze your current embedding CSV format"""
    print(f"🔍 Analyzing: {csv_file_path}")
    
    # Read the CSV
    df = pd.read_csv(csv_file_path)
    
    print("📊 DataFrame Info:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   First few rows:")
    print(df.head(3))
    
    # Check embedding format
    if 'Embedding' in df.columns:
        sample_embedding = df['Embedding'].iloc[0]
        print(f"\n🧮 Embedding Format Analysis:")
        print(f"   Type: {type(sample_embedding)}")
        print(f"   Sample: {sample_embedding[:100]}...")
        
        # Try to parse the embedding string
        try:
            # If it's string representation of list
            if isinstance(sample_embedding, str):
                vector = np.fromstring(sample_embedding.strip('[]'), sep=',')
                print(f"   Parsed vector shape: {vector.shape}")
                print(f"   First 5 values: {vector[:5]}")
        except Exception as e:
            print(f"   Parsing error: {e}")
    
    return df

# Run analysis on your embedding file
if __name__ == "__main__":
    # Replace with your actual embedding CSV file path
    embedding_file = "sample_EXTRACTED_embeddings_table.csv"  # Change this
    if os.path.exists(embedding_file):
        analyze_embedding_file(embedding_file)
    else:
        print(f"❌ File not found: {embedding_file}")
        print("Looking for embedding files...")
        for file in os.listdir('.'):
            if 'embed' in file.lower() or '.csv' in file:
                print(f"Found: {file}")