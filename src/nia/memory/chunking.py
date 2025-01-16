"""Text chunking utilities for memory system."""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 128,
    min_chunk_size: int = 64
) -> List[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Text to split into chunks
        chunk_size: Target size for each chunk
        overlap: Number of characters to overlap between chunks
        min_chunk_size: Minimum size for a chunk
        
    Returns:
        List[str]: List of text chunks
    """
    # Clean and normalize text
    text = text.strip()
    if not text:
        return []
        
    # Handle short texts
    if len(text) <= chunk_size:
        return [text]
        
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If single sentence is too long, split on other punctuation
        if sentence_length > chunk_size:
            sub_parts = re.split(r'(?<=[,;:])\s+', sentence)
            for part in sub_parts:
                if len(part) > chunk_size:
                    # Split on spaces as last resort
                    words = part.split()
                    temp_chunk = []
                    temp_length = 0
                    
                    for word in words:
                        word_length = len(word) + 1  # +1 for space
                        if temp_length + word_length > chunk_size:
                            if temp_chunk:  # Only add if we have content
                                chunks.append(' '.join(temp_chunk))
                            temp_chunk = [word]
                            temp_length = word_length
                        else:
                            temp_chunk.append(word)
                            temp_length += word_length
                            
                    if temp_chunk:  # Add any remaining content
                        chunks.append(' '.join(temp_chunk))
                else:
                    # Add part if it would fit in chunk
                    if current_length + len(part) + 1 <= chunk_size:
                        current_chunk.append(part)
                        current_length += len(part) + 1
                    else:
                        if current_chunk:  # Only add if we have content
                            chunks.append(' '.join(current_chunk))
                        current_chunk = [part]
                        current_length = len(part)
        else:
            # Add sentence if it would fit in chunk
            if current_length + sentence_length + 1 <= chunk_size:
                current_chunk.append(sentence)
                current_length += sentence_length + 1
            else:
                if current_chunk:  # Only add if we have content
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
                
    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
        
    # Add overlapping content
    if overlap > 0 and len(chunks) > 1:
        overlapped_chunks = []
        for i in range(len(chunks)):
            if i == 0:
                overlapped_chunks.append(chunks[i])
            else:
                # Take end of previous chunk
                prev_end = chunks[i-1][-overlap:]
                # Add to start of current chunk
                overlapped_chunks.append(prev_end + chunks[i])
                
        chunks = overlapped_chunks
        
    # Filter out chunks that are too small
    chunks = [c for c in chunks if len(c) >= min_chunk_size]
    
    logger.debug(f"Split text into {len(chunks)} chunks")
    return chunks

def chunk_content(
    content: Any,
    chunk_size: int = 512,
    overlap: int = 128,
    min_chunk_size: int = 64
) -> List[Dict]:
    """Split content into chunks while preserving metadata.
    
    Args:
        content: Content to split (string or dict with 'text' field)
        chunk_size: Target size for each chunk
        overlap: Number of characters to overlap between chunks
        min_chunk_size: Minimum size for a chunk
        
    Returns:
        List[Dict]: List of chunks with metadata
    """
    # Extract text and metadata
    if isinstance(content, str):
        text = content
        metadata = {}
    elif isinstance(content, dict):
        text = content.get('text', str(content))
        metadata = {k: v for k, v in content.items() if k != 'text'}
    else:
        text = str(content)
        metadata = {}
        
    # Get text chunks
    text_chunks = chunk_text(
        text,
        chunk_size=chunk_size,
        overlap=overlap,
        min_chunk_size=min_chunk_size
    )
    
    # Create chunk objects with metadata
    chunks = []
    for i, chunk_text in enumerate(text_chunks):
        chunk = {
            'text': chunk_text,
            'chunk_index': i,
            'total_chunks': len(text_chunks)
        }
        # Add original metadata
        chunk.update(metadata)
        chunks.append(chunk)
        
    return chunks
