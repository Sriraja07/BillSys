import webview
import threading
import time
import sys
import os
from app import app, db, create_default_admin

def start_flask():
    """Start the Flask application"""
    app.run(debug=False, port=5000, host='127.0.0.1', use_reloader=False)

def create_window():
    """Create and configure the desktop window"""
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Create the webview window
    webview.create_window('Electrical Billing Software',app,
        min_size=(700, 600),
        resizable=True,
        maximized=False,
        on_top=False,
        shadow=True,
        vibrancy=False
    )
    
    # Start the webview
    webview.start(ssl=True, http_server=True,debug=False)

def main():
    """Main function to start the desktop application"""
    print("🚀 Starting Electrical Billing Software...")
    
    # Initialize database
    with app.app_context():
        db.create_all()
        create_default_admin()
        print("✅ Database initialized")
    
    # Start Flask in a separate thread
    #flask_thread = threading.Thread(target=start_flask, daemon=True)
    #flask_thread.start()
    print("✅ Flask server starting...")
    
    # Create and start the desktop window
    try:
        create_window()
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 