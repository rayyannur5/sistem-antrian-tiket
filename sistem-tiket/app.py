# service1/app.py
from flask import Flask, request, jsonify
from celery import Celery
import os
from models import User, Ticket, TicketHold, db
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Configure Celery
celery = Celery(
    app.name,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)


@app.route('/get_id', methods=['POST'])
def get_id():
    data = request.json
    user_id = data.get('user_id')
    ticket_id = data.get('ticket_id')

    if not user_id or not ticket_id:
        return jsonify({
            'message': 'User ID and Ticket ID are required'
        }), 400

    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.stock <= 0:
        return jsonify({
            'message': 'Ticket not available or out of stock'
        }), 400

    hold_id = str(uuid.uuid4())
    expiration_time = datetime.now() + timedelta(minutes=5)

    ticket_hold = TicketHold(id=hold_id, expires_at=expiration_time, user_id=user_id, ticket_id=ticket_id)
    db.session.add(ticket_hold)
    db.session.commit()

    return jsonify({
        'id': hold_id,
        'expires_at': expiration_time.strftime('%Y-%m-%d %H:%M:%S'),
        'ticket': {
            'id': ticket.id,
            'name': ticket.name
        }
    }), 201

@app.route('/purchase', methods=['POST'])
def purchase():
    data = request.json
    hold_id = data.get('id')

    if not hold_id:
        return jsonify({
            'message': 'Hold ID is required'
        }), 400

    ticket_hold = TicketHold.query.get(hold_id)

    if not ticket_hold:
        return jsonify({
            'message': 'Hold not found or expired'
        }), 404

    if datetime.now() > ticket_hold.expires_at:
        db.session.delete(ticket_hold)
        db.session.commit()
        return jsonify({
            'message': 'Hold has expired'
        }), 410

    ticket = Ticket.query.get(ticket_hold.ticket_id)
    if ticket.stock <= 0:
        return jsonify({
            'message': 'Ticket out of stock'
        }), 400

    # Reduce ticket stock
    ticket.stock -= 1
    db.session.delete(ticket_hold)
    db.session.commit()

    return jsonify({
        'message': 'Purchase successful',
        'ticket': {
            'id': ticket.id,
            'name': ticket.name,
            'remaining_stock': ticket.stock
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
