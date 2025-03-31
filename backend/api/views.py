import os
import io, json
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pdf2image import convert_from_path
import google.generativeai as genai
from api.models import InvoiceData, Invoice 

genai.configure(api_key="AIzaSyCjEgLe1W9fdegUpgk3byUYmoK1-ZB1cps")

MODEL_CONFIG = {
    "temperature": 0.2,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
]

model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=MODEL_CONFIG,
                              safety_settings=safety_settings)

def process_invoice_with_ai(file_path):
    """
    Process the uploaded file (PDF/Image) with Gemini AI to extract invoice data.
    """
    system_prompt = """
    You are an AI specialized in invoice data extraction.
    Your task is to analyze invoices from images or PDFs and return the extracted data in structured JSON format.

    Ensure the output contains:
    - Invoice Number
    - Vendor Details
    - Date
    - Amount (Total, Tax, Subtotal)
    
    Return the data in valid JSON format with these keys:
    - invoice_number
    - vendor_details
    - date (in YYYY-MM-DD format)
    - total_amount (numeric)
    - tax_amount (numeric)
    - subtotal_amount (numeric)
    """

    user_prompt = "Extract and format the invoice data as JSON. Ensure the output is valid JSON format."

    file_ext = Path(file_path).suffix.lower()

    if file_ext in [".jpg", ".jpeg", ".png"]:
        image_info = [{"mime_type": "image/png", "data": Path(file_path).read_bytes()}]
    elif file_ext == ".pdf":
        images = convert_from_path(file_path)  # Convert PDF to images
        image_info = []
        for img in images:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            image_info.append({"mime_type": "image/png", "data": img_byte_arr.getvalue()})
    else:
        return {"error": "Unsupported file format"}

    response_texts = []
    for img_data in image_info:
        input_prompt = [system_prompt, img_data, user_prompt]
        response = model.generate_content(input_prompt)
        response_texts.append(response.text)

    return response_texts

@csrf_exempt  # Disable CSRF for testing
def upload_invoice(request):
    if request.method == "GET":
        return JsonResponse({"message": "API is working. Use POST to upload files."})
    if request.method == "POST":
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        uploaded_file = request.FILES['file']
        file_path = default_storage.save(uploaded_file.name, ContentFile(uploaded_file.read()))
        full_file_path = os.path.join(default_storage.location, file_path)

        # Process invoice with Google Gemini AI (returns extracted JSON data)
        extracted_data = process_invoice_with_ai(full_file_path)

        # Extract JSON from the response text
        json_data = None
        try:
            for text in extracted_data:
                # Look for JSON content in the response
                text = text.strip()
                # Find the first { and last } to extract JSON
                if '{' in text and '}' in text:
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    potential_json = text[start:end]
                    json_data = json.loads(potential_json)
                    break
            
            if not json_data:
                json_data = {}
                
            # Convert the json_data to a string for storage
            extracted_json_str = json.dumps(json_data)
            
            # Save file info to InvoiceData model
            invoice_entry = InvoiceData.objects.create(
                file_name=uploaded_file.name,
                file_path=file_path,
                extracted_data=extracted_json_str
            )
            
            # Parse extracted data for structured storage
            invoice_number = json_data.get("invoice_number", "Unknown")
            vendor_details = json_data.get("vendor_details", "Unknown Vendor")
            
            # Handle date format
            date_str = json_data.get("date", None)
            
            # Default values for numeric fields
            total_amount = json_data.get("total_amount", 0.0)
            if isinstance(total_amount, str):
                # Remove currency symbols and commas
                total_amount = total_amount.replace('$', '').replace(',', '')
                try:
                    total_amount = float(total_amount)
                except ValueError:
                    total_amount = 0.0
                    
            tax_amount = json_data.get("tax_amount", 0.0)
            if isinstance(tax_amount, str):
                tax_amount = tax_amount.replace('$', '').replace(',', '')
                try:
                    tax_amount = float(tax_amount)
                except ValueError:
                    tax_amount = 0.0
                    
            subtotal_amount = json_data.get("subtotal_amount", 0.0)
            if isinstance(subtotal_amount, str):
                subtotal_amount = subtotal_amount.replace('$', '').replace(',', '')
                try:
                    subtotal_amount = float(subtotal_amount)
                except ValueError:
                    subtotal_amount = 0.0
                    
            line_items = json_data.get("line_items", [])

            # Store extracted structured invoice data in the Invoice model
            try:
                invoice_record = Invoice.objects.create(
                    invoice_number=invoice_number,
                    vendor_details=vendor_details,
                    date=date_str,
                    total_amount=total_amount,
                    tax_amount=tax_amount,
                    subtotal_amount=subtotal_amount,
                    line_items=line_items
                )
                invoice_id = invoice_record.id
            except Exception as e:
                invoice_id = None
                print(f"Error creating Invoice record: {str(e)}")

            response_data = {
                "message": "File uploaded and processed successfully",
                "file_name": uploaded_file.name,
                "file_path": file_path,
                "extracted_data": json_data,
                "invoice_id": invoice_id,
                "status": "success"
            }
            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid extracted data format: {str(e)}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"Processing error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)