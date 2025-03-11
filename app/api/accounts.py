from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Account, User
from app import db
import random
import string

bp = Blueprint('accounts', __name__)

def generate_account_number():
    """Generate a random 10-digit account number"""
    return ''.join(random.choices(string.digits, k=10))

def check_account_owner(account_id, user_id):
    """Check if the account belongs to the user"""
    account = Account.query.get_or_404(account_id)
    if account.user_id != user_id:
        return False, account
    return True, account

@bp.route('', methods=['GET'])
@jwt_required()
def get_accounts():
    current_user_id = get_jwt_identity()
    accounts = Account.query.filter_by(user_id=current_user_id).all()
    
    return jsonify([{
        'id': account.id,
        'account_number': account.account_number,
        'account_type': account.account_type,
        'balance': account.balance,
        'created_at': account.created_at.isoformat()
    } for account in accounts])

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_account(id):
    current_user_id = get_jwt_identity()
    is_owner, account = check_account_owner(id, current_user_id)
    
    if not is_owner:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify({
        'id': account.id,
        'account_number': account.account_number,
        'account_type': account.account_type,
        'balance': account.balance,
        'created_at': account.created_at.isoformat()
    })

@bp.route('', methods=['POST'])
@jwt_required()
def create_account():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if 'account_type' not in data:
        return jsonify({'error': 'Account type is required'}), 400
        
    # Validate account type
    valid_types = ['savings', 'checking']
    if data['account_type'].lower() not in valid_types:
        return jsonify({'error': f'Account type must be one of: {", ".join(valid_types)}'}), 400
    
    # Generate unique account number
    while True:
        account_number = generate_account_number()
        if not Account.query.filter_by(account_number=account_number).first():
            break
    
    account = Account(
        account_number=account_number,
        account_type=data['account_type'].lower(),
        user_id=current_user_id,
        balance=0.0
    )
    
    db.session.add(account)
    db.session.commit()
    
    return jsonify({
        'message': 'Account created successfully',
        'account': {
            'id': account.id,
            'account_number': account.account_number,
            'account_type': account.account_type,
            'balance': account.balance,
            'created_at': account.created_at.isoformat()
        }
    }), 201

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_account(id):
    current_user_id = get_jwt_identity()
    is_owner, account = check_account_owner(id, current_user_id)
    
    if not is_owner:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    if 'account_type' in data:
        valid_types = ['savings', 'checking']
        if data['account_type'].lower() not in valid_types:
            return jsonify({'error': f'Account type must be one of: {", ".join(valid_types)}'}), 400
        account.account_type = data['account_type'].lower()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Account updated successfully',
        'account': {
            'id': account.id,
            'account_number': account.account_number,
            'account_type': account.account_type,
            'balance': account.balance,
            'created_at': account.created_at.isoformat()
        }
    })

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_account(id):
    current_user_id = get_jwt_identity()
    is_owner, account = check_account_owner(id, current_user_id)
    
    if not is_owner:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if account.balance > 0:
        return jsonify({'error': 'Cannot delete account with positive balance'}), 400
    
    db.session.delete(account)
    db.session.commit()
    
    return jsonify({'message': 'Account deleted successfully'})
