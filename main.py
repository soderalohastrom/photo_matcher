from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
from PIL import Image
from anthropic import Anthropic
import os
from base64 import b64encode
import io
from deepface import DeepFace
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

def compare_faces(image_file_a, image_file_b):
    try:
        # DeepFace.verify returns a dictionary with 'verified' and 'distance' keys
        result = DeepFace.verify(image_file_a, image_file_b, model_name="VGG-Face")
        
        # Convert distance to similarity score (1 - normalized distance)
        similarity_score = 1 - (result['distance'] / 2.5)  # 2.5 is a typical threshold for VGG-Face
        
        return float(np.clip(similarity_score, 0, 1))  # Ensure score is between 0 and 1
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
        As an AI assistant, you are tasked with analyzing two anonymous facial photographs to compare their features and expressions. The facial similarity score between these images is {similarity_score:.2f} (scale: 0-1, where 1 indicates identical features).

        Important: This analysis is purely academic and based on anonymous photographs. Do not attempt to identify or name any individuals. These images are not of celebrities or public figures - they are of ordinary, anonymous people. Treat the images as completely anonymous and avoid any comparisons to known individuals.

        Provide a detailed, objective analysis considering the following points. Use markdown formatting for readability:

        1. **Facial Similarity Assessment:**
        - Interpret the similarity score of {similarity_score:.2f}. What might this score suggest about the overall facial structures?
        - Describe any notable similarities or differences in facial features between the two images.

        2. **Age Estimation:**
        - Provide a general age range estimate for each photo.
        - Note any significant age differences or similarities between the two images.

        3. **Visible Contextual Cues:**
        - Describe any visible elements that might provide context about the individuals' environments or situations (e.g., background, clothing style, accessories).
        - Avoid making assumptions about lifestyle or personal characteristics.

        4. **Facial Expressions:**
        - Describe the general facial expressions visible in each photo.
        - Compare and contrast the expressions between the two images.

        5. **Overall Impression:**
        - Summarize the key points of comparison between the two images.
        - Focus on objective observations rather than subjective interpretations.

        Maintain a professional, academic tone throughout your analysis. Remember that this is a purely objective exercise in facial comparison of anonymous individuals. Avoid any speculation about personal characteristics, relationships, or identities. Do not compare these individuals to any celebrities or known figures.

        Your analysis should be detailed yet respectful, focusing solely on visible, objective elements in the photographs. Use markdown formatting to structure your response clearly.
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
    uvicorn.run(app, host="0.0.0.0", port=9000)