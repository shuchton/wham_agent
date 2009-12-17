# CS3310 Lab 4
#
# allYourBaseAreBelongToUs.py
#
# Scott Huchton
# Will Taff

import sys
import time
import socket
from copy import deepcopy
from heapq import heappush, heappop
from math import fabs

# Set the buffer size
BUFSZ = 4096 # (4kB)

# VERBOSE output
VERBOSE = True

# Define a room for the station
class Room:
    def __init__(self, name, coordinates, exits, weapon = None):
        self.name = name
        self.coordinates = coordinates
        self.exits = exits
        self.weapon = weapon

# Define the station and its geometry
class Station:
    def __init__(self):

        # Define the rooms of the Wham in a dictionary
        self.roomList = {"Aft Engine Access Gangway": Room("Aft Engine Access Gangway", (0, -3), [("aft", "Engine Room"), ("forward", "Forward Engine Access Gangway")]),
        "Aft Spoke": Room("Aft Spoke", (0, -1), [("aft", "Forward Engine Access Gangway"), ("forward", "Dock"), ("port", "Hub D"), ("starboard", "Hub C")]),
        "Biology Lab": Room("Biology Lab", (1, 1), [("starboard", "Starboard Spoke")], 'h'),
        "Captain's Quarters": Room("Captain's Quarters", (0, 2), [("forward", "Forward Spoke")], 'p'),
        "Command Center": Room("Command Center", (0, 4), [("aft", "Forward Spoke")], "g"),
        "Crew Quarters": Room("Crew Quarters", (-1, 1), [("port", "Port Spoke")]),
        "Dock": Room("Dock", (0, 0), [("aft", "Aft Spoke")]),
        "Engine Room": Room("Engine Room", (0, -4), [("forward", "Aft Engine Access Gangway")], 'e'),
        "Forward Engine Access Gangway": Room("Forward Engine Access Gangway", (0, -2), [("aft", "Aft Engine Access Gangway"), ("forward", "Aft Spoke")]),
        "Forward Spoke": Room("Forward Spoke", (0, 3), [("aft", "Captain's Quarters"), ("forward", "Command Center"), ("port", "Hub A"), ("starboard", "Hub B")], 'f'),
        "Galley": Room("Galley", (-3, 0), [("forward", "Mess")], 'c'),
        "Hub A": Room("Hub A", (-2, 3), [("aft", "Port Spoke"),("starboard", "Forward Spoke")]),
        "Hub B": Room("Hub B", (2, 3), [("aft", "Starboard Spoke"), ("port", "Forward Spoke")]),
        "Hub C": Room("Hub C", (2, -1), [("forward", "Starboard Spoke"), ("port", "Aft Spoke")]),
        "Hub D": Room("Hub D", (-2, -1), [("forward", "Port Spoke"), ("starboard", "Aft Spoke")]),
        "Mess": Room("Mess", (-3, 1), [("aft", "Galley"), ("starboard", "Port Spoke")], 'b'),
        "Physics Lab": Room("Physics Lab", (3, 1), [("forward", "Workshop"), ("port", "Starboard Spoke")], 'l'),
        "Port Spoke": Room("Port Spoke", (-2, 1), [("aft", "Hub D"), ("forward", "Hub A"), ("port", "Mess"), ("starboard", "Crew Quarters")]),
        "Starboard Spoke": Room("Starboard Spoke", (2, 1), [("aft", "Hub C"), ("forward", "Hub B"), ("port", "Biology Lab"), ("starboard", "Physics Lab")]),
        "Workshop": Room("Workshop", (3, 2), [("aft", "Physics Lab")], "b")}

    # Return the Manhatten distance between the two points.
    def findDistance(self, startLoc, endLoc):
        start = self.roomList[startLoc].coordinates
        end = self.roomList[endLoc].coordinates

        return int(fabs(start[0]-end[0]) + fabs(start[1]-end[1]))

    # Method to ensure that the room name exists in the Station
    def checkRoomName(self, roomName):
        try:
            self.roomList[roomName]
            return True
        except KeyError:
            return False

    def getPath(self, startLoc, endLoc):
        pQueue = []
        print pQueue
        # Initialize the Queue
        startRoom = self.roomList[startLoc]
        startNode = SearchNode(startRoom, [], None, 0, self.findDistance(startLoc, endLoc))
        heappush(pQueue, (startNode.priority, startNode))

        # Set goal flag to false
        goal = False

        # the ancestor list of the goal node is the path
        goalNode = None

        while not(goal) and pQueue:
            node = heappop(pQueue)[1]
            # Debug code
            #Goal Test
            if (node.room.name == endLoc):
                goal = True
                goalNode = node
            else:
                # Goal not found, so run successor function
                successors = node.successor()
                # Check exits for ancestor list of the current node
                # if not there, push to priority queue
                for exit in successors:
                    action = exit[0]
                    roomName = exit[1]
                    # Ancestor check
                    found = False
                    if not(node.ancestorList == []):
                        #ancestorList = node.getAncestorList()
                        for ancestor in node.ancestorList:
                            if ancestor.room.name == roomName:
                                found = True
                    # Passed ancestor check, so add to pQueue
                    if not(found):
                        # Create a node with the new Room
                        newRoom = self.roomList[roomName]
                        newAncestorList = deepcopy(node.ancestorList)
                        newAncestorList.append(node)
                        cost = node.cost + self.findDistance(node.room.name, roomName)
                        estimate = self.findDistance(roomName, endLoc)
                        newNode = SearchNode(newRoom, newAncestorList, action, cost, estimate)
                        #Add to pQueue
                        heappush(pQueue, (newNode.priority, newNode))

        # The ancestor list of the goal node is the best path
        pathNodes = goalNode.ancestorList
        #Add the goal node
        pathNodes.append(goalNode)
        #Delete the start node (room currently in)
        del(pathNodes[0])

        path = []
        for node in pathNodes:
            path.append(node.action)

        return path

# End Station Class

# Define the searchnode used by the A* search
class SearchNode:
    def __init__(self, room, ancestorList, action, cost, estimate):
        self.room = room
        self.ancestorList = ancestorList
        self.action = action
        self.cost = cost
        self.estimate = estimate
        self.priority = cost + estimate

    def successor(self):
        return self.room.exits
# End SearchNode

class MUD:
    def __init__(self, station, agent):
        # initialize the MUD here
        self.station = station
        self.agent = agent
        self.host = sys.argv[1]
        self.port = int(sys.argv[2])
        self.delay = int(sys.argv[5])
        self.logfilename = sys.argv[6]
        self.currentLocation = "Dock"

    def printToLogFile(self, filename, record):
        if filename != "none":
            fin = open(filename, "a")
            fin.write(record)
            fin.close()

    def send(self, str):
        self.printToLogFile(self.logfilename, "Send: " + time.asctime() + "\n" + str + "\n")
        sys.stdout.flush()
        sock.send(str)
        time.sleep(self.delay/1000)
        return self.listen()

    def listen(self):
        response = ""
        sock.settimeout(None)
        received = sock.recv(BUFSZ)
        sock.settimeout(0)
        while len(received) > 0:
            response += received
            time.sleep(0.1)
            try:
                received = sock.recv(BUFSZ)
            except socket.error:
                break
        self.printToLogFile(self.logfilename, "Receive: " + time.asctime() + "\n" + response + "\n")
        return response

    # Used to establish the initial position
    def parseCurrentLocation(self, locString):
        if "(" in locString:
            locationEnd = locString.find("(") - 1
            location = locString[0:locationEnd]
        return location.strip()

    def parseDestinationLocation(self, locString):
        if "\"" in locString:
            locationStart = locString.find("\"") + 11
            locationEnd = locString.find("\"", locationStart) + 1
            location = locString[locationStart:locationEnd]
            location = location[:len(location)-1]
        return location.strip()


    def moveTo(self, room):
        path = self.station.getPath(self.agent.currentLocation, room)
        success = True
        for action in path:
            move = mud.send(action + "\n")
            if "energy" in move:
                success = False
            if VERBOSE:
                print move
        if success:
            self.agent.currentLocation = room
        else:
            self.agent.currentLocation = self.parseCurrentLocation(mud.send("look\n"))
        if VERBOSE:
            print self.agent.username + " is in the " + self.agent.currentLocation


class Agent:
    def __init__(self):
        # initialize the MUD here
        self.username = sys.argv[3]
        self.password = sys.argv[4]
        self.currentLocation = "Dock"
        self.patrolRoute = {"Dock": "Aft Spoke",
                            "Aft Spoke": "Hub D",
                            "Hub D": "Port Spoke",
                            "Port Spoke": "Mess",
                            "Mess": "Galley",
                            "Galley": "Crew Quarters",
                            "Crew Quarters": "Hub A",
                            "Hub A": "Forward Spoke",
                            "Forward Spoke": "Command Center",
                            "Command Center": "Captain's Quarters",
                            "Captain's Quarters": "Hub B",
                            "Hub B": "Starboard Spoke",
                            "Starboard Spoke": "Biology Lab",
                            "Biology Lab": "Physics Lab",
                            "Physics Lab": "Workshop",
                            "Workshop": "Hub C",
                            "Hub C": "Engine Room",
                            "Engine Room": "Aft Engine Access Gangway",
                            "Aft Engine Access Gangway": "Forward Engine Access Gangway",
                            "Forward Engine Access Gangway": "Dock"}

    def getNextPatrolRoom(self):
        return self.patrolRoute[self.currentLocation]

# Begin the main program
DEBUG = True


# Error checking of input
if len(sys.argv) != 7:
    print "You must provide 6 command line arguments"
    print "1: host (i.e. localhost)\n2: port\n3: username"
    print "4: password\n5: delay (in ms)\n6: log filename"
    sys.exit(1)

# Set up the environment
wham = Station()
agent = Agent()
mud = MUD(wham, agent)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((mud.host, mud.port))
sock.settimeout(0) # make reads non-blocking
# Connect (or create) to the MUD
response = mud.send("connect " + agent.username + " " + agent.password + "\n")
if "player does not exist" in response:
    response = mud.send("create " + agent.username + " " + agent.password + "\n")

# In case the initial position is not the Dock for some reason
#if "Dock" not in response:
#    agent.currentLocation = mud.parseCurrentLocation(mud.send("look\n"))

# Go to the command center
mud.moveTo("Command Center")
#mud.send("push red button\n")
if DEBUG:
    print agent.currentLocation
    print mud.parseCurrentLocation(mud.send("look\n"))
while True:
    if DEBUG:
        path = wham.getPath(agent.currentLocation, agent.getNextPatrolRoom())
        print path
    mud.moveTo(agent.getNextPatrolRoom())
    print agent.currentLocation