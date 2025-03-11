from datetime import datetime
from app import db
from passlib.hash import pbkdf2_sha256

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accounts = db.relationship('Account', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    account_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transactions_from = db.relationship('Transaction', 
                                     foreign_keys='Transaction.from_account_id',
                                     backref='from_account', lazy='dynamic')
    transactions_to = db.relationship('Transaction', 
                                   foreign_keys='Transaction.to_account_id',
                                   backref='to_account', lazy='dynamic')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, transfer
    amount = db.Column(db.Float, nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    to_account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')
    description = db.Column(db.String(200))
