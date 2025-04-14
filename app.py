import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file
from PIL import Image
import logging
import tempfile
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

logging.basicConfig(level=logging.INFO)


HUGGING_FACE_SPACE = "InvincibleMeta/meta-GlobalOCR"
client = Client(HUGGING_FACE_SPACE, download_files = False)



# Get the token from the environment variable
VALID_TOKEN = "sk-89QmxJSClcA4EceONWSfF-qw1qwur6cNyE6FeW4sGgs"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('GlobalOCRToken')
        logging.info(f"Received token: {token}")
        #token or not token.startswith('Bearer ') or
        if token != VALID_TOKEN:
            return jsonify({'message': 'Token is missing or invalid!'}), 401
        return f(*args, **kwargs)
    return decorated
@app.route('/ocr')
def index():
    return "API works!"

@app.route('/ocr/meta-ocr-test', methods=['POST'])
@token_required
def test():
    # client.view_api()
    return("Validation succesful ✅ " )
    

@app.route('/ocr/meta-global-ocr', methods=['POST'])
@token_required
def meta_ocr_test():
    try:
        # Retrieve the front image from the request
        document_front_image = request.files.get('front_img')

        # Ensure that the front image is provided and not empty
        if not document_front_image or document_front_image.filename == '':
            return jsonify({'error': 'The front_img file is missing or empty'}), 400
        
        # Process the front image
        extracted_details1 = process_image(document_front_image)
        # print("Details extracted from front image: ", extracted_details1)
        
        # Check if the back image is provided
        document_back_image = request.files.get('back_img')  # This can be None
        extracted_details2 = {}

        # Process the back image if it is provided
        if document_back_image and document_back_image.filename != '':
            extracted_details2 = process_image(document_back_image)
            # print("Details extracted from back image: ", extracted_details2)
        
        # Combine the extracted details from both images
        combined_details = combine_extracted_details(extracted_details1, extracted_details2)
        
        # Return the combined result
        return jsonify(combined_details)
    
    except Exception as e:
        logging.error("Error processing the request", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
def sanitize_value(value):
    """Remove unwanted characters such as newlines and trailing quotes."""
    return value.replace("\n", "").replace("\"", "").strip()

def process_image(image):
    doc_img_temp = tempfile.NamedTemporaryFile(delete=False)
    try:
        document_img = Image.open(image)
        document_img_format = document_img.format if document_img.format else "PNG"

        document_img.save(doc_img_temp.name, format=document_img_format)
        
        result = client.predict(
                img=handle_file(doc_img_temp.name),
                api_name="/SmartExtract"
        )
        # print(result)
        extracted_details = result[1][0] 
        best_predictions = {}
        relatable_keywords_list = []
        for field, predictions in extracted_details.items():
            if predictions:
                # Always take the first prediction assuming it's the most relevant
                best_prediction = predictions[0]
                best_predictions[field] = sanitize_value(best_prediction.get('text', ''))
                
                # Collect all predictions as relatable keywords
                relatable_keywords_list.extend([sanitize_value(p.get('text', '')) for p in predictions])

        # Combine relatable keywords from the "Other_data" field and predictions below 80%
        relatable_keywords = ", ".join([
            sanitize_value(keyword.get("text", ""))
            for keyword in extracted_details.get("Other_data", [])
        ] + relatable_keywords_list)
        
        # Safely extract the image URL
        extracted_image_url = None
        if len(result) > 2 and isinstance(result[2], list) and result[2]:
            if 'image' in result[2][0]:
                extracted_image_url = result[2][0]['image'].get('url', '')
                
        # document Type Extraction
        # document_type_info = result[3]
        
        formatted_result = {
            "name": best_predictions.get('Name', ''),
            "firstName": best_predictions.get('First Name', ''), 
            "lastName": best_predictions.get('Last Name', ''),
            "dateOfBirth": best_predictions.get('Date of Birth', ''),
            "country": best_predictions.get('Country', ''),
            "gender": best_predictions.get('Gender', ''),
            "expiryDate": best_predictions.get('Expiry Date', ''),
            "documentId": best_predictions.get('Document Id', ''),
            "MRZno": best_predictions.get('MRZ', ''),
            "otherData": relatable_keywords, 
            "photo": extracted_image_url,
            "father'sName": best_predictions.get("Father's Name", ''),
            "mother'sName": best_predictions.get("Mother's Name", ''),
            "address": best_predictions.get("Address", ''),
            "documentType":  best_predictions.get("Type", ''), # ---- from the document classfication model ----
            "dateOfIssue":best_predictions.get("Date of Issue", ''),
            "fileNo":best_predictions.get("File no", '')    
        }   
        
        return formatted_result
    
    finally:
        doc_img_temp.close()
        os.remove(doc_img_temp.name)
def combine_extracted_details(details_front, details_back):
    logging.debug("Combining details from front and back images.")    

    combined = details_front.copy()  # Start with front details

    for key, value in details_back.items():
        if key == 'otherData':
            # Append back otherData to front otherData
            if value:
                if combined.get('otherData'):
                    combined['otherData'] += f", {value}"
                else:
                    combined['otherData'] = value
            continue  # Handle 'otherData' separately

        # Only add the back value if the front value is missing or empty
        if key not in combined or not combined[key].strip():
            combined[key] = value
            logging.debug(f"Added {key} from back: {value}")
        else:
            logging.debug(f"Skipped {key} from back as it already exists in front: {combined[key]}")

    # Optionally, clean up 'otherData' by removing duplicates and sorting
    if 'otherData' in combined:
        other_data_set = set(map(str.strip, combined['otherData'].split(',')))
        combined['otherData'] = ", ".join(sorted(other_data_set))

    logging.debug(f"Combined details: {combined}")
    return combined

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
