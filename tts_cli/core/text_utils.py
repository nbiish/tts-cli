import re

def split_text(text: str, max_length: int = 200) -> list[str]:
    """
    Split text into chunks smaller than max_length, respecting sentence boundaries.
    
    Args:
        text: The input text to split.
        max_length: The maximum length of each chunk.
        
    Returns:
        A list of text chunks.
    """
    if not text:
        return []
        
    # Normalize whitespace
    text = " ".join(text.split())
    
    if len(text) <= max_length:
        return [text]
        
    chunks = []
    current_chunk = ""
    
    # Split by sentence boundaries (., !, ?) keeping the punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        # If a single sentence is too long, we need to split it further
        if len(sentence) > max_length:
            # If we have a current chunk accumulating, push it first
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Split long sentence by comma or other loose boundaries if possible
            # For now, let's just do a hard split on words if needed
            words = sentence.split(' ')
            temp_chunk = ""
            
            for word in words:
                if len(temp_chunk) + len(word) + 1 <= max_length:
                    if temp_chunk:
                        temp_chunk += " " + word
                    else:
                        temp_chunk = word
                else:
                    if temp_chunk:
                        chunks.append(temp_chunk.strip())
                    temp_chunk = word
            
            if temp_chunk:
                current_chunk = temp_chunk
        else:
            # Check if adding this sentence would exceed max_length
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks
