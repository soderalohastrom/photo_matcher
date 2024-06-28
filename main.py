from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
from PIL import Image
import anthropic
import os
from base64 import b64encode
import io
import uvicorn
import cv2
import face_recognition_models
import pkg_resources

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Access the environment variable
api_key = os.getenv('ANTHROPIC_API_KEY')

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Create an instance of the Anthropic client
client = anthropic.Anthropic(api_key=api_key)

def load_image_file(file, mode='RGB'):
    im = Image.open(file)
    if mode:
        im = im.convert(mode)
    return np.array(im)

def face_encodings(face_image, known_face_locations=None, num_jitters=1):
    face_locations = known_face_locations or _raw_face_locations(face_image)
    pose_predictor = pose_predictor_68_point
    landmarks = [pose_predictor(face_image, _rect_to_css(face_location)) for face_location in face_locations]
    return [np.array(face_encoder.compute_face_descriptor(face_image, raw_landmark_set, num_jitters)) for raw_landmark_set in landmarks]

def _raw_face_locations(img, number_of_times_to_upsample=1):
    return cnn_face_detector(img, number_of_times_to_upsample)

def compare_faces(image_file_a, image_file_b):
    try:
        img_a = load_image_file(image_file_a)
        img_b = load_image_file(image_file_b)
        
        encoding_a = face_encodings(img_a)[0]
        encoding_b = face_encodings(img_b)[0]

        distance = np.linalg.norm(encoding_a - encoding_b)
        similarity_score = 1 - (distance / 2)  # Normalize to 0-1 range

        return max(0, min(1, similarity_score))
    except Exception as e:
        print(f"Error in compare_faces: {e}")
        return None

def encode_image(image_file):
    return b64encode(image_file.read()).decode('utf-8')

async def describe_face_comparison(image_file_a, image_file_b):
    similarity_score = compare_faces(image_file_a, image_file_b)

    if similarity_score is None:
        raise HTTPException(status_code=400, detail="Error: Could not compare faces.")

    try:
        # Reset file pointers to the beginning
        image_file_a.seek(0)
        image_file_b.seek(0)
        
        # Encode images
        base64_image_a = encode_image(image_file_a)
        base64_image_b = encode_image(image_file_b)

        # Construct the prompt with images
        prompt = f"""
        As an AI assistant for a high-end matchmaking company, your task is to analyze two facial images of anonymous individuals (referred to as John Doe and Jane Doe) and provide insights relevant to potential compatibility. The facial similarity score between these two individuals is {similarity_score:.2f} (on a scale from 0 to 1, where 1 indicates identical faces).

        Important: These individuals are completely anonymous. Do not attempt to identify them. Treat them as generic representations of potential matches, referred to only as John Doe and Jane Doe.

        Please provide an immediate, detailed analysis considering the following:

        1. Overall Facial Harmony: Describe how well John and Jane's faces complement each other visually.
        2. Specific Facial Features: Compare and contrast key features of John and Jane, such as eyes, nose, mouth, and facial structure. Note any striking similarities or differences.
        3. Expressions and Perceived Personality: Infer potential personality traits or emotional states for John and Jane based on their facial expressions and features. Consider how these might align or create interesting dynamics.
        4. Age and Lifestyle Indicators: Estimate approximate ages for John and Jane, and note any visible lifestyle indicators (e.g., grooming, style choices visible in the images).
        5. Potential Compatibility Insights: Based on facial similarity research and the given score, suggest potential areas of compatibility or challenges for John and Jane. Remember, while similarity often indicates compatibility, unique combinations can also create intriguing matches.
        6. Aesthetic Appeal as a Couple: Comment on how visually harmonious John and Jane might appear together.

        Provide your analysis in a professional, sensitive manner. Avoid making absolute statements about compatibility, as facial similarity is just one factor in a complex matchmaking process. Aim for a balanced perspective that highlights potential positives while noting areas that might require further consideration.

        Begin your analysis immediately without any disclaimers about image analysis or individual identification. Focus solely on the compatibility assessment between John Doe and Jane Doe based on their facial features and the provided similarity score.

        [Image 1 - John Doe]
        <image_1>
        
        [Image 2 - Jane Doe]
        <image_2>
        """

        # Send the prompt to Claude
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image_a
                            }
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image_b
                            }
                        }
                    ]
                }
            ]
        )
        description = response.content[0].text
        return {"similarity_score": similarity_score, "analysis": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating description: {str(e)}")

@app.post("/faces")
async def face_comparison(image1: UploadFile = File(...), image2: UploadFile = File(...)):
    try:
        # Create temporary in-memory file-like objects
        image1_file = io.BytesIO(await image1.read())
        image2_file = io.BytesIO(await image2.read())
        
        result = await describe_face_comparison(image1_file, image2_file)
        return JSONResponse(content=result)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Load face recognition models
predictor_68_point_model = pkg_resources.resource_filename(__name__, "face_recognition_models/models/shape_predictor_68_face_landmarks.dat")
face_recognition_model = pkg_resources.resource_filename(__name__, "face_recognition_models/models/dlib_face_recognition_resnet_model_v1.dat")
cnn_face_detection_model = pkg_resources.resource_filename(__name__, "face_recognition_models/models/mmod_human_face_detector.dat")

pose_predictor_68_point = dlib.shape_predictor(predictor_68_point_model)
face_encoder = dlib.face_recognition_model_v1(face_recognition_model)
cnn_face_detector = dlib.cnn_face_detection_model_v1(cnn_face_detection_model)