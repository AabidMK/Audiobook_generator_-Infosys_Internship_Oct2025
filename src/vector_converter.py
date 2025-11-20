# step2_vector_converter.py
import pandas as pd
import numpy as np
import os
import pickle
import json
from datetime import datetime

class EmbeddingToVectorConverter:
    def __init__(self):
        self.vectors = None
        self.text_chunks = None
        self.dimension = None
        self.metadata = []
    
    def load_embeddings_from_csv(self, csv_file_path):
        """
        Step 2.1.1: Load your embedding CSV and convert to numerical vectors
        """
        print(f"📁 Loading embeddings from: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            print(f"❌ File not found: {csv_file_path}")
            return None, None
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            print(f"✅ CSV loaded successfully")
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            
            # Extract text chunks and embeddings
            self.text_chunks = df['Text'].tolist()
            embedding_strings = df['Embedding'].tolist()
            
            print(f"   Found {len(self.text_chunks)} text chunks")
            print(f"   Found {len(embedding_strings)} embedding strings")
            
            # Convert embedding strings to numerical vectors
            vectors = []
            successful_conversions = 0
            
            for i, embed_str in enumerate(embedding_strings):
                try:
                    if pd.isna(embed_str) or embed_str == '':
                        print(f"⚠ Empty embedding at index {i}, skipping")
                        continue
                    
                    # Convert string to numpy array
                    if isinstance(embed_str, str):
                        # Remove any brackets and split by commas
                        clean_str = embed_str.strip('[]()')
                        vector = np.fromstring(clean_str, sep=',')
                        
                        # Validate vector
                        if len(vector) > 0 and not np.any(np.isnan(vector)):
                            vectors.append(vector)
                            successful_conversions += 1
                            
                            # Store metadata
                            self.metadata.append({
                                'chunk_id': len(vectors) - 1,
                                'original_index': i,
                                'text_length': len(self.text_chunks[i]),
                                'vector_norm': np.linalg.norm(vector),
                                'conversion_success': True
                            })
                        else:
                            print(f"⚠ Invalid vector at index {i}")
                    else:
                        print(f"⚠ Non-string embedding at index {i}: {type(embed_str)}")
                        
                except Exception as e:
                    print(f"❌ Conversion error at index {i}: {e}")
                    self.metadata.append({
                        'chunk_id': i,
                        'original_index': i,
                        'conversion_success': False,
                        'error': str(e)
                    })
            
            # Convert to numpy array
            self.vectors = np.array(vectors)
            self.dimension = self.vectors.shape[1] if len(vectors) > 0 else 0
            
            print(f"\n🎯 CONVERSION SUMMARY:")
            print(f"   Successful conversions: {successful_conversions}/{len(embedding_strings)}")
            print(f"   Final vectors shape: {self.vectors.shape}")
            print(f"   Vector dimension: {self.dimension}")
            print(f"   Data type: {self.vectors.dtype}")
            
            return self.vectors, self.text_chunks
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return None, None
    
    def analyze_vectors(self):
        """
        Step 2.1.2: Analyze the converted vectors
        """
        if self.vectors is None:
            print("❌ No vectors to analyze")
            return
        
        print(f"\n📊 VECTOR ANALYSIS:")
        print(f"   Shape: {self.vectors.shape}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Total vectors: {len(self.vectors)}")
        print(f"   Data type: {self.vectors.dtype}")
        print(f"   Mean: {np.mean(self.vectors):.6f}")
        print(f"   Std: {np.std(self.vectors):.6f}")
        print(f"   Min: {np.min(self.vectors):.6f}")
        print(f"   Max: {np.max(self.vectors):.6f}")
        
        # Show sample vectors
        print(f"\n🔍 SAMPLE VECTORS (first 3):")
        for i in range(min(3, len(self.vectors))):
            print(f"   Vector {i}: {self.vectors[i][:5]}...")  # First 5 dimensions
    
    def save_vectors(self, output_dir="vector_output"):
        """
        Step 2.1.3: Save vectors in multiple formats
        """
        if self.vectors is None:
            print("❌ No vectors to save")
            return None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as pickle (for Python use)
        pickle_path = os.path.join(output_dir, f"vectors_{timestamp}.pkl")
        vector_data = {
            'vectors': self.vectors,
            'text_chunks': self.text_chunks,
            'dimension': self.dimension,
            'metadata': self.metadata,
            'created_at': datetime.now().isoformat()
        }
        
        with open(pickle_path, 'wb') as f:
            pickle.dump(vector_data, f)
        
        # Save as numpy file (for ML applications)
        npy_path = os.path.join(output_dir, f"vectors_{timestamp}.npy")
        np.save(npy_path, self.vectors)
        
        # Save as CSV with reduced precision (for inspection)
        csv_path = os.path.join(output_dir, f"vectors_{timestamp}.csv")
        vector_df = pd.DataFrame(self.vectors)
        vector_df['text_chunk'] = self.text_chunks
        vector_df['chunk_id'] = range(len(self.text_chunks))
        vector_df.to_csv(csv_path, index=False)
        
        # Save metadata
        meta_path = os.path.join(output_dir, f"metadata_{timestamp}.json")
        with open(meta_path, 'w') as f:
            json.dump({
                'total_vectors': len(self.vectors),
                'vector_shape': self.vectors.shape,
                'dimension': self.dimension,
                'conversion_timestamp': datetime.now().isoformat(),
                'files_created': [pickle_path, npy_path, csv_path, meta_path]
            }, f, indent=2)
        
        print(f"\n💾 VECTORS SAVED SUCCESSFULLY:")
        print(f"   Pickle: {pickle_path}")
        print(f"   Numpy: {npy_path}")
        print(f"   CSV: {csv_path}")
        print(f"   Metadata: {meta_path}")
        
        return {
            'pickle': pickle_path,
            'numpy': npy_path,
            'csv': csv_path,
            'metadata': meta_path
        }

# Test function
def test_conversion():
    """Test the vector conversion process"""
    converter = EmbeddingToVectorConverter()
    
    # Find CSV files automatically
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'embedding' in f.lower()]
    
    if not csv_files:
        print("❌ No embedding CSV files found!")
        print("💡 Looking for any CSV files...")
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if csv_files:
        print(f"🔍 Found CSV files: {csv_files}")
        
        # Use the first CSV file found
        target_file = csv_files[0]
        print(f"🎯 Processing: {target_file}")
        
        # Convert embeddings to vectors
        vectors, texts = converter.load_embeddings_from_csv(target_file)
        
        if vectors is not None:
            # Analyze vectors
            converter.analyze_vectors()
            
            # Save vectors
            saved_files = converter.save_vectors()
            
            print(f"\n✅ STEP 2 COMPLETE!")
            print(f"   Your embeddings are now converted to vectors")
            print(f"   Vectors are ready for semantic search and analysis")
            
            return converter, saved_files
        else:
            print("❌ Conversion failed")
            return None, None
    else:
        print("❌ No CSV files found in directory")
        return None, None

if __name__ == "__main__":
    test_conversion()