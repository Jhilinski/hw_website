from hello import app, socketio  # Import app and socketio from your main app file

# Remove the __main__ block for production; keep it for development testing only
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)