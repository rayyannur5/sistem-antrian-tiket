from .extensions import db

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Database models
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    holds = db.relationship('TicketHold', backref='User', lazy=True)

class Ticket(db.Model):
    __tablename__ = 'Ticket'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    holds = db.relationship('TicketHold', backref='Ticket', lazy=True)

class TicketHold(db.Model):
    __tablename__ = 'TicketHold'
    id = db.Column(db.String(36), primary_key=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)  # ForeignKey added here
    ticket_id = db.Column(db.Integer, db.ForeignKey('Ticket.id'), nullable=False)  # ForeignKey added here

class Transaction(db.Model):
    __tablename__ = 'Transaction'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)  # ForeignKey added here
    ticket_id = db.Column(db.Integer, db.ForeignKey('Ticket.id'), nullable=False)  # ForeignKey added here

