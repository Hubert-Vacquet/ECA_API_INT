from flask import Blueprint, request, jsonify
from app.services.enedis_service import validate_pdl

enedis_bp = Blueprint('enedis', __name__)

@enedis_bp.route('/validate_enedis', methods=['POST'])
def validate_enedis():
    data = request.get_json()
    pdl = data.get('usage_point_id')

    if not pdl:
        return jsonify({"status": "error", "message": "PDL manquant"}), 400

    # Remplacez cette liste par votre logique de validation réelle
    PDL_ACTIVÉS = ["22516914714270", "11453290002823"]

    print("PDL: ", pdl)

    if pdl in PDL_ACTIVÉS:
        print("PDL validé : ", pdl)
        return jsonify({"status": "validated"}), 200
    else:
        print("PDL NON validé : ", pdl)
        return jsonify({"status": "error", "message": "PDL non activé"}), 403
