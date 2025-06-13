import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple

class VectorSearch:
    def __init__(self, processed_data_file: str):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.load_data(processed_data_file)
    
    def load_data(self, processed_data_file: str):
        """Load processed data and embeddings"""
        with open(processed_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.processed_data = data['processed_data']
        self.embeddings = np.array(data['embeddings'])
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Search for relevant content using vector similarity"""
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k most similar items
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append((self.processed_data[idx], similarities[idx]))
        
        return results