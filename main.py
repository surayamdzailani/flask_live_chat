from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random #use to generate random group code 
from string import ascii_uppercase #all variable character we can choose from generating group code 

#flask setup 

app = Flask(__name__)
app.config["SECRET_KEY"] = "abcd"
socketio = SocketIO(app)

rooms = {} #will store all the room info we have generate 
#function to generate our room code
def generate_unique_code(Length):
    while True:
        code = ""
        for _ in range (Length):#to generate code until it reach the length using random that will pick random ascii charc
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break
    return code


@app.route("/", methods=["POST", "GET"]) #post means post data to this route #get data  
def home():
    session.clear() #Seassion will be clear when user go the the homepage
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False) #if join dosent exist we will get false same with create
        create = request.form.get('create', False)

        if not name: 
             return render_template("home.html", error="Please Enter Name!", code=code, name=name) #if statement for the cases if user didnt enter any name
        
        if join != False and not code: #if user didnt enter a code room 
            return render_template("home.html", error="Please Enter Code Room!", code=code, name=name) 
        
        room = code 
        if create != False:
            room = generate_unique_code(6) #4 is going to be the length of our room code generated
            rooms[room] = {'members':0, 'message':[]}
        elif code not in rooms:
            return render_template("home.html", error=" Room doesnt not exist!", code=code, name=name) 
        
        #create temporary data using session that will temporary store all information about user because in this project we didnt do the sign in authentication form into our server
        session["room"] = room
        session["name"] =  name
        return redirect(url_for("room"))
    
    return render_template("home.html")

#create another route which will be our room root to start conversation
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages = rooms[room]['message'])

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room and not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name":name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f'{name} joined room {room}')

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name":name, "message": "has left the room"}, to=room)
    print(f'{name} left chatroom {room}')

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    rooms[room]["message"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


        


if __name__ == "__main__":
    socketio.run(app, debug=True)