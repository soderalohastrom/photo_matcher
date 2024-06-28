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

        # Construct the prompt with images
        prompt = f"""
        As an AI assistant for a high-end matchmaking company, analyze two facial images and provide insights relevant to potential compatibility. The facial similarity score between these two individuals is {similarity_score:.2f} (on a scale from 0 to 1, where 1 indicates identical faces).

        Provide a detailed analysis considering the following points. Use markdown formatting for better readability, and start each point on a new line:

        1. **Overall Facial Harmony:** Describe how well the faces complement each other visually.

        2. **Specific Facial Features:** Compare and contrast key features such as eyes, nose, mouth, and facial structure. Note any striking similarities or differences.

        3. **Expressions and Perceived Personality:** Infer potential personality traits or emotional states based on facial expressions and features. Consider how these might align or create interesting dynamics.

        4. **Age and Lifestyle Indicators:** Estimate approximate ages and note any visible lifestyle indicators (e.g., grooming, style choices visible in the images).

        5. **Potential Compatibility Insights:** Based on facial similarity research and the given score, suggest potential areas of compatibility or challenges. Remember, while similarity often indicates compatibility, unique combinations can also create intriguing matches.

        6. **Aesthetic Appeal as a Couple:** Comment on how visually harmonious the individuals might appear together.

        Provide your analysis in a professional, sensitive manner. Avoid making absolute statements about compatibility, as facial similarity is just one factor in a complex matchmaking process. Aim for a balanced perspective that highlights potential positives while noting areas that might require further consideration.

        Begin your analysis immediately without any disclaimers about image analysis or individual identification. Focus solely on the compatibility assessment based on the facial features and the provided similarity score.

        Format your response in markdown, using appropriate headers, bullet points, or numbered lists for clarity and readability.
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