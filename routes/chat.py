from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ml.chatbot import chat_response

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat')
@login_required
def index():
    if current_user.role == 'customer':
        return render_template('chat/customer.html')
    return render_template('chat/index.html')


@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send():
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'reply': 'Please type a message.'})

    result = chat_response(message, current_user)
    return jsonify(result)
