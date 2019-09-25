from flask import Flask, render_template, flash, request, redirect
from flask import url_for, make_response, jsonify
from flask import send_from_directory
import os
from os import environ as env
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from flask import session as login_session
from database import Base,msg_history,User
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from authlib.flask.client import OAuth
from six.moves.urllib.parse import urlencode

import httplib2
import json
import requests
from flask_socketio import SocketIO,emit,send,join_room, leave_room
import http.client


app = Flask(__name__)
app.config['SECRET_KEY']='15324'
engine = create_engine('sqlite:///site.db')
Base.metadata.bind = engine

# uploads images
UPLOAD_FOLDER = os.path.basename('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# send images from directory
@app.route('/upload/full/<filename>')
def send_img(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()
Base.metadata.create_all(engine)
socketio =SocketIO(app)
def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'profile' not in login_session:
      # Redirect to Login page here
      return redirect('/login')
    return f(*args, **kwargs)

  return decorated
var=""
amr="test"
@app.route('/chat/<guide_id>')
def chat(guide_id):
    var=guide_id
    print("var out--------------"+var)
    @requires_auth
    @socketio.on('connect')
    def on_connect():
        x = login_session['profile']
        room=x["user_id"]+var
        join_room(room)
    @socketio.on('message')
    def handlemessage(msgs):
        userinfo=login_session['profile']
        print('message:'+msgs)
        x=userinfo['user_id']+var
        print ("amr:------"+amr)
        newmsg = msg_history(msg=msgs,room=x,msg_from=userinfo['user_id'])
        session.add(newmsg)
        session.commit()
        message_from=userinfo['user_id']
        send((msgs,userinfo['user_id'],datetime.utcnow().strftime('%Y-%m-%d %H:%M')),broadcast=True,room=userinfo['user_id']+var)
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine
    print(guide_id)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    msgs = session.query(msg_history).all()
    userinfo=login_session['profile']
    return render_template('chat1.html',msgs=msgs,userinfo=login_session['profile'],room=userinfo['user_id']+guide_id)
msguser_id=""    
@app.route('/continuechat/<room>')
def continuechat(room):
    room=room
    @requires_auth
    @socketio.on('connect')
    def on_connect():
        x = login_session['profile']
        join_room(room)
    @socketio.on('message')
    def handlemessage(msg):
        userinfo=login_session['profile']
        print('message:'+msg)
        newmsg = msg_history(msg=msg,room=room,msg_from=userinfo['user_id'])
        session.add(newmsg)
        session.commit()
        send((msg,userinfo['user_id'],datetime.utcnow().strftime('%Y-%m-%d %H:%M')),broadcast=True,room=room)
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    msgs = session.query(msg_history).all()
    return render_template('chat1.html',msgs=msgs,userinfo=login_session['profile'],room=room)

@app.route('/')
def site():
    if 'profile' not in login_session:
        return render_template('site1.html',userinfo=None)
    else:    
        return render_template('site1.html',userinfo=login_session['profile'])

@app.route('/profile')
@requires_auth
def profile():
    userinfo=login_session['profile']
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    user_profile = session.query(User).filter_by(id=userinfo["user_id"]).first()
    return render_template('profile.html',userinfo=user_profile,send_img="send_img")

@app.route("/editprofile",methods=['GET', 'POST'])
@requires_auth
def editprofile():
    userinfo=login_session['profile']
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    userprofile = session.query(User).filter_by(id=userinfo["user_id"]).first()
    if request.method == 'POST':
        filename = userprofile.picture
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        userprofile.name = request.form['name']
        userprofile.country=request.form['country']
        userprofile.city=request.form['state']
        userprofile.picture=filename
        session.add(userprofile)
        session.commit()
        return redirect(url_for('profile'))
    else:    
	    return render_template("form.html")


oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id='eMgwZqvguQVh0lKHfSdqbzA6RH0lVNp2',
    client_secret='xMP9FsIQCy5t2lqoCDgUMDJ4g2iVezRQTkYNlxg5HxqL8bzaQ_sigKq2ubs_Dwri',
    api_base_url='https://directme.auth0.com',
    access_token_url='https://directme.auth0.com/oauth/token',
    authorize_url='https://directme.auth0.com/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)

@app.route('/callback')
def callback_handling():
    # Handles response from token endpoint
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    # Store the user information in flask session.
    login_session['jwt_payload'] = userinfo
    login_session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture'],
        'email': userinfo['email']
    }
    storeuser=login_session['profile']    
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    check = session.query(User).filter_by(id=storeuser['user_id']).first()
    if check == None:
            new_user = User(id=storeuser['user_id'],name=storeuser['name'],email=storeuser['email'],picture=storeuser['picture'])
            session.add(new_user)
            session.commit()

    return redirect('http://localhost:8080/dashboard')


@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri='http://localhost:8080/callback', audience='https://directme.auth0.com/userinfo')


@app.route('/dashboard')
@requires_auth
def dashboard():
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    users = session.query(User).all()	
    return render_template('dashboard.html',
                           userinfo=login_session['profile'],
                           userinfo_pretty=json.dumps(login_session['jwt_payload'], indent=4),users=users)  
@app.route('/logout')
def logout():
    # Clear session stored data
    login_session.clear()
    # Redirect user to logout endpoint
    return redirect('http://localhost:8080/')


@app.route('/choose_city')
@requires_auth
def choose_city():
    return render_template('list.html')




@app.route('/user_city',methods=['GET', 'POST'])
@requires_auth
def user_city():
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    getuserinfo=login_session['profile']

    if request.method == 'POST':
        edituser = session.query(User).filter_by(id=getuserinfo['user_id']).first()
        edituser.country=request.form['country']
        edituser.city=request.form['state']
        session.add(edituser)
        session.commit()
        return redirect(url_for('become_guide'))
    else:
        return redirect(url_for('/'))     
@app.route('/become_guide',methods=['GET','POST'])
@requires_auth
def become_guide():
    if request.method == 'GET':
        return render_template('become_guide.html',userinfo=login_session['profile'])
    if request.method == 'POST':
        engine = create_engine('sqlite:///site.db')
        Base.metadata.bind = engine

        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        getuserinfo=login_session['profile']
        edituser = session.query(User).filter_by(id=getuserinfo['user_id']).first()
        edituser.user_type="guide"
        session.add(edituser)
        session.commit()
        return redirect(url_for('guide_list'))

@app.route('/guide_list')
@requires_auth
def guide_list():
	
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    allguide = session.query(User).filter_by(user_type="guide").all()
    if 'profile' not in login_session:
        return render_template('guide_list.html',allguide=allguide,userinfo=None)
    else:    
        return render_template('guide_list.html',allguide=allguide,userinfo=login_session['profile'])

@app.route('/chat_rooms')
@requires_auth
def chat_rooms():
    engine = create_engine('sqlite:///site.db')
    Base.metadata.bind = engine
   
    DBSession = sessionmaker(bind=engine)
    session = DBSession()    
    userinfo=login_session['profile']
    allrooms = session.query(msg_history).filter(msg_history.room.like('%'+userinfo["user_id"]+'%')).all()
    specific_rooms=[]
    room_from=[]
    for i in allrooms:
        if i.room not in specific_rooms:
            specific_rooms.append(i.room)
            allguide = session.query(User).filter_by(id=i.msg_from).first()
            room_from.append(allguide.name)
    compined_data=list(zip(specific_rooms, room_from))        
    return render_template('chat_rooms.html',allrooms=specific_rooms,compined_data=compined_data,userinfo=userinfo)

if __name__ == '__main__':
    socketio.run(app,debug=True,host='0.0.0.0', port=8080)