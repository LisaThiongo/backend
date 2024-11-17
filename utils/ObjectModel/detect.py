from ultralytics import YOLO
from PIL import Image


model_path = "utils/ObjectModel/best.pt/home/sannux/backend/utils/ObjectModel/best.pt"
# Load the pre-trained YOLO model
model = YOLO(model_path)

async def run_detection(image: Image):
    # Perform object detection on the input image
    results = model.predict(image)

    # Process the detection results
    labeled_image = results[0].plot()
    detected_objects = {}

    # Iterate through detected objects
    for result in results[0].boxes.data:
        x1, y1, x2, y2, conf, cls = result
        class_name = model.names[int(cls)]

        # Calculate width and height from bounding box coordinates
        width = int(x2) - int(x1)
        height = int(y2) - int(y1)

        # If the object class already exists in the dictionary, append the coordinates to the list
        if class_name not in detected_objects:
            detected_objects[class_name] = {
                "coordinates": [{"x": int(x1), "y": int(y1), "width": width, "height": height}]
            }
        else:
            detected_objects[class_name]["coordinates"].append({"x": int(x1), "y": int(y1), "width": width, "height": height})

    # Convert the dictionary to a list format for returning as JSON
    detection_list = []
    for obj, details in detected_objects.items():
        detection_list.append({
            "object": obj,
            "coordinates": details["coordinates"]
        })

    return detection_list
