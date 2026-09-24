import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from configs.settings import config_by_name
from backend.services.db_init import init_db

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../frontend')
    app.config.from_object(config_by_name[config_name])
    CORS(app)
    
    # Initialize the database
    with app.app_context():
        init_db()

    # Register blueprints
    from backend.routes.api import api_bp
    app.register_blueprint(api_bp)

    # Security Headers Middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        return response

    # Global Error Handlers for Consistent JSON Responses
    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({"status": "error", "message": getattr(e, 'description', 'Bad Request')}), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    @app.errorhandler(413)
    def handle_payload_too_large(e):
        return jsonify({"status": "error", "message": "Request payload exceeds maximum allowed size (2MB)"}), 413

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"status": "error", "message": "An internal server error occurred"}), 500

    # Health and Status Endpoint
    @app.route('/api/status', methods=['GET'])
    def status():
        return jsonify({
            "status": "online",
            "service": "Autonomous Bioinformatics Analyst",
            "version": "1.0.0 (MVP Shell)"
        }), 200

    # Secure Frontend Serving (Path Traversal & Dotfile Protection)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        static_dir = os.path.abspath(app.static_folder)
        if path != "":
            # Reject dotfiles or hidden files
            parts = path.replace('\\', '/').split('/')
            if any(part.startswith('.') for part in parts if part):
                return jsonify({"status": "error", "message": "Access denied"}), 403

            target_path = os.path.abspath(os.path.join(static_dir, path))
            # Verify target path is strictly within static_dir to prevent path traversal
            if os.path.commonpath([static_dir, target_path]) == static_dir and os.path.isfile(target_path):
                return send_from_directory(static_dir, path)

        return send_from_directory(static_dir, 'index.html')

    return app

app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', True))
