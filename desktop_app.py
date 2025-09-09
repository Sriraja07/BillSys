import webview
from app import app

if __name__ == '__main__':
    #with app.app_context():
        #db.create_all()
        #create_default_admin()
    #app.run(debug=True) 
    webview.create_window('Electrical Billing App', app,min_size=(700,500),frameless=False,resizable=True)
    webview.start(ssl=True, http_server=True,debug=False)