from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User
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
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'User created successfully',
        'access_token': access_token
    }), 201

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
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
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'Invalid or missing token'}), 401
            
        user = User.query.get_or_404(current_user_id)
        
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
                'name': user.name
            }
        })
    
    return jsonify({'error': 'Invalid email or password'}), 401
