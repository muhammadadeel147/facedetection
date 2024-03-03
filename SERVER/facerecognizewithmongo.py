
# !pip install face_recognition
# pip install pandas
#  import pandas as pd
# pip install os

# pip install cmake
# pip install dlib
# pip install flask_ngrok
# pip install Flask-PyMongo

# pip install face_recognition
# pip install flask_cors
import face_recognition
from flask import Flask, request, send_file, jsonify
# import pandas as pd
from flask_cors import CORS
from flask_ngrok import run_with_ngrok
import os

import pandas as pd
import face_recognition
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_ngrok import run_with_ngrok
from flask import Flask, request, send_file, jsonify
app = Flask(__name__)
CORS(app)


app.config['MONGO_URI'] = 'mongodb+srv://AMEER:TestingPuprpose@cluster0.boegp.mongodb.net/faceRecognization?retryWrites=true&w=majority'  # Replace with your MongoDB URI
mongo = PyMongo(app)

try:
    mongo.db.list_collection_names()  
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)




@app.route('/signup', methods=['POST']) 
def signup():
    global existing_data

    if 'file' not in request.files:
        return jsonify({'error': 'No file found'})
    if 'id' not in request.form or 'cnic' not in request.form:
        return jsonify({'error': 'No employee ID or CNIC found'})

    emp_id = request.form['id']
    cnic = request.form['cnic']
    name = request.form.get('name', '')
    city = request.form.get('city', '')  
    district = request.form.get('district', '')  
    province = request.form.get('province', '')  
    election_center = request.form.get('election_center', '')  

    file = request.files['file']

 
    if mongo.db.face_embeddings.find_one({'cnic': cnic}):
        return jsonify({'status': 'error', 'message': f'User with CNIC {cnic} already exists.'})


    image = face_recognition.load_image_file(file)

    face_locations = face_recognition.face_locations(image)
    

    if len(face_locations) > 0:
     
        face_encodings = face_recognition.face_encodings(image, face_locations)

     
        face_encodings_str = [", ".join(map(str, encoding)) for encoding in face_encodings]

        mongo.db.face_embeddings.insert_one({
            'emp_id': emp_id,
            'cnic': cnic,
            'name': name,
            'city': city,
            'district': district,
            'province': province,
            'election_center': election_center,
            'embeddings': face_encodings_str
        })

        return jsonify({
            'status': 'success',
            'message': f'Embeddings of Employee ID {emp_id} with CNIC {cnic} added and saved successfully.'
        })
    else:
        return jsonify({'status': 'error', 'message': 'No faces found in the image.'})



@app.route('/face_match_login', methods=['POST'])
def face_match_login():

    if 'cnic' not in request.form:
        return jsonify({'error': 'CNIC not found'})

    cnic = request.form['cnic']


    if 'file' not in request.files:
        return jsonify({'error': 'No file found'})

    file = request.files['file']

    incoming_image = face_recognition.load_image_file(file)
    incoming_embedding = face_recognition.face_encodings(incoming_image)

    if len(incoming_embedding) > 0:
        incoming_embedding = incoming_embedding[0]

     
        existing_data = list(mongo.db.face_embeddings.find({'cnic': cnic}))

   
        match_found = False
        matched_user_data = None

        for row in existing_data:
            existing_embeddings = row['embeddings']
            for existing_embedding_str in existing_embeddings:
                existing_embedding = eval(existing_embedding_str) 

              
                results = face_recognition.compare_faces([existing_embedding], incoming_embedding)
                if results[0]:
                    match_found = True
                    matched_user_data = {
                        'emp_id': row.get('emp_id', ''),
                        'cnic': row.get('cnic', ''),
                        'name': row.get('name', ''),
                        'city': row.get('city', ''),
                        'district': row.get('district', ''),
                        'province': row.get('province', ''),
                        'election_center': row.get('election_center', '')
                      
                    }
                    break

        if match_found:
            print('************* Face Matched')
            response_data = {
                'match_status': 'image matched',
                'success': True,
                'data': matched_user_data
            }
        else:
            print('************* Face Not Matched')
            response_data = {
                'match_status': 'image not match',
                'success': False
            }
    else:
        response_data = {'error': 'No face detected in the incoming image.'}

    return jsonify(response_data)

@app.route('/login', methods=['POST'])
def login_user():
  
    request_data = request.get_json()

 
    if 'cnic' not in request_data:
        return jsonify({'error': 'CNIC not found'})

    cnic = request_data['cnic']


    print(f"Received CNIC: {cnic}")


    user_data = mongo.db.face_embeddings.find_one({'cnic': cnic})

    if user_data:
     
        user_name = user_data.get('name', 'Name not available')
        cnic_data = user_data.get('cnic', 'Cnic not available')
        response_data = {
            'success': True,
            'data':{
                'name': user_name,
                'cnic':cnic_data,
            }
        }
    else:
        response_data = {
            'error': 'User not found',
            'success': False
        }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run()
