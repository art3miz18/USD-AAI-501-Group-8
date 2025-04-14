## **README.md**

---

# DOCUMENT OCR KIE

This is a Flask-based API that provides Optical Character Recognition (OCR) capabilities for document processing. It can handle images of various documents such as passports and IDs, extracting important information including names, dates, document types, and more.

## Features

- Token-based authentication for secure access.
- Support for single or double-sided documents (front and back).
- Extraction of key details such as name, date of birth, nationality, and document type.
- Face extraction from images.
- Document type classification.

## Technologies Used

- **Flask**: Backend API framework.
- **Gradio Client**: To interact with the Hugging Face Gradio app.
- **Pillow (PIL)**: Image handling library.
- **Flask-CORS**: Cross-origin resource sharing.
- **Logging**: For logging API interactions and errors.

## Installation

### Requirements

- Python 3.x
- Flask
- Gradio Client
- Pillow (PIL)

### Steps

1. **Clone the repository**:

   ```bash
   git clone <repo_url>
   ```

2. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:

   ```bash
   python app.py
   ```

   The API will run on `http://0.0.0.0:8080`.

## Usage

### Authentication

This API uses token-based authentication. The token should be included in the `GlobalOCRToken` header of the request.

Example using `curl`:

```bash
curl -X POST http://<your-server-ip>:8080/ocr/meta-global-ocr \
-H "KIEToken: <your_token>" \
-F "front_img=@path_to_image" \
-F "back_img=@path_to_back_image"
```

### Endpoints

#### 1. `/ocr/kie-ocr-test` (POST)
A test endpoint to verify token validation and API connectivity.

#### 2. `/ocr/kie-ocr` (POST)
Extracts details from the front and back of a document.

**Request Parameters**:
- `front_img`: (Required) Image file of the front side of the document.
- `back_img`: (Optional) Image file of the back side of the document.

### Sample Response

```json
{
    "name": "John Doe",
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1980-01-01",
    "country": "USA",
    "gender": "M",
    "expiryDate": "2030-01-01",
    "documentId": "ABC123456",
    "MRZno": "P<USAJOHN<<DOE<<<<<<<<<<<<1234567890",
    "otherData": "some additional data",
    "photo": "http://path_to_extracted_face_image.jpg",
    "father'sName": "Father Name",
    "mother'sName": "Mother Name",
    "address": "123 Main St, Anytown, USA",
    "documentType": "passport",
    "dateOfIssue": "2015-01-01",
    "fileNo": "XYZ123456"
}
```

### Error Handling

- **400 Error**: Missing or invalid input (e.g., no `front_img` provided).
- **500 Error**: Internal server error during document processing.

