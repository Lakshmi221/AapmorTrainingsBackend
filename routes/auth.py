# from flask import Blueprint, request, jsonify, make_response
# import jwt
# import datetime
# from flask_cors import CORS
# from dotenv import load_dotenv
# import os

# auth_bp = Blueprint('auth', __name__)
# CORS(auth_bp, supports_credentials=True,origins=["http://localhost:5173"])


# load_dotenv()
# @auth_bp.route("/verify-token", methods=["POST"])
# def verify_token():
#     data = request.get_json()
#     token = data.get("token")

#     if not token:
#         return jsonify({"error": "Token missing"}), 400

#     try:

#         secret_key = os.getenv("SECRET_KEY")
#         decoded = jwt.decode(token, secret_key, algorithms=["HS256"])


#         response = make_response(jsonify({
#             "message": "Token valid",
#             "user": {
            
#                 "name": decoded.get("FullName"),
#                 "department": decoded.get("Department"),
#                 "access":decoded.get("Access"),
#                 "role":decoded.get("User")
#             }
#         }))

#         response.set_cookie(
#             key="auth_token",
#             value=token,
#             httponly=True,
#             secure=False,           # 🔄 Use True in production with HTTPS
#             samesite="Lax",         # Or "Strict" for tighter CSRF protection
#             max_age=86400,              # Ensure it's valid across app
#         )

#         return response

#     except jwt.ExpiredSignatureError:
#         return jsonify({"error": "Token expired"}), 401
#     except jwt.InvalidTokenError:
#         return jsonify({"error": "Invalid token"}), 401

# @auth_bp.route('/logout', methods=['POST'])
# def logout():
#     response = make_response(jsonify({"message": "Logged out"}), 200)
#     response.set_cookie('token', '', expires=0, httponly=True, samesite='Strict', secure=True)
#     return response
