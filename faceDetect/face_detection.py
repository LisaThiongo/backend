# has FACENET, SINGLESHOT DETECTION AND MTCNN (OVERALL BETTER)

# MTCNN WITH blurring 

from http.client import HTTPException
import cv2
import numpy as np
import os
from mtcnn import MTCNN
import json
import matplotlib.pyplot as plt
import traceback
from fastapi import UploadFile, HTTPException
from typing import List
from io import BytesIO


def detect_faces_mtcnn(image_path, confidence_threshold=0.9):

    # Initialize MTCNN detector
    detector = MTCNN()
    
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at path: {image_path}")
    
    # Convert BGR to RGB (MTCNN uses RGB)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect faces
    detections = detector.detect_faces(rgb_image)
    
    # List to store face information
    faces = {}
    for detection in detections:
        confidence = detection['confidence']
        if confidence > confidence_threshold:
            x, y, w, h = detection['box']

            # Convert bounding box to a tuple for dictionary usage
            box_tuple = (x, y, w, h)

            # Check if this box is already in the dictionary
            if box_tuple not in faces:
                # Store face information in the dictionary
                faces[box_tuple] = {
                    'confidence': float(confidence)
                }

                # Draw rectangle around face
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Add confidence score
                text = f"{confidence * 100:.2f}%"
                cv2.putText(image, text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

                # Print coordinates for unique detections
                print(f"Coordinates are: {x}, {y}, {w}, {h}")

    # Convert dictionary to a list of faces for compatibility with existing code
    faces_list = [{'bbox': bbox, 'confidence': info['confidence']} for bbox, info in faces.items()]

    return image, faces_list




def process_image(image_file: UploadFile, confidence_thresholds: List[float] = [0.9, 0.8, 0.7]) -> dict:
    try:
        # Save the uploaded image temporarily
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "temp_image.jpg")
        
        with open(image_path, "wb") as f:
            f.write(image_file.file.read())

        print(f"Processing image at: {image_path}")

        # Initialize variables for the best result
        max_faces = 0
        best_result = None

        # Try different confidence thresholds
        for confidence in confidence_thresholds:
            print(f"\nTrying confidence threshold: {confidence}")
            annotated_image, detected_faces = detect_faces_mtcnn(image_path, confidence)

            if len(detected_faces) > max_faces:
                max_faces = len(detected_faces)
                best_result = (annotated_image, detected_faces)

        if best_result:
            annotated_image, detected_faces = best_result
        else:
            raise HTTPException(status_code=400, detail="No faces detected with any confidence threshold")

        print(f"\nFound {len(detected_faces)} faces")

        # Prepare data for JSON output (only face number and coordinates)
        faces_data = []
        for i, face in enumerate(detected_faces, 1):
            x, y, w, h = face['bbox']
            faces_data.append({
                "face_id": i,
                "coordinates": {"x": x, "y": y, "width": w, "height": h}
            })
        print("##############################")
        # Prepare output directories and paths
        output_dir = os.path.join(current_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Define paths for JSON output and annotated image
        json_output_path = os.path.join(output_dir, "faces_data.json")
        # Save JSON file
        with open(json_output_path, 'w') as json_file:
            json.dump(faces_data, json_file, indent=4)

        print(f"Face data saved to JSON file at: {json_output_path}")

        return {
            "faces_detected": len(detected_faces),
            "faces_data": faces_data
        }

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error processing image")