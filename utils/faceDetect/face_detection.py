from http.client import HTTPException
import cv2
import numpy as np
from mtcnn import MTCNN
from fastapi import UploadFile, HTTPException
from typing import List
from PIL import Image

def decode_image(image) -> np.ndarray:
    """
    Convert various image inputs to numpy array format required by OpenCV.
    """
    try:
        if isinstance(image, np.ndarray):
            return image
        elif isinstance(image, Image.Image):
            return np.array(image)
        elif isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            raise ValueError("Unsupported image format")
    except Exception as e:
        raise ValueError(f"Error decoding image: {str(e)}")

def detect_faces_mtcnn(image: np.ndarray, confidence_threshold=0.9):
    """
    Detect faces using MTCNN and annotate the image.
    """
    try:
        # Ensure image is in numpy array format
        image = decode_image(image)
        
        # Create a copy of the image to avoid modifying the original
        image_copy = image.copy()
        
        # Initialize MTCNN detector
        detector = MTCNN()
        
        # Convert BGR to RGB (MTCNN uses RGB)
        rgb_image = cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        detections = detector.detect_faces(rgb_image)
        
        # List to store face information
        faces = []
        
        # Process each detection
        for detection in detections:
            confidence = detection['confidence']
            if confidence > confidence_threshold:
                x, y, w, h = detection['box']
                faces.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                })
                # Draw rectangle around face
                cv2.rectangle(image_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Add confidence score
                text = f"{confidence * 100:.2f}%"
                cv2.putText(image_copy, text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
        
        return image_copy, faces
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting faces: {str(e)}")

async def process_image(image: np.ndarray, confidence_thresholds: List[float] = [0.6]) -> dict:
    """
    Process an image to detect faces using multiple confidence thresholds.
    If no faces are detected, return an empty response.
    """
    try:
        # Initialize variables for the best result
        max_faces = 0
        best_result = None
        
        # Try different confidence thresholds
        for confidence in confidence_thresholds:
            print(f"\nTrying confidence threshold: {confidence}")
            annotated_image, detected_faces = detect_faces_mtcnn(image, confidence)
            
            # Update the best result if more faces are detected
            if len(detected_faces) > max_faces:
                max_faces = len(detected_faces)
                best_result = (annotated_image, detected_faces)
        
        if best_result:
            annotated_image, detected_faces = best_result
            # Prepare the return data with only face coordinates in the requested format
            coordinates_data = [{
                'x': face['x'],
                'y': face['y'],
                'width': face['width'],
                'height': face['height']
            } for face in detected_faces]
            
            return {
                "object": "Face",
                "coordinates": coordinates_data  # Returning only coordinates
            }
        else:
            # Return empty response if no faces are detected
            return {}
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Input error: {str(ve)}")
    except HTTPException as he:
        raise he  # Re-raise any HTTP-related errors
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
