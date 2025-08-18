#!/usr/bin/env python3
"""
Test similarity computation directly in Python as a workaround
"""

import os
import json
import math
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors without numpy"""
    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))
    
    # Cosine similarity
    return dot_product / (magnitude1 * magnitude2)

def test_manual_search():
    """Test search by manually computing similarities"""
    
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("🔍 Testing manual similarity search...")
    
    # Generate query embedding
    query = "explain the tool mode"
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding
    print(f"✅ Generated query embedding: {len(query_embedding)} dimensions")
    
    # Get all chunks with embeddings
    result = supabase.table("document_chunks").select(
        "id, text_content, embedding, page_number, documents!inner(filename)"
    ).execute()
    
    print(f"📊 Retrieved {len(result.data)} chunks")
    
    similarities = []
    for chunk in result.data:
        try:
            # Parse embedding from JSON string
            if isinstance(chunk['embedding'], str):
                chunk_embedding = json.loads(chunk['embedding'])
            else:
                chunk_embedding = chunk['embedding']
            
            # Compute similarity
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            
            similarities.append({
                'id': chunk['id'],
                'text': chunk['text_content'],
                'similarity': similarity,
                'filename': chunk.get('filename', 'unknown'),
                'page_number': chunk['page_number']
            })
            
        except Exception as e:
            print(f"❌ Error processing chunk {chunk['id']}: {e}")
    
    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"\n🎯 TOP RESULTS for '{query}':")
    for i, result in enumerate(similarities[:3]):
        print(f"{i+1}. Similarity: {result['similarity']:.4f}")
        print(f"   Text: {result['text'][:100]}...")
        print(f"   File: {result['filename']}, Page: {result['page_number']}")
        print()

if __name__ == "__main__":
    test_manual_search()