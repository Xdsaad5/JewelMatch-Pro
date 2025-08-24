from flask import Flask, request, jsonify, render_template
import os
import shutil
import ast
from image import *
from datetime import datetime


app = Flask(__name__)

output_folder = os.path.join('static', 'matched_images')
os.makedirs(output_folder, exist_ok=True)
items = []
workers = []

def parse_filter_parameters(form_data):
    """Extracts and converts filter parameters to their respective data types."""
    item = ast.literal_eval(form_data.get('item_name', '{}'))
    worker = ast.literal_eval(form_data.get('worker_name', '{}'))

    filters = {
        'item_id': int(item.get('itemId')) if item.get('itemId') else None,
        'worker_id': int(worker.get('workerId')) if worker.get('workerId') else None,
        'date_from': datetime.strptime(form_data.get('date_from'), '%Y-%m-%d').date() 
                   if form_data.get('date_from') else None,
        'date_to': datetime.strptime(form_data.get('date_to'), '%Y-%m-%d').date() 
                 if form_data.get('date_to') else None,
        'net_weight_from': float(form_data.get('net_weight_from')) 
                         if form_data.get('net_weight_from') else None,
        'net_weight_to': float(form_data.get('net_weight_to')) 
                       if form_data.get('net_weight_to') else None,
        'weight_from': float(form_data.get('weight_from')) 
                     if form_data.get('weight_from') else None,
        'weight_to': float(form_data.get('weight_to')) 
                   if form_data.get('weight_to') else None,
    }
    return filters

@app.route('/')
def dashboard():
    global items
    items = get_items()
    global workers
    workers = get_worker()
    return render_template('img-detector.html', items=items,workers=workers)

@app.route('/match', methods=['POST'])
def match_jewelry():
    print("Form data received:", request.form)  # Debug all form data
    form = request.form

    data = parse_filter_parameters(request.form)
    print('data: ',data)
    sold_items = sold_stock(data)
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    if os.path.isdir(output_folder):
        shutil.rmtree(output_folder)  # Delete the directory and all its contents
        os.makedirs(output_folder)
    file = request.files['image']
    temp_path = "temp_upload.jpg"
    file.save(temp_path)
    
    matches = fetch_db_images(sold_items,output_folder)
    os.remove(temp_path)
    print('matches:', matches)
    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)  # Expose to LAN

