from os import posix_fadvise
from flask import (
    flash,
    render_template,
    redirect,
    request,
    session,
    url_for,
    Response,
)
from twilio.twiml.voice_response import VoiceResponse
import random
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
    p = path.copy()
    p.append(index)
    if maze[index].final:
        print(p)
        return True
    values = [maze[index].east, maze[index].west, maze[index].north, maze[index].south]
    for val in values:
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
    

@app.route('/ivr/welcome', methods=['POST'])
def start():
    return menu(0)


@app.route('/maze/go/<room>', methods=['POST'])
def menu(room):
    response = VoiceResponse()
    selectedOption = getDirection(request)
    currentRoom = maze[room]
    rooms = {1: currentRoom.north, 2: currentRoom.east, 3: currentRoom.south, 4: currentRoom.west, -1: currentRoom}
    currentRoom = rooms[selectedOption]
    if currentRoom.index == room and room != 0:
        _hit_head(response)
    return _give_instructions(response, currentRoom)

# private methods
def getDirection(request):
    resultMap = {"north": 8, "east": 6, "south": 2, "west": 4}
    if 'Digits' in request.form.keys():
        key = request.form['Digits']
        if key % 2 != 0 or key > 8 or key == 0:
            key = -1
        return key
    if 'SpeechResult' in request.form.keys():
        key = request.form['SpeechResult']
        if key not in resultMap.keys():
            return -1
        return resultMap[key]
    return -1

def twiml(resp):
    resp = Response(str(resp))
    resp.headers['Content-Type'] = 'text/xml'
    return resp

def _hit_head(response):
    response.say("You have run straight into a wall, try again.")

def _initial_instructions(response):
    response.say("You are at the entrance of a maze. You can navigate with your keypad or with your voice. Choose wisely.")

def _final_instructions(response):
    response.say("You have made it to the end of the maze, congratulations!")
    response.hangup()

def _add_directions(response, currentRoom):
    with response.gather(
        num_digits=1, action='/maze/go/' + str(currentRoom.index), method="POST", input="dtmf speech"
    ) as g:
        g.say(message=_get_room_string(currentRoom))

def _get_room_string(currentRoom):
    description = "You are in a room. "
    if currentRoom.north != None:
        description += "There is a room to the north. "
    if currentRoom.east != None:
        description += "There is a room to the east. "
    if currentRoom.south != None:
        description += "There is a room to the south. "
    if currentRoom.west != None:
        description += "There is a room to the west. "
    return description

def _give_instructions(response, currentRoom):
    if currentRoom.index == 0:
        _initial_instructions(response)
    if currentRoom.final:
        _final_instructions(response)
    else:
        _add_directions(response, currentRoom)
    
    return twiml(response)
