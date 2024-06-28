import face_recognition
import numpy as np
from PIL import Image
import anthropic
import os
from base64 import b64encode

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Access the environment variable
api_key = os.getenv('ANTHROPIC_API_KEY')

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Create an instance of the Anthropic client
client = anthropic.Anthropic(api_key=api_key)

def load_and_encode_face(image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            return face_encodings[0]
        else:
            raise ValueError(f"No face found in the image: {image_path}")
    except Exception as e:
        raise ValueError(f"Error processing image {image_path}: {str(e)}")

def compare_faces(image_path_a, image_path_b):
    try:
        encoding_a = load_and_encode_face(image_path_a)
        encoding_b = load_and_encode_face(image_path_b)

        distance = np.linalg.norm(encoding_a - encoding_b)
        similarity_score = 1 - (distance / np.sqrt(len(encoding_a)))

        return max(0, min(1, similarity_score))
    except Exception as e:
        print(f"Error in compare_faces: {e}")
        return None

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return b64encode(image_file.read()).decode('utf-8')

def describe_face_comparison(image_path_a, image_path_b):
    similarity_score = compare_faces(image_path_a, image_path_b)

    if similarity_score is None:
        print("Error: Could not compare faces.")
        return

    print(f"Similarity Score: {similarity_score:.2f}")

    try:
        # Encode images
        base64_image_a = encode_image(image_path_a)
        base64_image_b = encode_image(image_path_b)

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
        print(f"Claude's Matchmaking Analysis:\n{description}")
    except Exception as e:
        print(f"Error generating description: {str(e)}")

if __name__ == "__main__":
    image_path_a = "photos/man.jpg"
    image_path_b = "photos/lady.jpg"

    describe_face_comparison(image_path_a, image_path_b)