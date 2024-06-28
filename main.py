from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
from PIL import Image
from anthropic import Anthropic
import os
from base64 import b64encode
import io
import cv2
from skimage.metrics import structural_similarity as ssim
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Access the environment variable
api_key = os.getenv('ANTHROPIC_API_KEY')

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Create an instance of the Anthropic client
client = Anthropic(api_key=api_key)

def load_image_file(file):
    image = Image.open(file).convert('RGB')
    return np.array(image)

def detect_face(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        return None
    (x, y, w, h) = faces[0]
    return image[y:y+h, x:x+w]

def compare_faces(image_file_a, image_file_b):
    try:
        img_a = load_image_file(image_file_a)
        img_b = load_image_file(image_file_b)
        
        face_a = detect_face(img_a)
        face_b = detect_face(img_b)
        
        if face_a is None or face_b is None:
            return 0.0  # Return 0 similarity if faces can't be detected
        
        face_a_gray = cv2.cvtColor(face_a, cv2.COLOR_RGB2GRAY)
        face_b_gray = cv2.cvtColor(face_b, cv2.COLOR_RGB2GRAY)
        
        face_a_resized = cv2.resize(face_a_gray, (100, 100))
        face_b_resized = cv2.resize(face_b_gray, (100, 100))
        
        similarity_score = ssim(face_a_resized, face_b_resized)
        return max(0, min(1, similarity_score))
    except Exception as e:
        print(f"Error in compare_faces: {e}")
        return 0.0  # Return 0 similarity on error

def encode_image(image_file):
    return b64encode(image_file.read()).decode('utf-8')

async def describe_face_comparison(image_file_a, image_file_b):
    similarity_score = compare_faces(image_file_a, image_file_b)

    try:
        # Reset file pointers to the beginning
        image_file_a.seek(0)
        image_file_b.seek(0)
        
        # Encode images
        base64_image_a = encode_image(image_file_a)
        base64_image_b = encode_image(image_file_b)

        prompt = f"""
        As an AI assistant for a confidential matchmaking service, you are tasked with analyzing facial features in photographs to assess potential compatibility. This analysis is based on a facial similarity score and other visible cues, without identifying specific individuals. The facial similarity score provided is {similarity_score:.2f} (scale: 0-1, where 1 indicates identical features).

        Important: This analysis is purely for matchmaking purposes and does not involve identifying or commenting on specific individuals. Treat the images as anonymous representations.

        Provide a detailed, professional analysis considering the following points. Use markdown formatting for readability:

        1. **Interpretation of Facial Similarity Score:**
        - Explain what the score of {similarity_score:.2f} might indicate in terms of potential compatibility.
        - Briefly mention any relevant research on how facial similarity relates to attraction or relationship dynamics.

        2. **Age Compatibility Assessment:**
        - Provide a general age range estimate for each photo.
        - Discuss potential compatibility factors related to the estimated ages.

        3. **Lifestyle and Interest Indicators:**
        - Note any visible cues that might suggest shared interests or lifestyles (e.g., style of dress, grooming, accessories).
        - Analyze how these factors could contribute to compatibility.

        4. **Facial Expression and Personality Insights:**
        - Describe the general facial expressions visible in the photos.
        - Infer potential personality traits based on these expressions and how they might interact in a relationship context.

        5. **Overall Compatibility Potential:**
        - Synthesize the above factors to provide an assessment of overall compatibility potential.
        - Highlight areas that suggest good compatibility and areas that might require further exploration.

        Maintain a professional, ethical tone throughout your analysis. Remember that facial features and expressions are just one aspect of compatibility. Focus on potential and possibilities rather than definitive conclusions.

        Your analysis should be detailed yet respectful, avoiding any comments that could be construed as judgmental or overly personal. Use markdown formatting to structure your response clearly.
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
        result = await describe_face_comparison(image1.file, image2.file)
        return JSONResponse(content=result)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)