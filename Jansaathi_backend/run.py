from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    # debug=True enables auto-reloading when you save code changes
    app.run(host='0.0.0.0', port=5000, debug=True)
