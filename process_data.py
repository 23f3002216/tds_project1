#!/usr/bin/env python3
"""
Script to process scraped data into searchable format
"""

import os
from src.data_processor import DataProcessor

def main():
    processor = DataProcessor()
    
    print("Processing discourse data...")
    discourse_data = processor.process_discourse_data('data/discourse_posts.json')
    print(f"Processed {len(discourse_data)} discourse posts")
    
    print("Processing course content...")
    course_data = processor.process_course_content('data/tds_pages_md')
    print(f"Processed {len(course_data)} course content sections")
    
    # Combine all data
    all_data = discourse_data + course_data
    print(f"Total data points: {len(all_data)}")
    
    print("Creating embeddings...")
    processor.create_embeddings(all_data)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    print("Saving processed data...")
    processor.save_processed_data('data/processed_data.json')
    
    print("Data processing complete!")

if __name__ == "__main__":
    main()