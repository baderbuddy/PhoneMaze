from os import posix_fadvise
from flask import (
    flash,
    render_template,
    redirect,
    request,
    session,
    url_for,
    Response,
    Flask,
)
from twilio.twiml.voice_response import VoiceResponse
import random

app = Flask(__name__)


class Maze:
    def __init__(self):
        self.north = None
        self.east = None
        self.west = None
        self.south = None
        self.final = False

    def __str__(self):
        return str(self.index) + " " + str(self.final)

    def __repr__(self):
        return self.__str__()


maze = []
mazeSize = 80


def generateMaze():
    global maze
    maze = []
    for x in range(mazeSize):
        maze.append(Maze())
        maze[x].index = x
    maze[-1].final = True
    for m in maze:
        if m.north == None:
            if random.randrange(100) > 70:
                c = random.choice(maze)
                if c.south == None:
                    c.south = m
                    m.north = c
        if m.south == None:
            if random.randrange(100) > 70:
                c = random.choice(maze)
                if c.north == None:
                    c.north = m
                    m.south = c
        if m.west == None:
            if random.randrange(100) > 70:
                c = random.choice(maze)
                if c.east == None:
                    c.east = m
                    m.west = c
        if m.east == None:
            if random.randrange(100) > 70:
                c = random.choice(maze)
                if c.west == None:
                    c.west = m
                    m.east = c


tried = []


def testMaze(index, path):
    tried[index] = True
   
    if maze[index].final:
        print(path)
        return True
    values = [
        maze[index].north,
        maze[index].east,
        maze[index].south,
        maze[index].west
    ]
    for i, val in enumerate(values):
        p = path.copy()
        p.append(str(index) + " " + str(i))
        if val != None:
            if not tried[val.index]:
                if testMaze(val.index, p):
                    return True
    return False


def start():
    global tried
    generateMaze()
    tried = [False for i in range(len(maze))]
    return testMaze(0, [])


while not start():
    pass

@app.route("/", methods=['GET'])
def default():
  return Response("Hello")

@app.route('/maze/go', methods=['POST'])
def start():
    return menu(0)


@app.route('/maze/go/<r>', methods=['POST'])
def menu(r):
    room = int(r)
    response = VoiceResponse()
    selectedOption = getDirection(request)
   
    currentRoom = maze[room]
    rooms = {
        2: currentRoom.north,
        6: currentRoom.east,
        8: currentRoom.south,
        4: currentRoom.west,
        -1: currentRoom
    }
    currentRoom = rooms[selectedOption]
    if currentRoom == None:
      currentRoom = maze[room]
    print("In room " + str(room) + " going to " + str(selectedOption) + " ended up in room " + str(currentRoom.index))
   
    if currentRoom.index == room and room != 0:
        _hit_head(response)
    return _give_instructions(response, currentRoom)


# private methods
def getDirection(request):
    resultMap = {"north": 2, "east": 6, "south": 8, "west": 4}
    if 'SpeechResult' in request.form.keys():
        key = request.form['SpeechResult'].lower()
        print(key)
        for realKey in resultMap.keys():
          if realKey in key:
            return resultMap[realKey]
            
        return -1
    if 'Digits' in request.form.keys():
        key = int(request.form['Digits'])
        if key % 2 != 0 or key > 8 or key == 0:
            key = -1
        return key
    
    return -1


def twiml(resp):
    resp = Response(str(resp))
    resp.headers['Content-Type'] = 'text/xml'
    return resp


def _hit_head(response):
    response.say("You have run straight into a wall, try again.")


def _initial_instructions(response):
    response.say(
        "You are at the entrance of a maze. You can navigate with your keypad or with your voice. Choose wisely."
    )


def _final_instructions(response):
    response.say("You have made it to the end of the maze, congratulations!")
    response.hangup()


def _add_directions(response, currentRoom):
    with response.gather(num_digits=1,
                         action='/maze/go/' + str(currentRoom.index),
                         method="POST",
                         input="dtmf speech") as g:
        g.say(message=_get_room_string(currentRoom))


def _get_room_string(currentRoom):
    description = "You are in a room. "
    debug = "Room: " + str(currentRoom.index)
    if currentRoom.north != None:
        description += "There is a room to the north. "
        debug += " North: " + str(currentRoom.north.index)
    if currentRoom.east != None:
        description += "There is a room to the east. "
        debug += " east: " + str(currentRoom.east.index)
    if currentRoom.south != None:
        description += "There is a room to the south. "
        debug += " south: " + str(currentRoom.south.index)
    if currentRoom.west != None:
        description += "There is a room to the west. "
        debug += " west: " + str(currentRoom.west.index)
    print(debug)
    return description


def _give_instructions(response, currentRoom):
    if currentRoom.index == 0:
        _initial_instructions(response)
    if currentRoom.final:
        _final_instructions(response)
    else:
        _add_directions(response, currentRoom)

    return twiml(response)


app.run(host="0.0.0.0", port=80)
