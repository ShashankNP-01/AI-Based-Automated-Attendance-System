"""
Utility functions for the attendance system.
Helper functions that are used across multiple scripts/notebooks.
"""

import numpy as np
from typing import List, Tuple, Dict
import cv2
from PIL import Image

def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        float: Cosine similarity score (0 to 1)
    """
    # Normalize embeddings
    emb1_norm = embedding1 / np.linalg.norm(embedding1)
    emb2_norm = embedding2 / np.linalg.norm(embedding2)
    
    # Compute dot product (cosine similarity for normalized vectors)
    similarity = np.dot(emb1_norm, emb2_norm)
    
    return float(similarity)

def batch_cosine_similarity(embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
    """
    Calculate pairwise cosine similarity between two sets of embeddings.
    
    Args:
        embeddings1: Array of shape (N, D) - N embeddings of dimension D
        embeddings2: Array of shape (M, D) - M embeddings of dimension D
    
    Returns:
        np.ndarray: Similarity matrix of shape (N, M)
    """
    # Normalize all embeddings
    emb1_norm = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
    emb2_norm = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)
    
    # Compute similarity matrix using matrix multiplication
    similarity_matrix = np.dot(emb1_norm, emb2_norm.T)
    
    return similarity_matrix

def find_best_match(query_embedding: np.ndarray, 
                    database_embeddings: Dict[str, np.ndarray],
                    threshold: float = 0.4) -> Tuple[str, float]:
    """
    Find the best matching person for a query embedding.
    
    Args:
        query_embedding: Query face embedding
        database_embeddings: Dictionary of {person_id: embedding}
        threshold: Minimum similarity threshold to consider a match
    
    Returns:
        tuple: (person_id, similarity_score) or (None, 0.0) if no match
    """
    best_match_id = None
    best_similarity = 0.0
    
    for person_id, db_embedding in database_embeddings.items():
        similarity = cosine_similarity(query_embedding, db_embedding)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match_id = person_id
    
    # Check if best match meets threshold
    if best_similarity >= threshold:
        return best_match_id, best_similarity
    else:
        return None, 0.0

def draw_bounding_boxes(image: Image.Image, 
                       boxes: List[Tuple[int, int, int, int]],
                       labels: List[str] = None,
                       color: str = 'red',
                       width: int = 3) -> Image.Image:
    """
    Draw bounding boxes on an image.
    
    Args:
        image: PIL Image
        boxes: List of (x1, y1, x2, y2) coordinates
        labels: Optional list of labels for each box
        color: Box color
        width: Box line width
    
    Returns:
        PIL Image with boxes drawn
    """
    from PIL import ImageDraw, ImageFont
    
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
        
        if labels and i < len(labels):
            # Draw label
            label = labels[i]
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Draw text background
            text_bbox = draw.textbbox((x1, y1-20), label, font=font)
            draw.rectangle(text_bbox, fill=color)
            draw.text((x1, y1-20), label, fill='white', font=font)
    
    return img_copy

def validate_email(email: str) -> bool:
    """
    Simple email validation.
    
    Args:
        email: Email string to validate
    
    Returns:
        bool: True if valid format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_roll_no(roll_no: str) -> bool:
    """
    Validate roll number format.
    
    Args:
        roll_no: Roll number to validate
    
    Returns:
        bool: True if valid (alphanumeric, 3-20 chars)
    """
    return bool(roll_no) and roll_no.isalnum() and 3 <= len(roll_no) <= 20

def resize_image(image_path: str, max_size: Tuple[int, int] = (1920, 1080)) -> Image.Image:
    """
    Resize an image while maintaining aspect ratio.
    
    Args:
        image_path: Path to image file
        max_size: Maximum (width, height)
    
    Returns:
        PIL Image resized
    """
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img

def calculate_attendance_rate(present: int, total: int) -> float:
    """
    Calculate attendance rate percentage.
    
    Args:
        present: Number of students present
        total: Total number of students
    
    Returns:
        float: Attendance rate (0-100)
    """
    if total == 0:
        return 0.0
    return (present / total) * 100

def format_confidence(confidence: float) -> str:
    """
    Format confidence score for display.
    
    Args:
        confidence: Confidence score (0-1)
    
    Returns:
        str: Formatted string (e.g., "87.3%")
    """
    return f"{confidence * 100:.1f}%"

def create_attendance_summary(total_students: int, 
                            present: int,
                            absent: int) -> Dict[str, any]:
    """
    Create attendance summary statistics.
    
    Args:
        total_students: Total number of enrolled students
        present: Number present
        absent: Number absent
    
    Returns:
        dict: Summary statistics
    """
    return {
        'total_students': total_students,
        'present': present,
        'absent': absent,
        'attendance_rate': calculate_attendance_rate(present, total_students),
        'absence_rate': calculate_attendance_rate(absent, total_students)
    }

# Model-specific utilities

def prepare_face_for_adaface(aligned_face: np.ndarray) -> np.ndarray:
    """
    Prepare aligned face for AdaFace model input.
    
    Args:
        aligned_face: 112x112 BGR image from RetinaFace
    
    Returns:
        np.ndarray: Preprocessed image
    """
    # AdaFace expects BGR format, 112x112 - already provided by RetinaFace
    # Just ensure it's the right shape
    assert aligned_face.shape == (112, 112, 3), f"Expected (112, 112, 3), got {aligned_face.shape}"
    return aligned_face

def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """
    L2 normalize an embedding vector.
    
    Args:
        embedding: Raw embedding vector
    
    Returns:
        np.ndarray: Normalized embedding (unit length)
    """
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm

if __name__ == '__main__':
    print("✅ Utility functions loaded!")
    print("\nAvailable functions:")
    print("  - cosine_similarity()")
    print("  - batch_cosine_similarity()")
    print("  - find_best_match()")
    print("  - draw_bounding_boxes()")
    print("  - validate_email()")
    print("  - validate_roll_no()")
    print("  - resize_image()")
    print("  - calculate_attendance_rate()")
    print("  - create_attendance_summary()")
