from flask import Flask
from routes.trainings_routes import trainings_bp
from routes.users import users_bp
# from routes.auth import auth_bp
from utils.error_log import error_bp
from utils.cloudinary_config import *
from flask_cors import CORS
from email_services.mail_config import init_mail
from email_services.scheduler import start_scheduler
from email_services.mail_config import mail
from flask import request, jsonify
import jwt
import os
from utils.logger import setup_logger

app = Flask(__name__)
logger = setup_logger("main")
CORS(
    app,
supports_credentials=True,
    resources={r"/*": {"origins": "*", "send_wildcard": False}},
)

init_mail(app)
start_scheduler()

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"}, 200



@app.route('/verify-token', methods=['GET'])
def verify_token(): 
    auth_header = request.headers.get('Authorization', '')
    if not auth_header or not auth_header.lower().startswith('bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    token = auth_header.split(' ', 1)[1]
    
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        return jsonify({'payload': payload, 'valid': True}), 200
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)}), 401
        



# Register blueprints
app.register_blueprint(trainings_bp)
app.register_blueprint(users_bp)
# app.register_blueprint(auth_bp)
app.register_blueprint(error_bp)



if __name__ == '__main__':
    app.run(port=8000, debug=True)
