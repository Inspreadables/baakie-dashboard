from dashboard import app

if __name__ == '__main__':
    # Turn off debug mode for production
    app.run(host='0.0.0.0', port=5000, debug=False)
