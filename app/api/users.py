from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, Account
from app import db
from email_validator import validate_email, EmailNotValidError

bp = Blueprint('users', __name__)

@bp.route('', methods=['POST'])
def create_user():
    print('Request Headers:', dict(request.headers))
    print('Request Body:', request.get_data(as_text=True))
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate email
    try:
        validate_email(data['email'], check_deliverability=False)
    except EmailNotValidError as e:
        return jsonify({
            'error': 'Invalid email address',
            'details': str(e)
        }), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    user = User(
        email=data['email'],
        name=data['name']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Generate access token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'User created successfully',
        'access_token': access_token
    }), 201

@bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users]
    })

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        current_user_id = int(get_jwt_identity())
    except:
        return jsonify({
            'error': 'Authentication failed',
            'details': 'Invalid token format'
        }), 401
        
    if not current_user_id:
        return jsonify({
            'error': 'Authentication failed',
            'details': 'Invalid or expired token'
        }), 401
        
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({
            'error': 'User not found',
            'details': 'Your account could not be found'
        }), 404
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'created_at': user.created_at.isoformat()
    })

@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_user_profile():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'details': 'Your account could not be found'
            }), 404
        
        try:
            data = request.get_json()
            print(f'Received data: {data}')
        except Exception as e:
            return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 400
            
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
            
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON format'}), 400
            
        # Update name if provided
        if 'name' in data:
            if not isinstance(data['name'], str):
                return jsonify({'error': 'Name must be a string'}), 400
            if not data['name'].strip():
                return jsonify({'error': 'Name cannot be empty'}), 400
            user.name = data['name'].strip()
            
        # Update email if provided
        if 'email' in data:
            try:
                validate_email(data['email'], check_deliverability=False)
                # Check if new email is already taken
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != current_user_id:
                    return jsonify({'error': 'Email already taken'}), 409
                user.email = data['email']
            except EmailNotValidError as e:
                return jsonify({'error': f'Invalid email address: {str(e)}'}), 400
                
        # Update password if provided
        if 'password' in data:
            if not isinstance(data['password'], str):
                return jsonify({'error': 'Password must be a string'}), 400
            if len(data['password']) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            user.set_password(data['password'])
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating profile: {str(e)}'}), 400

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at.isoformat()
            }
        })
    
    return jsonify({'error': 'Invalid email or password'}), 401

@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        # For security, don't reveal if email exists
        return jsonify({'message': 'If your email is registered, you will receive a password reset link'}), 200
    
    # Generate a reset token (in real app, send via email)
    reset_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=1))
    
    return jsonify({
        'message': 'Password reset instructions sent',
        'temp_token': reset_token  # In production, this should be sent via email
    }), 200

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    
    if not data or 'token' not in data or 'new_password' not in data:
        return jsonify({'error': 'Token and new password are required'}), 400
    
    try:
        # Verify the reset token
        user_id = get_jwt_identity(data['token'])
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Invalid token'}), 400
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password reset successful'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Invalid or expired token'}), 400

@bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_user():
    try:
        current_user_id = int(get_jwt_identity())
    except:
        return jsonify({
            'error': 'Authentication failed',
            'details': 'Invalid token format'
        }), 401
        
    if not current_user_id:
        return jsonify({
            'error': 'Authentication failed',
            'details': 'Invalid or expired token'
        }), 401
        
    try:
        # Check if user exists
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'error': 'User not found',
                'details': 'Your account could not be found'
            }), 404
            
        # Delete all associated accounts (this will cascade delete transactions)
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        for account in accounts:
            db.session.delete(account)
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Your account and all associated data have been deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Error deleting account',
            'details': str(e)
        }), 400
