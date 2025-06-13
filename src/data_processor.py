import json
import os
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class DataProcessor:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.processed_data = []
        self.embeddings = None
        
    def process_discourse_data(self, discourse_file: str) -> List[Dict]:
        """Process discourse posts into searchable chunks"""
        with open(discourse_file, 'r', encoding='utf-8') as f:
            discourse_data = json.load(f)
        
        processed_posts = []
        
        for post in discourse_data:
            # Extract relevant information
            topic_title = post.get('topic_title', '')
            topic_url = f"https://discourse.onlinedegree.iitm.ac.in/t/{post.get('topic_slug', '')}/{post.get('topic_id', '')}"
            
            # Process each post in the topic
            posts = post.get('post_stream', {}).get('posts', [])
            for p in posts:
                content = p.get('cooked', '') or p.get('raw', '')
                if content:
                    # Clean HTML content
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                    if len(content) > 50:  # Only include substantial content
                        processed_posts.append({
                            'content': content,
                            'title': topic_title,
                            'url': topic_url,
                            'post_number': p.get('post_number', 1),
                            'source': 'discourse',
                            'full_url': f"{topic_url}/{p.get('post_number', 1)}"
                        })
        
        return processed_posts
    
    def process_course_content(self, md_folder: str) -> List[Dict]:
        """Process markdown course content"""
        processed_content = []
        
        for filename in os.listdir(md_folder):
            if filename.endswith('.md'):
                filepath = os.path.join(md_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split content into sections
                sections = self.split_markdown_content(content)
                
                for section in sections:
                    if len(section['content']) > 100:
                        processed_content.append({
                            'content': section['content'],
                            'title': section['title'],
                            'url': f"https://tds.s-anand.net/#/{filename.replace('.md', '').replace('_', '-').lower()}",
                            'source': 'course_content',
                            'file': filename
                        })
        
        return processed_content
    
    def split_markdown_content(self, content: str) -> List[Dict]:
        """Split markdown content into logical sections"""
        sections = []
        lines = content.split('\n')
        current_section = {'title': '', 'content': ''}
        
        for line in lines:
            if line.startswith('#'):
                if current_section['content']:
                    sections.append(current_section)
                current_section = {
                    'title': line.strip('#').strip(),
                    'content': line + '\n'
                }
            else:
                current_section['content'] += line + '\n'
        
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def create_embeddings(self, data: List[Dict]):
        """Create embeddings for all content"""
        texts = [item['content'] for item in data]
        self.embeddings = self.model.encode(texts)
        self.processed_data = data
    
    def save_processed_data(self, output_file: str):
        """Save processed data and embeddings"""
        data_to_save = {
            'processed_data': self.processed_data,
            'embeddings': self.embeddings.tolist() if self.embeddings is not None else []
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)