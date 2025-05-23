import logging
from flask import Blueprint, request, jsonify
from app.config import Config
from app.utils.db import get_db_connection
from datetime import datetime

housing_bp = Blueprint('housing', __name__)

@housing_bp.route('/housings', methods=['GET'])
def get_housings_by_user():
    user_id = request.args.get('user_id')
    if not user_id or user_id == "null":
        return jsonify({"error": "user_id manquant"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT BID, NOM_BIEN, USAGE_POINT_ID
            FROM BIEN_IMMOBILIER
            WHERE PROPRIETAIRE = ?
        """, (user_id,))
        rows = cur.fetchall()

        housings = [
            {"id": row[0], "nom_bien": row[1], "pdl": row[2]}
            for row in rows
        ]

        cur.close()
        conn.close()

        return jsonify(housings), 200

    except Exception as e:
        logging.exception("Erreur lors de la récupération des logements :", e)
        return jsonify({"error": "Erreur serveur"}), 500

@housing_bp.route('/housing/<int:bid>', methods=['GET'])
def get_housing_by_bid(bid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT BID, NOM_BIEN, USAGE_POINT_ID, PROPRIETAIRE
            FROM BIEN_IMMOBILIER
            WHERE BID = ?
        """, (bid,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if row is None:
            return jsonify({"error": "Aucun logement trouvé avec cet identifiant."}), 404

        housing = {
            "id": row[0],
            "nom_bien": row[1],
            "pdl": row[2],
            "proprietaire": row[3]
        }

        return jsonify(housing), 200

    except Exception as e:
        logging.exception("Erreur lors de la récupération du logement :", e)
        return jsonify({"error": "Erreur serveur"}), 500

@housing_bp.route('/housing/<int:bid>', methods=['PUT'])
def update_housing(bid):
    data = request.get_json()
    nom_bien = data.get('nom_bien')
    pdl = data.get('pdl')

    if not nom_bien or not pdl:
        return jsonify({'error': 'Les champs nom_bien et pdl sont requis.'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE BIEN_IMMOBILIER
            SET NOM_BIEN = ?, USAGE_POINT_ID = ?, DATE_DERNIERE_MODIFICATION = ?
            WHERE BID = ?
        """, (nom_bien, pdl, datetime.now(), bid))

        if cur.rowcount == 0:
            return jsonify({'error': 'Aucun logement trouvé avec cet ID.'}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Logement mis à jour avec succès.'}), 200

    except Exception as e:
        logging.exception("Erreur lors de la mise à jour du logement :", e)
        return jsonify({'error': 'Erreur serveur'}), 500

@housing_bp.route('/housing/<housing_id>', methods=['DELETE'])
def delete_housing(housing_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Récupérer le propriétaire avant suppression
        cur.execute("SELECT PROPRIETAIRE FROM BIEN_IMMOBILIER WHERE BID = ?", (housing_id,))
        result = cur.fetchone()
        if not result:
            return jsonify({'message': 'Aucun logement trouvé avec cet ID.'}), 404
        proprietaire = result[0]

        # Supprimer le logement
        cur.execute("DELETE FROM BIEN_IMMOBILIER WHERE BID = ?", (housing_id,))
        rows_affected = cur.rowcount

        # Vérifier s'il reste d'autres logements
        cur.execute("SELECT COUNT(*) FROM BIEN_IMMOBILIER WHERE PROPRIETAIRE = ?", (proprietaire,))
        count = cur.fetchone()[0]

        # Supprimer le rôle si aucun autre logement
        if count == 0:
            cur.execute("DELETE FROM PROFIL_UTILISATEUR WHERE UID = ? AND ROLE = 'Propriétaire'", (proprietaire,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Logement supprimé avec succès.'}), 200

    except Exception as e:
        logging.exception("Erreur lors de la suppression du logement :", e)
        return jsonify({'error': 'Erreur serveur'}), 500

@housing_bp.route('/housings', methods=['POST'])
def add_housing():
    data = request.get_json()
    user_id = data.get('user_id')
    nom_bien = data.get('nom_bien')
    pdl = data.get('pdl')

    if not user_id or not nom_bien or not pdl:
        return jsonify({"error": "user_id, nom_bien et pdl sont requis"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Récupérer le BID le plus élevé actuel
        cur.execute("SELECT MAX(BID) FROM BIEN_IMMOBILIER")
        max_bid = cur.fetchone()[0]
        new_bid = max_bid + 1 if max_bid is not None else 1

        # Insérer le logement
        cur.execute("""
            INSERT INTO BIEN_IMMOBILIER ( PROPRIETAIRE, NOM_BIEN, USAGE_POINT_ID, DATE_DERNIERE_MODIFICATION, UTILISATEUR_MODIFICATION )
            VALUES ( ?, ?, ?, ? , ?)
            RETURNING BID
        """, (user_id, nom_bien, pdl, datetime.now(), user_id))
        new_bid = cur.fetchone()[0]

        # Vérifier si l'utilisateur a déjà le rôle
        cur.execute("""
            SELECT 1 FROM PROFIL_UTILISATEUR
            WHERE UID = ? AND ROLE = 'Propriétaire'
        """, (user_id,))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO PROFIL_UTILISATEUR (UID, ROLE)
                VALUES (?, 'Propriétaire')
            """, (user_id,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Logement ajouté avec succès", "bid": new_bid}), 201

    except Exception as e:
        logging.exception("Erreur lors de l'ajout du logement :", e)
        return jsonify({"error": "Erreur serveur"}), 500
