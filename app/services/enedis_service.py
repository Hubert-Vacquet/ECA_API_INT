from flask import jsonify

# À centraliser ou lier à la base si besoin réel
PDL_ACTIVÉS = [
    "22516914714270",
    "11453290002823"
]

def validate_pdl(data):
    pdl = data.get('usage_point_id')

    if not pdl:
        return jsonify({"status": "error", "message": "PDL manquant"}), 400

    if pdl in PDL_ACTIVÉS:
        return jsonify({"status": "validated"}), 200
    else:
        return jsonify({"status": "error", "message": "PDL non activé"}), 403
