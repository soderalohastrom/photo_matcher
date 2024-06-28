import face_recognition
import numpy as np
from PIL import Image
import openai
import os

# Access the environment variable directly
api_key = os.getenv('OPENAI_API_KEY')

# Use the API key
print(f"Your OPENAI API key is: {api_key}")

# Create an instance of the OpenAI client
client = openai.OpenAI(api_key=api_key)  # Use the directly accessed API key

# Function to load and encode a single face from an image
def load_and_encode_face(image_path):
    image = face_recognition.load_image_file(image_path)
    print(f"Image loaded: {image_path}")  # Debug: Check if image is loaded
    face_encodings = face_recognition.face_encodings(image)
    if face_encodings:
        print(f"Face encodings found: {len(face_encodings)}")  # Debug: Check if encodings are found
        return face_encodings[0]
    else:
        raise ValueError("No face found in the image")

# Function to compare two face encodings and return a similarity score
def compare_faces(image_path_a, image_path_b):
    try:
        encoding_a = load_and_encode_face(image_path_a)
        encoding_b = load_and_encode_face(image_path_b)

        distance = np.linalg.norm(encoding_a - encoding_b)
        similarity_score = 1 - (distance / np.sqrt(len(encoding_a)))

        # Ensure the score is between 0 and 1
        return max(0, min(1, similarity_score))
    except Exception as e:
        print(f"Error in compare_faces: {e}")  # Debug: Print the error
        return -1  # Return -1 to indicate an error

# Function to describe the face comparison using GPT-4o
def describe_face_comparison(image_path_a, image_path_b):
    similarity_score = compare_faces(image_path_a, image_path_b)

    if similarity_score == -1:
        print("Error: No faces found in one or both images.")
        return

    print(f"Similarity Score: {similarity_score}")

    # Check if OpenAI API key is set
    if api_key:  # Use the directly accessed API key
        prompt = f"The similarity score between the two faces is {similarity_score:.2f}. Describe the comparison."
        response = client.chat.completions.create(  # Use openai.ChatCompletion.create
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        description = response.choices[0].message.content.strip()
        print(f"GPT-4o Description: {description}")
    else:
        print("Note: No description generated. Set the 'OPENAI_API_KEY' environment variable to use GPT-4o description.")

# Example usage
image_path_a = "photos/man.jpg"
image_path_b = "photos/lady.jpg"

describe_face_comparison(image_path_a, image_path_b)
