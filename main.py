from flask import Flask,render_template,request,flash,redirect,url_for
from werkzeug.utils import secure_filename
import os 
import cv2

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'webp', 'gif', 'png', 'jpg', 'jpeg'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'the rando
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/")
def ProcessImage(filename, operation):
    img=cv2.imread(f"static/uploads/{filename}")
    match operation:
        case "cgray":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            newfilename=f"static\processed\{filename}"
            cv2.imwrite(newfilename,gray)
            return newfilename
        case "cpng":
            newfilename=f"static\processed\{filename.split('.')[0]}.png"
            cv2.imwrite(newfilename,img)
            return newfilename
        case "cjpeg":
            newfilename=f"static\processed\{filename.split('.')[0]}.jpeg"
            cv2.imwrite(newfilename,img)
            return newfilename
        case "cwebp":
            newfilename=f"static\processed\{filename.split('.')[0]}.webp"
            cv2.imwrite(newfilename,img)
            return newfilename

    
    print(f"the operation is {operation} and filename is {filename}")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/edit",methods=['GET','POST'])
def edit():
    if request.method=="POST":
         operation=request.form.get("operation")
         if 'file' not in request.files:
            flash('No file part')
            return "Error"
    file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
    if file.filename =="":
            flash('No selected file')
            return "error no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new=ProcessImage(filename,operation)
        flash(f"your Image has been processed and is available <a href='/{new}' target='_blank'>here</a>")
        return render_template("index.html")






@app.route("/docs")
def docs():
    return render_template("doc.html")

app.run(debug=True,port=5001)
