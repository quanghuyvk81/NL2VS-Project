from flask import Flask, request, send_from_directory, jsonify
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return "Flask server is running"

@app.route('/uploads/data/<filename>')
def get_data_file(filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], 'data')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return send_from_directory(folder_path, filename)

@app.route('/uploads/images/<filename>')
def get_image_file(filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return send_from_directory(folder_path, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400

    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400

    if file:
        filename = file.filename
        if filename.endswith(('.csv', '.xlsx')):
            folder = 'data'
        elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')):
            folder = 'images'
        else:
            return {'error': 'File type not supported'}, 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
        file.save(file_path)
        return {'file_url': f'/uploads/{folder}/{filename}'.replace(os.sep, '/')}, 200

@app.route('/uploads', methods=['GET'])
def list_files():
    files_data = {}
    for folder in ['data', 'images']:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        if os.path.exists(folder_path):
            files_data[folder] = os.listdir(folder_path)
        else:
            files_data[folder] = []
    return jsonify(files_data)

if __name__ == '__main__':
    for folder in ['data', 'images']:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    app.run(host='0.0.0.0', port=5001)
