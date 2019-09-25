from flask import Flask , render_template
from flask_socketio import SocketIO , emit

app = Flask(__name__)

app.config['SECRET_KEY']='165165555555516'
socketio = SocketIO( app )

@app.route('/')
def index ():
	return "jgjhgj"

if __name__ =='__main__':
	socketio.run(app, debug=True)