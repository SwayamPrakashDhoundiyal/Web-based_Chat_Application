from flask import Flask, render_template,request,redirect,url_for,session
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
from flask_socketio import SocketIO, join_room, leave_room,emit

#from db import get_username,get_message_data,get_user,get_code,check_code_generated_for,put_code,get_user_code,get_connect_code_list,check_username_email,user_save,put_message_data
from db import*

import random
from string import ascii_lowercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "areybabuji"
SocketiO = SocketIO(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

signup_room = []

def generate_key(length:int,username,user_bool:bool,conn_name="default"):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_lowercase)
        if user_bool and conn_name != "default": 
            code_gen = check_code_generated_for(username,code,conn_name)
            if code_gen == False:
                break
            else:
                return "None"
        elif user_bool and conn_name == "default":
            code_gen = check_code_generated_for(username,code)
            if code_gen == False:
                break
            else:
                continue
        elif user_bool == False:
            if code in signup_room:
                continue
            else:
                break
    return code

@app.route('/',methods=["POST","GET"])
def login():
    boolean = "none"
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = get_user(email)
        
        if user and user.check_password(password):
            login_user(user)
            return render_template('chat.html',username=user.username)
        else:
            boolean = "block"
    
    return render_template('login.html',boolean=boolean)

@app.route('/temp',methods=["POST","GET"])
def temp():
    return render_template('temp.html')

@app.route('/signup',methods=["POST","GET"])
def signup_handle():
    usr_error = "none"
    email_err = "none"
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        bool_dict = check_username_email(username,email)
        if bool_dict['username']:
            usr_error = "block"
        elif bool_dict['email']:
            email_err = "block"
        else:
            personal_code = generate_key(6,username=username,user_bool=True)
            user_save(username,email,password,personal_code)
            return redirect(url_for('login'))            
        
    return render_template("signup.html",usr_error= usr_error,email_err=email_err)

@app.route('/chat')
def chat():
    return render_template('chat.html')

@SocketiO.on('send_message')
def handle_send_message(data):
    app.logger.info("{} has send {} in room {}".format(data['sender'],data['message'],data['connection_code']))
    SocketiO.emit('receive_message',data,room=data['connection_code'])
    put_message_data(data['connection_code'],data['sender'],data['message'],data['time'])
    print(session)

@SocketiO.on('join_personal_room')
def handle_join_personalroom_event(data):
    room_code = get_user_code(data['username'])
    join_room(room_code)
    session["username"] = data['username']
    session["personal_code"] = room_code
    app.logger.info("{} has joined the room {}".format(data['username'],room_code))
    contact_list = get_connect_code_list(data['username'])
    if contact_list != "default":
        data_list = {}
        i=0
        for key in contact_list:
            data_list[i]=key
            i=i+1
        emit('update_contact',data_list, room=room_code)
    else:
        emit('update_contact',None,room=room_code)
    
    #SocketiO.emit('join_room_announcement', data,room=data['room'])    

@SocketiO.on('contact_connection_start')
def handle_connection_multiple(data):
    connection_code = get_code(session['username'],data['connection_name'])
    if connection_code['task']:
        session['connection_code'] = connection_code['code']
        app.logger.info(session['connection_code'])
    else:
        app.logger.info(connection_code['Error'])
                
    #emit('contact_connect',{'connection_name':data['connection_name']},room=session['personal_code'])
    emit('contact_connect',{'connection_name':data['connection_name'],'username':session['username'],'connection_code':session['connection_code']},room=session['personal_code'])

@SocketiO.on('start_msg_history')
def handle_message_history(data):
    message_list = get_message_data(data['connection_code'])
    SocketiO.emit('messagehistory',message_list,room=session['personal_code'])

@SocketiO.on('join_contact')
def handle_join_contactroom():
    join_room(session['connection_code'])

@SocketiO.on('request_userlist')
def search_request(data):
    list_result = get_username(data['entry'],session['personal_code'])
    SocketiO.emit('show_results',list_result,room=session['personal_code'])
    
@SocketiO.on('requeset_To')
def handle_sending_request(data):
    sender_dict = {'username':session['username'],'user_code':session['personal_code']}
    responese = request_store(data['connection_code'],session['personal_code'],session['username'])
    if responese == 'done':
        SocketiO.emit('has_requested',sender_dict,room=data['connection_code'])

@SocketiO.on('retrive_request_data')
def handle_request_data():
    request_data = request_retrieve(session['personal_code'])
    SocketiO.emit('display_request_data',request_data,room=session['personal_code'])

@SocketiO.on('send_acceptance')
def handle_connection_making(data):
    if data['accept']:
        key_code = generate_key(length=5,username=data['from_user'],user_bool=True,conn_name=data['to_user'])
        if key_code != "None":
            put_code(data['from_user'],data['to_user'],key_code)
            put_code(username=data['to_user'],conn_name=data['from_user'],conn_code=key_code)
            request_remove(data['connection_code'],session['personal_code'])
            app.logger.info("The user got the request: {} \n The user that send the request: {} \n The code generated: {}",data['to_user'],data['from_user'],key_code)
        else:
            app.logger.info("Already connected")
            request_remove(data['connection_code'],session['personal_code'])
    else:
        request_remove(data['connection_code'],session['personal_code'])














@SocketiO.on('leave_room')
def handle_disconnection_message(data):
    app.logger.info("{} has left the room")
    SocketiO.emit('user_left',data,room=data['room'])

@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    SocketiO.run(app,debug=True,port=3000)
