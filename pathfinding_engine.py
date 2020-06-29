import rdflib
import warnings
from collections import defaultdict
import requests


class PathfindingEngine:
    """
    Pathfinding Engine that finds pathways in graphs and calculates their implications/costs.
    Parameters
    ----------
    graphFileName : str
        Filename of the graph file to be parsed.

    format : str
        Format of triples given by the graph file (xml,turtle,rdfa,grddl).

    Attributes
    ----------
    graph : rdflib.Graph
        Graph containing triples with rdflib methods.
    namespaces : dict
        Index containing the short form prefixes of URI namespaces.
        Format is {URI : prefix}.
    Methods
    -------
    query(query)
        Takes in a SPARQL query string and returns a iterator object of results.
    getShortURI(URIRef)
        Converts a URIRef object to its short form string representation.
    queryAdjacent(resource, predicate='bot:adjacentElement', reverse = False)
        Returns an iterator object of all adjacent elements to the rightmost
        (reverse = True) or leftmost operator (reverse = False).
    peek(iterable)
        Look and see if there are any results in a SPARQL Query object.
    queryResources(resources)
        Returns a dictionary of resources associated with the leftmost operator.
    queryDFSSingle(start, path='', predicate=None, reverse=False, visited = None)
        Returns all accessible nodes and their pathways that reached them.
    queryDFSMulti(start, end, path='', predicate=None, reverse=False)
        Returns all paths between two nodes.
    cost(location)
        Returns the cost of a single location.
    """

    def __init__(self, graphFileName=None, format='turtle'):
        # load the graph
        self.graph = rdflib.Graph()
        self.namespaces = {}
        if graphFileName is not None:
            self.graph.load(graphFileName, format=format)
            for value, key in self.graph.namespaces():
                if key[-1] != '#':
                    warnings.warn("{} does not end with a #, searching functionality may be affected".format(key))
                self.namespaces[str(key)] = value

    ####Edited
    def query(self, query):

        # api-endpoint
        URL = "http://localhost:47808/api/query"

        # sending get request and saving the response as response object
        r = requests.get(url=URL, data=query)
        if r:
            # extracting data in json format
            data = r.json()
            #print(data['Rows'])
            #return self.graph.query(query)
            return data['Rows']
        return

    def getShortURI(self, URIRef) -> str:
        # take URIRef object and return its abbreviated format for sparql
        #if str(URIRef).split("#")[0] + "#" in self.namespaces.keys():
        #    return self.namespaces[str(URIRef).split("#")[0] + "#"] + ":" + str(URIRef).split("#")[1]
        return "building1:"+URIRef

    def queryAdjacent(self, resource, predicate='bot:adjacentElement', reverse=False):
        if "building1" not in str(resource):
            resource="building1:"+resource
        if reverse:
            qres = "SELECT ?resource WHERE {?resource %s %s};" % (predicate, resource)
            #SELECT ?resource WHERE {?resource bot:adjacentElement building1:Door-Single-Flush-339570};
        else:
            qres = "SELECT ?resource WHERE {%s %s ?resource};" % (resource, predicate)

        result=self.query(qres)
        if result:
            resList=[]
            #print(resource)
            for res in result:
                resList.append(res["?resource"]["Value"])
            #print("---> ",resList)
            return resList
        return

    def peek(self, iterable):
        if iterable:
            if iterable.__len__() == 0:
                return None
            return iterable
        else:
            return
    ###????
    def queryResources(self, resources) -> dict:
        # only gets points in the roooms currently
        implications = dict()
        for r in list(resources):
            if r not in implications.keys():
                implications[r] = [self.getShortURI(x) \
                                   for x in self.graph.objects( \
                        subject=rdflib.URIRef('http://building1.com#' + r.split(':')[-1]), \
                        predicate=rdflib.URIRef('https://brickschema.org/schema/1.0.1/BrickFrame#controls') \
                        )]
        return implications

    # todo: might remove
    def getSensorTypes(self) -> list:
        a = self.query("""select ?mid where {  
            			?mid rdfs:subClassOf* brick:Sensor .
                                                   }
                """)
        for x in a:
            for b in x:
                print(b)
        types = [self.getShortURI(x) \
                 for x in self.graph.query("""
			select ?mid where { 
            			?mid rdfs:subClassOf* brick:Sensor .
            		}""")
                 ]
        return list(set(types))
    ###Edited
    def getRooms(self) -> list:
        '''
        rooms = [self.getShortURI(x[0]) \
                 for x in self.graph.query("""
                        select ?room where { 
                                ?room a/rdfs:type* brick:Room .
                        }""")
                 ]
        '''
        rooms="SELECT ?room WHERE {?room rdf:type brick:Room};"
        res=self.query(rooms)
        return res

    def getPoints(self, room) -> list:
        '''points = [self.getShortURI(x[0]) \
                  for x in self.graph.query("""
                    select ?point where { 
                        %s bf:isLocationOf ?point .
                    }""" % (room))]
        '''
        points="SELECT ?point WHERE {"+room+" bf:hasPoint ?point};"     #building1:Room-1-1-188
        res=self.query(points)
        #return list(set(points))
        return res

    def queryDFSSingle(self, start, path='', predicate=None, reverse=False, visited=None) -> list:
        # resource (start, end) format = building1:Room-1
        if not isinstance(start, str):
            start = self.getShortURI(start)

        if path == '':
            path = start
        else:
            path = path + " --> " + start

        if visited is None:
            visited = set()
        visited.add(start)

        paths = []

        adjacentElements = self.peek(self.queryAdjacent(start, reverse=reverse))
        if adjacentElements is None:
            return [path], visited

        # find the furthest room to desired room
        for resource in adjacentElements:
            resource = self.getShortURI(resource[0])

            if resource in visited:
                paths.append(path)
                continue

            # 2 cases: adjacent room or door
            if "Door" in resource and resource not in path:
                newpaths, visited = self.queryDFSSingle(resource, path=path, reverse=True, visited=visited)
                paths = paths + newpaths

            elif resource not in path:
                newpaths, visited = self.queryDFSSingle(resource, path=path, visited=visited)
                paths = paths + newpaths

        paths = list(set(paths))
        paths.sort()

        return paths, visited

    def queryDFSMulti(self, start, end, path='', predicate=None, reverse=False) -> list:
        # resource (start, end) format = building1:Room-1

        #if not isinstance(start, str):
        #    start = self.getShortURI(start)
        if ':' not in end:
            end="building1:"+end
        if ":" not in start:
            start="building1:"+start

        if path == '':
            path = start
        else:
            path = path + " + " + start

        if start == end:
            print("---------------------------")
            return [path]

        paths = []

        adjacentElements = self.peek(self.queryAdjacent(start, reverse=reverse))

        #print(adjacentElements)
        if adjacentElements is None:
            return [path]

        # find the furthest room to desired room
        for resource in adjacentElements:
            #resource = self.getShortURI(resource[0])

            # 2 cases: adjacent room or door
            if "Door" in resource and resource not in path:
                newpaths = self.queryDFSMulti(start=resource, end=end, path=path, reverse=True)
                paths = paths + newpaths

            elif resource not in path:
                newpaths = self.queryDFSMulti(start=resource, end=end, path=path)
                paths = paths + newpaths
            else:
                if resource == end or resource == start:
                    paths = paths+[resource]


        paths = list(set(paths))
        #print(path)
        #paths.sort()

        return paths

    def cost1(self, room) -> float:
        total_cost = 0

        try:
            points = defaultdict(list)
            for x in self.graph.query("""
                    select ?point ?location where { 
                        %s bf:isLocationOf ?point .
                        ?point bf:controls ?command .
                        ?equipment bf:hasPoint ?command .
                        ?equipment bf:feeds ?zone .
                        ?zone bf:hasPart ?location .
                    }""" % (room)):
                points[self.getShortURI(x[0])].append(x[1])

            zones_cost = {'building1:Public-Zone': 0, 'building1:Reception-Zone': 1, 'building1:Operations-Zone': 2,
                          'building1:Security-Zone': 3, 'building1:High-Security-Zone': 4}
            sensitivity = None
            for x in self.graph.query("""
                    select ?zone where {
                        ?zone a bot:Zone .
                        ?zone bot:hasSpace %s .
                    }""" % (room)):
                zone = self.getShortURI(x[0])
                if zone in list(zones_cost.keys()):
                    sensitivity = zones_cost[zone]

            # todo: allow for user to set weights thorugh AHP
            weights = {'brick:Room_Temperature_Sensor': 0.318, 'brick:Damper_Position_Sensor': 0.232,
                       'brick:Occupancy_Sensor': 0.304, 'brick:Humidity_Sensor': 0.145, \
                       'brick:Room_Temperature_Setpoint': 0.460, 'brick:Humidity_Setpoint': 0.221,
                       'brick:Air_Flow_Setpoint': 0.319}

            points_cost = 0
            for x, y in points.items():
                point_type = [z for z in self.graph.query('select ?type where { %s a ?type . }' % (x))]
                point_type_class = self.getShortURI(point_type[0][0])
                if point_type_class in list(weights.keys()):
                    points_cost += weights[point_type_class] * (1 + len(y))

            total_cost = sensitivity + points_cost

        except:
            pass

        return total_cost

    #{"Rows":[{"?location":{"Namespace":"http://building1.com","Value":"Room-1-1-155"},"?point":{"Namespace":"http://building1.com","Value":"PCL1_VAV_119_RT_SP_TL"}},
    # {"?location":{"Namespace":"http://building1.com","Value":"Room-1-1-154"},"?point":{"Namespace":"http://building1.com","Value":"PCL1_VAV_119_RT_SP_TL"}}],"Count":2,"Elapsed":0,"Errors":null}
    def cost(self, room) -> float:
        total_cost = 0

        #try:
        points = defaultdict(list)
        pointsInfo=self.query("SELECT ?point ?location WHERE {%s bf:isLocationOf ?point . ?point bf:controls ?sensor . ?vav bf:hasPoint ?sensor . ?vav bf:feeds ?zone . ?zone bf:hasPart ?location .};" % (room))
        if pointsInfo!=None:
            for x in pointsInfo:
                #print(x["?point"]["Value"])
                points[x["?point"]["Value"]].append(x["?location"]["Value"])

        zones_cost = {'building1:Public-Zone': 0, 'building1:Reception-Zone': 1, 'building1:Operations-Zone': 2,
                      'building1:Security-Zone': 3, 'building1:High-Security-Zone': 4}
        sensitivity = 0
        zoneInfo=self.query("SELECT ?zone WHERE {?zone a bot:Zone . ?zone bot:hasSpace %s .};" % (room))
        if zoneInfo != None:
            for x in zoneInfo:
                zone = self.getShortURI(x[0])
                if zone in list(zones_cost.keys()):
                    sensitivity = zones_cost[zone]

        # todo: allow for user to set weights thorugh AHP
        weights = {'brick:Room_Temperature_Sensor': 0.318, 'brick:Damper_Position_Sensor': 0.232,
                   'brick:Occupancy_Sensor': 0.304, 'brick:Humidity_Sensor': 0.145, \
                   'brick:Room_Temperature_Setpoint': 0.460, 'brick:Humidity_Setpoint': 0.221,
                   'brick:Air_Flow_Setpoint': 0.319}

        points_cost = 0
        for x, y in points.items():
            point_type = [z["?type"]["Value"] for z in self.query('SELECT ?type WHERE { building1:%s rdf:type ?type . };' % (x))]
            print(point_type)
            point_type_class = "brick:"+point_type[0]
            print((point_type_class))
            if point_type_class in list(weights.keys()):
                points_cost += weights[point_type_class] * (1 + len(y))

        total_cost = sensitivity + points_cost

        #except Exception as e:
        #    print(e)

        return total_cost

if __name__ == '__main__':
    p=PathfindingEngine('Building1_Floor1.ttl')
    #print(p.getRooms())
    #print(p.queryDFSMulti(start="building1:Room-1-1-120",end="building1:Room-1-1-121"))
    print(p.cost("building1:Room-1-1-114"))