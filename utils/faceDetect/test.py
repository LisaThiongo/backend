


# import cv2
# import numpy as np
# import os
# import tensorflow as tf
# from mtcnn import MTCNN
# from keras_facenet import FaceNet
# import matplotlib.pyplot as plt

# def download_model_files():
#     """
#     FaceNet and MTCNN models are typically downloaded automatically by their respective libraries.
#     This function is kept for consistency but doesn't need to download anything manually.
#     """
#     print("Model files will be downloaded automatically when needed.")

# def detect_and_embed_faces(image_path, confidence_threshold=0.95):
#     """
#     Detect faces using MTCNN and generate embeddings using FaceNet
#     """
#     # Initialize MTCNN and FaceNet
#     detector = MTCNN()
#     facenet = FaceNet()

#     # Read image
#     image = cv2.imread(image_path)
#     if image is None:
#         raise ValueError(f"Could not read image at path: {image_path}")

#     # Convert BGR to RGB (MTCNN uses RGB)
#     rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

#     # Detect faces
#     detections = detector.detect_faces(rgb_image)

#     # List to store face information
#     faces = []

#     for detection in detections:
#         confidence = detection['confidence']
#         if confidence > confidence_threshold:
#             x, y, w, h = detection['box']
#             face_image = rgb_image[y:y+h, x:x+w]
            
#             # Generate embedding
#             face_image = cv2.resize(face_image, (160, 160))
#             face_image = np.expand_dims(face_image, axis=0)
#             embedding = facenet.embeddings(face_image)[0]

#             # Store face information
#             faces.append({
#                 'bbox': (x, y, w, h),
#                 'confidence': float(confidence),
#                 'embedding': embedding
#             })

#             # Draw rectangle around face
#             cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
#             # Add confidence score
#             text = f"{confidence * 100:.2f}%"
#             cv2.putText(image, text, (x, y-10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

#     return image, faces

# def display_image(image):
#     """
#     Display an image using matplotlib
#     """
#     plt.figure(figsize=(12, 8))
#     plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
#     plt.axis('off')
#     plt.show()

# def save_image(image, output_path):
#     """
#     Save the annotated image
#     """
#     output_path = os.path.abspath(output_path)
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     cv2.imwrite(output_path, image)
#     print(f"Saved annotated image to: {output_path}")

# if __name__ == "__main__":
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     image_path = os.path.join(current_dir, "images", "group6.jpeg")
    
#     try:
#         print(f"Processing image at: {image_path}")
        
#         # Try different confidence thresholds
#         confidence_thresholds = [0.95, 0.9, 0.85]
#         max_faces = 0
#         best_result = None
        
#         for confidence in confidence_thresholds:
#             print(f"\nTrying confidence threshold: {confidence}")
#             annotated_image, detected_faces = detect_and_embed_faces(image_path, confidence)
            
#             if len(detected_faces) > max_faces:
#                 max_faces = len(detected_faces)
#                 best_result = (annotated_image, detected_faces)
        
#         if best_result:
#             annotated_image, detected_faces = best_result
#         else:
#             print("No faces detected with any confidence threshold")
#             exit()
        
#         print(f"\nFound {len(detected_faces)} faces")
#         for i, face in enumerate(detected_faces, 1):
#             print(f"Face {i} - Confidence: {face['confidence']:.2f}")
        
#         # Display the image
#         display_image(annotated_image)
        
#         # Save the annotated image
#         output_dir = os.path.join(current_dir, "output")
#         output_path = os.path.join(output_dir, "annotated_facenet.jpg")
#         save_image(annotated_image, output_path)
        
#     except Exception as e:
#         print(f"\nError processing image: {str(e)}")
#         import traceback
#         print(traceback.format_exc())

# import cv2
# import numpy as np
# import os
# import wget

# def download_model_files():
#     """
#     Downloads the model files if they are not already present.
#     """
#     # Define URLs for the model files
#     prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
#     caffemodel_url = "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    
#     # Create 'models' directory if it doesn't exist
#     if not os.path.exists('models'):
#         os.makedirs('models')
    
#     # Download deploy.prototxt
#     prototxt_path = 'models/deploy.prototxt'
#     if not os.path.exists(prototxt_path):
#         print("Downloading deploy.prototxt...")
#         wget.download(prototxt_url, prototxt_path)
#         print(f"\nDownloaded deploy.prototxt to {prototxt_path}")
    
#     # Download res10_300x300_ssd_iter_140000.caffemodel
#     caffemodel_path = 'models/res10_300x300_ssd_iter_140000.caffemodel'
#     if not os.path.exists(caffemodel_path):
#         print("Downloading res10_300x300_ssd_iter_140000.caffemodel...")
#         wget.download(caffemodel_url, caffemodel_path)
#         print(f"\nDownloaded caffemodel to {caffemodel_path}")

# def detect_faces_dnn(image_path, confidence_threshold=0.5):
#     """
#     Detect faces using OpenCV's DNN face detector
#     """
#     # Load the pre-trained model
#     model_file = "models/res10_300x300_ssd_iter_140000.caffemodel"
#     config_file = "models/deploy.prototxt"
    
#     # Download model files if they don't exist
#     download_model_files()

#     # Load the DNN model
#     net = cv2.dnn.readNetFromCaffe(config_file, model_file)

#     # Read image
#     image = cv2.imread(image_path)
#     if image is None:
#         raise ValueError(f"Could not read image at path: {image_path}")

#     # Get image dimensions
#     (h, w) = image.shape[:2]

#     # Create a blob from the image
#     blob = cv2.dnn.blobFromImage(
#         cv2.resize(image, (300, 300)), 
#         1.0, 
#         (300, 300), 
#         (104.0, 177.0, 123.0)
#     )

#     # Pass the blob through the network and get detections
#     net.setInput(blob)
#     detections = net.forward()

#     # List to store face information
#     faces = []

#     # Loop over the detections
#     for i in range(detections.shape[2]):
#         confidence = detections[0, 0, i, 2]

#         if confidence > confidence_threshold:
#             # Calculate bounding box coordinates
#             box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
#             (startX, startY, endX, endY) = box.astype("int")

#             # Ensure coordinates are within image boundaries
#             startX = max(0, startX)
#             startY = max(0, startY)
#             endX = min(w, endX)
#             endY = min(h, endY)

#             # Store face information
#             faces.append({
#                 'bbox': (startX, startY, endX - startX, endY - startY),
#                 'confidence': float(confidence)
#             })

#             # Draw rectangle around face
#             cv2.rectangle(image, (startX, startY), (endX, endY), (0, 255, 0), 2)
            
#             # Add confidence score
#             text = f"{confidence * 100:.2f}%"
#             y = startY - 10 if startY - 10 > 10 else startY + 10
#             cv2.putText(image, text, (startX, y),
#                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

#     return image, faces

# def display_image(image):
#     """
#     Display an image using cv2
#     """
#     # Resize image if it's too large for display
#     height, width = image.shape[:2]
#     max_display_dimension = 1200
#     if max(height, width) > max_display_dimension:
#         scale = max_display_dimension / max(height, width)
#         image = cv2.resize(image, (int(width * scale), int(height * scale)))
    
#     cv2.imshow('Face Detection', image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()

# def save_image(image, output_path):
#     """
#     Save the annotated image
#     """
#     output_path = os.path.abspath(output_path)
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     cv2.imwrite(output_path, image)
#     print(f"Saved annotated image to: {output_path}")

# if __name__ == "__main__":
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     image_path = os.path.join(current_dir, "images", "group6.jpeg")
    
#     try:
#         print(f"Processing image at: {image_path}")
        
#         # Try different confidence thresholds
#         confidence_thresholds = [0.5, 0.3, 0.2]
#         max_faces = 0
#         best_result = None
        
#         for confidence in confidence_thresholds:
#             print(f"\nTrying confidence threshold: {confidence}")
#             annotated_image, detected_faces = detect_faces_dnn(image_path, confidence)
            
#             if len(detected_faces) > max_faces:
#                 max_faces = len(detected_faces)
#                 best_result = (annotated_image, detected_faces)
        
#         if best_result:
#             annotated_image, detected_faces = best_result
#         else:
#             print("No faces detected with any confidence threshold")
#             exit()
        
#         print(f"\nFound {len(detected_faces)} faces")
#         for i, face in enumerate(detected_faces, 1):
#             print(f"Face {i} - Confidence: {face['confidence']:.2f}")
        
#         # Display the image
#         display_image(annotated_image)
        
#         # Save the annotated image
#         output_dir = os.path.join(current_dir, "output")
#         output_path = os.path.join(output_dir, "annotated_1.jpg")
#         save_image(annotated_image, output_path)
        
#     except Exception as e:
#         print(f"\nError processing image: {str(e)}")
#         import traceback
#         print(traceback.format_exc())


# import cv2
# import numpy as np
# import os
# from mtcnn import MTCNN
# import matplotlib.pyplot as plt

# def detect_faces_mtcnn(image_path, confidence_threshold=0.9):
#     """
#     Detect faces using MTCNN
#     """
#     # Initialize MTCNN detector
#     detector = MTCNN()

#     # Read image
#     image = cv2.imread(image_path)
#     if image is None:
#         raise ValueError(f"Could not read image at path: {image_path}")

#     # Convert BGR to RGB (MTCNN uses RGB)
#     rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

#     # Detect faces
#     detections = detector.detect_faces(rgb_image)

#     # List to store face information
#     faces = []

#     for detection in detections:
#         confidence = detection['confidence']
#         if confidence > confidence_threshold:
#             x, y, w, h = detection['box']
            
#             # Store face information
#             faces.append({
#                 'bbox': (x, y, w, h),
#                 'confidence': float(confidence)
#             })

#             # Draw rectangle around face
#             cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
#             # Add confidence score
#             text = f"{confidence * 100:.2f}%"
#             cv2.putText(image, text, (x, y-10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

#     return image, faces

# def display_image(image):
#     """
#     Display an image using matplotlib
#     """
#     plt.figure(figsize=(12, 8))
#     plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
#     plt.axis('off')
#     plt.show()

# def save_image(image, output_path):
#     """
#     Save the annotated image
#     """
#     output_path = os.path.abspath(output_path)
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     cv2.imwrite(output_path, image)
#     print(f"Saved annotated image to: {output_path}")

# if __name__ == "__main__":
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     image_path = os.path.join(current_dir, "images", "group6.jpeg")
    
#     try:
#         print(f"Processing image at: {image_path}")
        
#         # Try different confidence thresholds
#         confidence_thresholds = [0.9, 0.8, 0.7]
#         max_faces = 0
#         best_result = None
        
#         for confidence in confidence_thresholds:
#             print(f"\nTrying confidence threshold: {confidence}")
#             annotated_image, detected_faces = detect_faces_mtcnn(image_path, confidence)
            
#             if len(detected_faces) > max_faces:
#                 max_faces = len(detected_faces)
#                 best_result = (annotated_image, detected_faces)
        
#         if best_result:
#             annotated_image, detected_faces = best_result
#         else:
#             print("No faces detected with any confidence threshold")
#             exit()
        
#         print(f"\nFound {len(detected_faces)} faces")
#         for i, face in enumerate(detected_faces, 1):
#             print(f"Face {i} - Confidence: {face['confidence']:.2f}")
        
#         # Display the image
#         display_image(annotated_image)
        
#         # Save the annotated image
#         output_dir = os.path.join(current_dir, "output")
#         output_path = os.path.join(output_dir, "annotated_mtcnn.jpg")
#         save_image(annotated_image, output_path)
        
#     except Exception as e:
#         print(f"\nError processing image: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
