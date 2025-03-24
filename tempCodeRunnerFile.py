from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import cv2

# Configuration constants
UPLOAD_FOLDER = 'static/uploads'  # Directory to store uploaded images
PROCESSED_FOLDER = 'static/processed'  # Directory to store processed images
ALLOWED_EXTENSIONS = {'webp', 'png', 'jpg', 'jpeg'}  # Allowed file extensions

# Initialize Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.secret_key = 'the rando'  # Secret key for session management and flash messages

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    Trims extra whitespace before checking.
    """
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].strip().lower()
        return ext in ALLOWED_EXTENSIONS
    return False

def process_image(filename, operation, quality=None):
    """
    Process the uploaded image according to the specified operation.
    Returns a tuple: (processed_filename, error_message)
    """
    try:
        # Construct full path to input image
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img = cv2.imread(img_path)
        if img is None:
            return None, "Failed to read the image file"
        
        output_filename = None
        
        # Process image based on operation type
        match operation:
            case "cgray":
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                output_filename = f"{filename}"
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
                cv2.imwrite(output_path, gray)
            case "cpng":
                output_filename = f"{os.path.splitext(filename)[0]}.png"
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
                cv2.imwrite(output_path, img)
            case "cjpeg":
                output_filename = f"{os.path.splitext(filename)[0]}.jpeg"
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
                cv2.imwrite(output_path, img)
            case "cwebp":
                output_filename = f"{os.path.splitext(filename)[0]}.webp"
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
                cv2.imwrite(output_path, img)
            case "compress":
                quality = int(quality) if quality is not None else 50
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    ext = '.jpg'
                output_filename = f"compressed_{os.path.splitext(filename)[0]}{ext}"
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
                compression_params = []
                if ext in ['.jpg', '.jpeg']:
                    compression_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                elif ext == '.png':
                    compression_params = [cv2.IMWRITE_PNG_COMPRESSION, min(9, 9 - int(quality/10))]
                elif ext == '.webp':
                    compression_params = [cv2.IMWRITE_WEBP_QUALITY, quality]
                cv2.imwrite(output_path, img, compression_params)
                original_size = os.path.getsize(img_path)
                compressed_size = os.path.getsize(output_path)
                size_reduction = (original_size - compressed_size) / original_size * 100
                output_filename = f"{output_filename}|{round(size_reduction, 2)}"
            case _:
                return None, f"Unknown operation: {operation}"
        
        return output_filename, None
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    if request.method == "POST":
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type.startswith('multipart/form-data')
        def prepare_response(success, **kwargs):
            if is_ajax:
                return jsonify({"success": success, **kwargs})
            else:
                if not success and 'error' in kwargs:
                    flash(f"Error: {kwargs['error']}")
                elif success and 'message' in kwargs:
                    flash(kwargs['message'], 'success')
                return redirect(url_for('home'))
        
        if 'operation' not in request.form:
            return prepare_response(False, error='No operation selected')
            
        operation = request.form.get("operation")
        quality = request.form.get("quality") if 'quality' in request.form else None
            
        if 'file' not in request.files:
            return prepare_response(False, error='No file part')
            
        file = request.files['file']
        if file.filename == "":
            return prepare_response(False, error='No selected file')
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            processed_result, error = process_image(filename, operation, quality)
            if error:
                return prepare_response(False, error=error)
            else:
                if '|' in processed_result:
                    processed_filename, size_reduction = processed_result.split('|')
                    processed_url = url_for('static', filename=f'processed/{processed_filename}')
                    message = f"Your image has been compressed with {size_reduction}% size reduction"
                    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
                    file_size = f"{os.path.getsize(processed_path) / 1024:.2f} KB"
                    try:
                        img = cv2.imread(processed_path)
                        dimensions = f"{img.shape[1]} × {img.shape[0]}"
                    except:
                        dimensions = "Unknown"
                    format_name = os.path.splitext(processed_filename)[1][1:].upper()
                    return prepare_response(
                        True, 
                        message=message, 
                        processed_url=processed_url,
                        file_size=file_size,
                        dimensions=dimensions,
                        format=format_name,
                        size_reduction=f"{size_reduction}%"
                    )
                else:
                    processed_url = url_for('static', filename=f'processed/{processed_result}')
                    message = f"Your image has been processed successfully"
                    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_result)
                    file_size = f"{os.path.getsize(processed_path) / 1024:.2f} KB"
                    try:
                        img = cv2.imread(processed_path)
                        dimensions = f"{img.shape[1]} × {img.shape[0]}"
                    except:
                        dimensions = "Unknown"
                    format_name = os.path.splitext(processed_result)[1][1:].upper()
                    return prepare_response(
                        True, 
                        message=message, 
                        processed_url=processed_url,
                        file_size=file_size,
                        dimensions=dimensions,
                        format=format_name
                    )
        return prepare_response(False, error="Invalid file type")
    
    return render_template("index.html")

@app.route("/docs")
def docs():
    return render_template("doc.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
