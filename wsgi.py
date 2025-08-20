from hello import app

# Remove the __main__ block for production; keep it for development testing only
if __name__ == '__main__':
    app.run( host='127.0.0.1', port=5000, debug=True)