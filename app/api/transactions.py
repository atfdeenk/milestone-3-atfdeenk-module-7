from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Transaction, Account, User
from app import db
from datetime import datetime

bp = Blueprint('transactions', __name__)

def check_account_owner(account_id, user_id):
    """Check if the account belongs to the user"""
    account = Account.query.get_or_404(account_id)
    if str(account.user_id) != str(user_id):
        return False, account
    return True, account

@bp.route('', methods=['GET'])
@jwt_required()
def get_transactions():
    current_user_id = get_jwt_identity()
    
    # Get query parameters for filtering
    account_id = request.args.get('account_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query: get all transactions related to user's accounts
    user_accounts = Account.query.filter_by(user_id=current_user_id).all()
    account_ids = [acc.id for acc in user_accounts]
    
    query = Transaction.query.filter(
        (Transaction.from_account_id.in_(account_ids)) |
        (Transaction.to_account_id.in_(account_ids))
    )
    
    # Apply filters if provided
    if account_id:
        if account_id not in account_ids:
            return jsonify({'error': 'Unauthorized access to account'}), 403
        query = query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        )
    
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date)
            query = query.filter(Transaction.timestamp >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date)
            query = query.filter(Transaction.timestamp <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    transactions = query.order_by(Transaction.timestamp.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'transaction_type': t.transaction_type,
        'amount': t.amount,
        'from_account_id': t.from_account_id,
        'to_account_id': t.to_account_id,
        'timestamp': t.timestamp.isoformat(),
        'status': t.status,
        'description': t.description
    } for t in transactions])

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_transaction(id):
    current_user_id = get_jwt_identity()
    transaction = Transaction.query.get_or_404(id)
    
    # Check if user owns either the source or destination account
    user_accounts = Account.query.filter_by(user_id=current_user_id).all()
    account_ids = [acc.id for acc in user_accounts]
    
    if (transaction.from_account_id not in account_ids and 
        transaction.to_account_id not in account_ids):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify({
        'id': transaction.id,
        'transaction_type': transaction.transaction_type,
        'amount': transaction.amount,
        'from_account_id': transaction.from_account_id,
        'to_account_id': transaction.to_account_id,
        'timestamp': transaction.timestamp.isoformat(),
        'status': transaction.status,
        'description': transaction.description
    })

@bp.route('', methods=['POST'])
@jwt_required()
def create_transaction():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['transaction_type', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['amount'] <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    
    transaction_type = data['transaction_type'].lower()
    valid_types = ['deposit', 'withdrawal', 'transfer']
    if transaction_type not in valid_types:
        return jsonify({'error': f'Transaction type must be one of: {", ".join(valid_types)}'}), 400
    
    # Handle different transaction types
    if transaction_type == 'transfer':
        if 'from_account_id' not in data or 'to_account_id' not in data:
            return jsonify({'error': 'Both from_account_id and to_account_id are required for transfers'}), 400
        
        # Check account ownership and existence
        is_owner, from_account = check_account_owner(data['from_account_id'], current_user_id)
        if not is_owner:
            return jsonify({'error': 'Unauthorized access to source account'}), 403
        
        to_account = Account.query.get_or_404(data['to_account_id'])
        
        # Check sufficient balance
        if from_account.balance < data['amount']:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Perform transfer
        from_account.balance -= data['amount']
        to_account.balance += data['amount']
        
        transaction = Transaction(
            transaction_type='transfer',
            amount=data['amount'],
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            description=data.get('description', 'Transfer')
        )
        
    elif transaction_type in ['deposit', 'withdrawal']:
        if 'account_id' not in data:
            return jsonify({'error': 'account_id is required'}), 400
        
        is_owner, account = check_account_owner(data['account_id'], current_user_id)
        if not is_owner:
            return jsonify({'error': 'Unauthorized access to account'}), 403
        
        if transaction_type == 'withdrawal' and account.balance < data['amount']:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Update balance
        if transaction_type == 'deposit':
            account.balance += data['amount']
            transaction = Transaction(
                transaction_type='deposit',
                amount=data['amount'],
                to_account_id=account.id,
                description=data.get('description', 'Deposit')
            )
        else:  # withdrawal
            account.balance -= data['amount']
            transaction = Transaction(
                transaction_type='withdrawal',
                amount=data['amount'],
                from_account_id=account.id,
                description=data.get('description', 'Withdrawal')
            )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'message': 'Transaction completed successfully',
        'transaction': {
            'id': transaction.id,
            'transaction_type': transaction.transaction_type,
            'amount': transaction.amount,
            'from_account_id': transaction.from_account_id,
            'to_account_id': transaction.to_account_id,
            'timestamp': transaction.timestamp.isoformat(),
            'status': transaction.status,
            'description': transaction.description
        }
    }), 201
