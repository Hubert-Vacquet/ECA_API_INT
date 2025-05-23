from flask import Blueprint, request, jsonify
from app.services.mail_service import send_verification_code

mail_bp = Blueprint('mail', __name__)

@mail_bp.route('/api/send_test_email', methods=['POST'])
def send_test_email():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code', '123456')

    if not email:
        return jsonify({"status": "error", "message": "Adresse email manquante"}), 400

    try:
        send_verification_code(email, code)
        return jsonify({"status": "success", "message": f"Code envoyé à {email}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
