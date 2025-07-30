import os
import logging
import argparse
from decouple import config
from flask import Flask, request, jsonify
from functools import wraps
import jwt
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Load secrets from environment
SECRET_KEY = config('SECRET_KEY')

# RBAC Roles and Permissions
roles_permissions = {
    'admin': {'read', 'write', 'delete'},
    'user': {'read'},
}

user_roles = {
    'user1': 'admin',
    'user2': 'user',
}

def create_token(username):
    payload = {'username': username}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['username']
    except jwt.ExpiredSignatureError:
        logging.error('Token expired')
        return None
    except jwt.InvalidTokenError:
        logging.error('Invalid token')
        return None

def rbac_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            username = decode_token(token)
            if username is None or username not in user_roles:
                logging.warning('Access denied: Invalid token or user')
                return jsonify({'message': 'Access denied'}), 403
            
            role = user_roles[username]
            if permission not in roles_permissions.get(role, set()):
                logging.warning(f'Access denied: User {username} does not have permission {permission}')
                return jsonify({'message': 'Access denied'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/read', methods=['GET'])
@rbac_required('read')
def read_data():
    logging.info('Read data accessed')
    return jsonify({'data': 'This is some protected data.'})

@app.route('/write', methods=['POST'])
@rbac_required('write')
def write_data():
    logging.info('Write data accessed')
    data = request.json
    logging.info(f'Data written: {data}')
    return jsonify({'message': 'Data written successfully.'}), 201

@app.route('/delete', methods=['DELETE'])
@rbac_required('delete')
def delete_data():
    logging.info('Delete data accessed')
    logging.info('Data deleted')
    return jsonify({'message': 'Data deleted successfully.'}), 200

def cli_main():
    parser = argparse.ArgumentParser(description='RBAC Example CLI')
    parser.add_argument('command', choices=['start', 'token'], help='Command to execute')
    parser.add_argument('--user', help='Username for token generation', required=False)
    args = parser.parse_args()

    if args.command == 'start':
        logging.info('Starting Flask app')
        app.run()
    elif args.command == 'token' and args.user:
        token = create_token(args.user)
        print(f'Token for {args.user}: {token}')
    else:
        logging.error('Invalid command or missing arguments')

if __name__ == '__main__':
    cli_main()