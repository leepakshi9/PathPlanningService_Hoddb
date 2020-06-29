from flask import request
from flask_api import FlaskAPI
import pathfinding_engine
from privacy_metric_cost import CostFinder
import math

app = FlaskAPI(__name__)

building = pathfinding_engine.PathfindingEngine("Building1_Floor1.ttl")
building.graph.parse("Brick.ttl", format="turtle")
building.graph.parse("BrickFrame.ttl", format="turtle")

@app.route('/namespaces/')
def namespaces():
    return building.namespaces

@app.route('/rooms/')
def allrooms():
    return building.getRooms()

@app.route('/resources/', methods=['GET', 'POST'])
def resources():
        if request.method == 'POST':
            room = str(request.data.get('room', ''))
            print(building.getPoints(room))
        try:
            return building.getPoints(room)
        except:
            return {"error": "Invalid room"}

        #return {"error": "Invalid room"}

# endpoint with all rooms and resources
@app.route('/allresources/')
def allresources():
    #return [{x: building.getPoints(x)} for x in building.getRooms()]
    rooms=building.getRooms()
    roomList=[]
    for r in rooms:
        roomList.append(r['?room']['Value'])
    return [{x: building.getPoints('building1:'+x)} for x in roomList]


def getCost1(path):
    path = path.split(' --> ')
    path_cost = 0
    for location in path:
        path_cost += building.cost(location)
    return path_cost

def getCost(path):
    pathCost = 0
    for room in path.split("+"):
        z = building.query('SELECT ?type WHERE { %s rdf:type ?type . };' % (room.strip()))
        type = z[0]["?type"]["Value"]
        print(type)
        if type == 'Room':
            print(room)
            print("-->2")
            pathCost = pathCost + building.cost(room.strip())
            pathCost=round(pathCost,2)
            print(pathCost)
    return pathCost

@app.route("/routes/", methods=['GET', 'POST'])
def routes():
    if request.method == 'POST':
        start = str(request.data.get('start', ''))
        end = str(request.data.get('end', ''))
        print(request.data, start, end)
        try:
            # return the cost of each path
            # todo: incorporate cost function into queryDFSMulti
            answer=[]
            result= building.queryDFSMulti(start,end) #[x, getCost(x)]
            for res in result:
                if end in res and start in res:
                    answer.append(res)
            for i in range(len(answer)):
                for j in range(1,len(answer)):
                    if len(answer[i])>len(answer[j]):
                        temp=answer[i]
                        answer[i]=answer[j]
                        answer[j]=temp
            print("-->")
            print(answer)

            #return {"paths":[x for x in answer]}
            return {"paths": [[x, getCost(x)] for x in answer]}
        except:
            return {"error": "Invalid start or end location"}

    return {"error": "Invalid start or end location"}

# todo: add questions endpoint for setting weights with AHP; save a set of default weights

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5050, debug=True)