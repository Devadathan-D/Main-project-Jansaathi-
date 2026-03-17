from flask import Flask, jsonify

from app.config import Config
from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)

    # 1. Configuration
    app.config.from_object(Config)

    # 2. Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # 3. Root Route (Health Check)
    @app.route("/", methods=["GET"])
    def health_check():
        """Returns 200 OK to verify the server is running."""
        return jsonify(
            {
                "status": "success",
                "message": "Jansaathi Backend API is running",
                "version": "1.0",
            }
        ), 200

    # 4. Register Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.document_routes import document_bp
    from .routes.recommendation_routes import recommendation_bp
    from .routes.scheme_routes import scheme_bp
    from .routes.user_routes import user_bp

    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(scheme_bp, url_prefix="/api/schemes")
    app.register_blueprint(recommendation_bp, url_prefix="/api/recommendations")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(document_bp, url_prefix="/api/documents")

    # 5. Database & Engine Initialization
    with app.app_context():
        db.create_all()

        try:
            from app.recommendation.content import ContentRecommender

            app.recommender = ContentRecommender()
            print("System: Recommendation Engine Loaded Successfully.")
        except ImportError as e:
            print(f"Warning: Could not load Recommendation Engine. Error: {e}")
        except Exception as e:
            print(f"Warning: Error initializing Recommendation Engine. Error: {e}")

    return app
