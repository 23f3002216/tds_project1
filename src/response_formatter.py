from typing import List, Dict, Tuple
import re

class ResponseFormatter:
    def format_response(self, answer: str, search_results: List[Tuple[Dict, float]]) -> Dict:
        """Format the API response according to required schema"""
        
        # Extract unique links from search results
        links = []
        seen_urls = set()
        
        for result, score in search_results[:5]:  # Top 5 results
            url = result.get('full_url') or result.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                
                # Create descriptive text from content
                content = result.get('content', '')[:200]
                title = result.get('title', '')
                
                # Clean up text for link description
                text = title if title else content
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 100:
                    text = text[:97] + "..."
                
                links.append({
                    "url": url,
                    "text": text or "Relevant discussion"
                })
        
        return {
            "answer": answer,
            "links": links
        }