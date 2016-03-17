#!/usr/bin/python
import sys
import graphviz as gv
import functools
import numpy
import pylab

globalLabelDict = {}
globalTotalTime = 0
globalUsecPerCount = 0

#graph = functools.partial(gv.Graph, format='pdf')
#digraph = functools.partial(gv.Digraph, format='pdf')

def sanitizeForGraphviz(tag):
    return tag.replace(":", "_")

def getTag(attr, sanitize=True):
    if 'tag' in attr.keys():
        tag = attr['tag']
    else:
        tag = attr['label']

    if sanitize:
        return sanitizeForGraphviz(tag)
    else:
        return tag

class Node:

    def __init__(self, attrDict):
        self.nodes = []
        self.attr  = attrDict
        self.node_attr = {'depth':0, 'frac':-1, 'rank':'descending'}
        
    def setFrac(self, frac):
        self.frac = frac
        
    def setDepth(self, depth):
        for i in range(len(self.nodes)):
            if self.node_attr['rank'] == 'same':
                self.nodes[i].node_attr['depth'] = depth + 1
            else:
                self.nodes[i].node_attr['depth'] = depth + i + 1
            self.nodes[i].setDepth(self.nodes[i].node_attr['depth'])

    def setShape(self, shape):
        for node in self.nodes:
            node.attr['shape'] = shape
            node.setShape(shape)

    def getNodesAtDepth(self, depth, nodeList):
        for node in self.nodes:
            if node.node_attr['depth'] == depth:
                nodeList.append(node)
            nodeList = node.getNodesAtDepth(depth, nodeList)
        return nodeList

    def printNodes(self, depth=0):
        prefix = ''
        for i in range(0,depth):
            prefix = prefix + ' '
        print prefix + self.attr['label'] + '->'

        for node in self.nodes:
            node.printNodes(depth+1)
                    
    def calls(self, nodes):
        if isinstance(nodes, list):
            for node in nodes:
                self.append(node)
        else:
            self.append(nodes)

    def callsStack(self, nodes):
        if isinstance(nodes, list):
            currNode = self
            for node in nodes:
                currNode = currNode.append(node)
        else:
            self.append(nodes)

    #------------------------------------------------------------
    # Main function for adding nodes to an existing node:
    #
    #  arg can be:
    #
    #  Node  -- append a Node object to the list of child nodes
    #  dict  -- append a Node constructed from dict to the list of child nodes
    #  list  -- append a list of Nodes to the list of child nodes
    #  tuple -- append a descending list of child nodes to the list of child nodes
    #------------------------------------------------------------
    
    def append(self, node):
        if isinstance(node, Node):
            self.nodes.append(node)
            return self
        elif isinstance(node, dict):
            n = Node(node)
            self.nodes.append(n)
            return n
        elif isinstance(node, list):
            for n in node:
                currNode = self.append(n)
            return currNode
        elif isinstance(node, tuple):
            currNode = self
            for n in node:
                currNode = currNode.append(n)
            return currNode

    def callsTo(self, node, to):
        for n in self.nodes:
            if getTag(n.attr) == sanitizeForGraphviz(node):
                if isinstance(to, dict):
                    n.append(to)
                elif isinstance(to, list):
                    currNode = n
                    for ito in to:
                        currNode = currNode.append(ito)
            n.callsTo(node, to)

    def callsAfter(self, after, node):
        index = 0
        for n in self.nodes:
            index = index+1
#            print 'Checking ' + n.attr['label'] + ' against ' + after
            if getTag(n.attr) == sanitizeForGraphviz(after):
 #               print 'Inserting ' + after + ' at index ' + str(index)
                self.insert(index, node)
                return
            n.callsAfter(after, node)

    def callsBefore(self, before, node):
        index = 0
        for n in self.nodes:
  #          print '(B) Checking ' + n.attr['label'] + ' against ' + before
            if getTag(n.attr) == sanitizeForGraphviz(before):
   #             print 'Inserting...'
                self.insert(index, node)
                return
                index = index+1
            index = index+1
            n.callsBefore(before, node)

    def insert(self, index, node):
        if isinstance(node, Node):
            self.nodes.insert(index, node)
        elif isinstance(node, dict):
            n = Node(node)
            self.nodes.insert(index, n)
        elif isinstance(node, list):
            topNode = Node(node[0])
            currNode = topNode
            for i in range(1,len(node)):
                currNode = currNode.append(node[i])
            self.nodes.insert(index, topNode)

    #------------------------------------------------------------
    # Connect this node to its children, and its children to theirs
    #------------------------------------------------------------

    def connectNodes(self, graph):

        # Connect this node to all of its children, and its children to theirs
        
        for node in self.nodes:
#            print 'Attempting to connect node ' + getTag(self.attr) + ' to ' + getTag(node.attr)
            graph.edge(getTag(self.attr), getTag(node.attr))
            node.connectNodes(graph)

        # And also connect the child nodes, else graphviz won't enforce ordering

        d = {'color':'invis'}
        for i in range(1, len(self.nodes)):
            graph.edge(getTag(self.nodes[i-1].attr), getTag(self.nodes[i].attr), **d)

    def setAttr(self, nodeName, attr, val):
        if sanitizeForGraphviz(nodeName) == getTag(self.attr):
            self.attr[attr] = val
        for node in self.nodes:
            node.setAttr(nodeName, attr, val)

    def setNodeAttr(self, nodeName, attr, val):
        if sanitizeForGraphviz(nodeName) == getTag(self.attr):
            self.node_attr[attr] = val
        for node in self.nodes:
            node.setNodeAttr(nodeName, attr, val)

    def setLabels(self, profilerActualDict):
        for node in self.nodes:
            node.renderLabel(profilerActualDict)
            node.setLabels(profilerActualDict)

    def constructLabel(self, tag, label, profilerActualDict, color=None):

        if tag in profilerActualDict.keys():
            frac = profilerActualDict[tag]['frac']
        else:
            frac = -1

        if frac >= 0:
            pieGen(frac)

        substr = label.split(':')
        n = len(substr)
        retLabel = '<<TABLE border="0" cellborder="0">'

        if color == None:
            color = 'black'
            
        if n == 1:
            retLabel += '<TR><TD><FONT color="' + color + '">' + substr[0] + '</FONT></TD></TR>'
        else:
            retLabel += '<TR><TD><FONT color="gray">' + substr[0] + '</FONT></TD></TR>'
            for i in range(1,n):
                retLabel += '<TR><TD><FONT color="' + color + '">' + substr[i] + '</FONT></TD></TR>'
                
        if frac >= 0:
            retLabel += '<TR><TD width="30" height="30" fixedsize="true">' + '<IMG SRC="figs/pc_' + str(int(frac)) + '.png" scale="true"/>' + '</TD></TR>'
            retLabel += '<TR><TD><FONT color="gray">' + str(int(profilerActualDict[tag]['corrusec']/(10000))) + ' &mu;s</FONT></TD></TR>'
            
        retLabel += '</TABLE>>'

        return retLabel
    
    def renderLabel(self, profilerActualDict):

        label = self.attr['label']
        label = label.strip(' ')

        tag = getTag(self.attr, False)

        retLabel = self.constructLabel(tag, label, profilerActualDict)

        if 'tag' not in self.attr.keys():
            self.attr['tag'] = self.attr['label']
            
        self.attr['label'] = retLabel

class DiGraph(Node):

    def __init__(self, attrDict={}):
        self.nodes = []
        self.attr = attrDict
        self.dg   = gv.Digraph('root')
        self.node_attr = {'depth':0, 'frac':-1}
        self.edges = []
        self.profilerSelfDict     = {}
        self.profilerBaselineDict = {}
        self.profilerActualDict   = {}
        self.totalTime = 0
        self.usecPerCount = 0
        
    def ingestProfilerOutput(self,
                             clientFileName,     serverFileName,
                             clientBaseFileName, serverBaseFileName,
                             clientCompFileName, profilerBaseFileName):

        compDict = parseProfilerOutput(clientCompFileName, {})

        self.calculateUsecPerCount(profilerBaseFileName)
        self.calculateBaselines(clientBaseFileName, serverBaseFileName)
        self.calculateTimes(clientFileName, serverFileName)

        # First correct the total time for the time spent profiling

        print 'Total (uncorrected) usec = ' + str(self.totalUsec)
        print 'Total count              = ' + str(self.totalCount)
        print 'usec per count           = ' + str(self.usecPerCount)
        

        self.totalUsec -= (self.totalCount * self.usecPerCount)

        print 'Total (corrected) usec   = ' + str(self.totalUsec)
        print 'Comp time (usec)         = ' + str(compDict['firstusec'])
        
        # Next, for each label encountered, subtract off baselines,
        # correct for profiling, and convert to a fraction of total time

        for key in self.profilerActualDict.keys():
            if key in self.profilerBaselineDict.keys():
                if isinstance(self.profilerBaselineDict[key], dict):
                    base  = self.profilerBaselineDict[key]['usec']
                else:
                    base = 0.0

            if isinstance(self.profilerActualDict[key], dict):
                usec  = self.profilerActualDict[key]['usec']
                count = self.profilerActualDict[key]['count']

                self.profilerActualDict[key]['corrusec'] = (usec - base) - (self.usecPerCount * count)
                self.profilerActualDict[key]['frac'] = 100 * self.profilerActualDict[key]['corrusec']/self.totalUsec
                
    def calculateUsecPerCount(self, fileName):
        self.profilerSelfDict = parseProfilerOutput(fileName, self.profilerSelfDict)
        baseUsec   = self.profilerSelfDict['ts_query_profiler_baseline:confirm']['usec']
        baseCounts = self.profilerSelfDict['ts_query_profiler_baseline:confirm']['count']
        self.usecPerCount = float(baseUsec) / float(baseCounts)

    def calculateBaselines(self, clientFileName, serverFileName):
        self.profilerBaselineDict = parseProfilerOutput(clientFileName, self.profilerBaselineDict)
        self.profilerBaselineDict = parseProfilerOutput(serverFileName, self.profilerBaselineDict)

    def calculateTimes(self, clientFileName, serverFileName):

        # Read the client file first.  The total time is the first
        # usec count encountered in the client file

        self.profilerActualDict = parseProfilerOutput(clientFileName, self.profilerActualDict)
        self.totalCount = self.profilerActualDict['totalcount']
        self.totalUsec = self.profilerActualDict['firstusec']

        # Read the server file last.  The total count is the sum of the client and server counts
        
        self.profilerActualDict = parseProfilerOutput(serverFileName, self.profilerActualDict)
        self.totalCount += self.profilerActualDict['totalcount']

    def setAttr(self, nodeName, attr, val):
        for node in self.nodes:
            node.setAttr(nodeName, attr, val)

    def setNodeAttr(self, nodeName, attr, val):
        for node in self.nodes:
            node.setNodeAttr(nodeName, attr, val)
            
    def setShape(self):
        for node in self.nodes:
            node.attr['shape'] = 'ellipse'
            node.setShape('rectangle')
            
    def printNodes(self):
        for node in self.nodes:
            node.printNodes()

    def title(self, title):
        self.dg.graph_attr['label'] = title
        self.dg.graph_attr['labelloc'] = 't'

    def render(self, name):
        self.setDepth()
        self.setShape()
        self.setLabels(self.profilerActualDict)
        self.constructSubgraphs()
        self.connectNodes()
        self.renderEdgeLabels()
        self.connectEdges()
        self.dg.render(name)

    def setDepth(self):
        for node in self.nodes:
            node.setDepth(0)

    def constructSubgraph(self, depth):
        nodeList = self.getNodesAtDepth(depth, [])
        if len(nodeList) > 0:
            sg = gv.Digraph('subgraph_' + str(depth))
            sg.graph_attr['rank'] = 'same'

            for node in nodeList:
#                print 'depth = ' + str(depth) + ' tag = ' + getTag(node.attr) + ' node.depth = ' + str(node.node_attr['depth'])
                sg.node(getTag(node.attr), **node.attr)

            self.dg.subgraph(sg)

            return True
        else:
            return False

    def constructSubgraphs(self):
        cont = True
        depth = 0
        while cont:
            cont = self.constructSubgraph(depth)
            depth = depth + 1

    def connectNodes(self):
        for node in self.nodes:
            node.connectNodes(self.dg)

    def renderEdgeLabels(self):
        for edge in self.edges:
            attr = edge[2]
            tag = attr['label'].strip(' ')
            label = attr['label']

            if 'color' in attr.keys():
                color = attr['color']

            attr['label'] = self.constructLabel(tag, label, self.profilerActualDict, color)
            print 'Constructed edge label for ' + tag 
    def connectEdges(self):
        for edge in self.edges:
            self.dg.edge(sanitizeForGraphviz(edge[0]), sanitizeForGraphviz(edge[1]), **edge[2])

    def edge(self, head, tail, attr={}):
        self.edges.append((head, tail, attr))
        
def parseTest():
    global globalLabelDict
    parseProfilerOutput('client.txt', globalLabelDict)
    parseProfilerOutput('server.txt', globalLabelDict)
    return globalLabelDict

def getLine(label, content):
    for line in content:
        if line.split(' ')[0] == label:
            return line.split(' ')
    return []
    
def parseProfilerOutput(fileName, labelDict):

    with open(fileName) as f:
        content = f.readlines()

    nline = len(content)

    totalcount = getLine('totalcount', content)
    labels = getLine('label', content)
    counts = getLine('count', content)
    usec   = getLine('usec',  content)
    
    if len(labels) != 0:
        for i in range(2, len(labels)):
            label = labels[i].replace("'", "")
            label = label.replace("\n", "")

            labelDict[label] = {}
            labelDict[label]['usec']  = float(usec[i])
            labelDict[label]['count'] = int(counts[i])
    else:
        for i in range(2, len(usec)):
            label = str(i)
            labelDict[label] = {}
            labelDict[label]['usec']  = float(usec[i])
            labelDict[label]['count'] = int(counts[i])

    total = totalcount[1]
    total = total.replace("'", "")
    total = total.replace("\n", "")
    
    labelDict['totalcount'] = int(total)
    labelDict['firstusec']  = float(usec[2])

    return labelDict

def pieGen(frac):
    frac = int(frac)
    colors = ['r', 'w']
    fracs = [frac,100-frac]

    fig,ax = pylab.subplots(figsize=(1,1))
    pie = ax.pie(fracs,colors=colors, shadow=False, startangle=90, counterclock=False)

    fname = 'figs/pc_' + str(int(frac)) + '.png'
    pylab.savefig(fname)
    pylab.close(fig)
    
def labelWpix(frac, label):

    global globalTotalTime
    global globalLabelDict
    global globalUsecPerCount

    label = label.strip(' ')
    if label in globalLabelDict.keys():
        usec  = globalLabelDict[label]['val']
        count = globalLabelDict[label]['count']
        corr = float(count) * float(globalUsecPerCount)

        print 'Count = ' + str(count) + ' usecpercount = ' + str(globalUsecPerCount) + ' corr = ' + str(corr)
        
        val = float(usec) - float(corr)

        print 'USEC = ' + str(float(usec)) + 'count = ' + str(count) + ' usecpercount = ' + str(globalUsecPerCount) + ' CORR = ' + str(corr)

        frac  = 100 * float(val)/globalTotalTime
        
        print 'Found frac = ' + str(frac) + ' for label = ' + label
    else:
        frac = -1
        
    if frac >= 0:
        pieGen(frac)

    substr = label.split(':')
    n = len(substr)
    retLabel = '<<TABLE border="0" cellborder="0">'

    if n == 1:
        retLabel += '<TR><TD>' + substr[0] + '</TD></TR>'
    else:
        retLabel += '<TR><TD><FONT color="gray">' + substr[0] + '</FONT></TD></TR>'
        for i in range(1,n):
            retLabel += '<TR><TD>' + substr[i] + '</TD></TR>'

    if frac >= 0:
        retLabel += '<TR><TD width="30" height="30" fixedsize="true">' + '<IMG SRC="figs/pc_' + str(int(frac)) + '.png" scale="true"/>' + '</TD></TR>'

    retLabel += '</TABLE>>'
    
    return retLabel

def add_nodes(graph, nodes):
    for n in nodes:
        if isinstance(n, tuple):
            print 'Adding node ' + n[0] + str(n[1])
            graph.node(n[0], **n[1])
        else:
            graph.node(n)
    return graph
        
def add_edges(graph, edges):
    for e in edges:
        if isinstance(e[0], tuple):
            graph.edge(*e[0], **e[1])
        else:
            graph.edge(*e)
    return graph

def connect_nodes_to_head(graph, head, nodes):
    n = numpy.shape(nodes)[0];
    for i in range(0,n-1):
        nh = nodes[i]
        nt = nodes[i+1]

        if isinstance(nh, tuple):
            nhname = nh[0]
        else:
            nhname = nh
  
        if isinstance(nt, tuple):
            ntname = nt[0]
        else:
            ntname = nt
              
        if i == 0:
            graph.edge(head, nhname)
            
        graph.edge(nhname, ntname)
        
    return graph

def connect_nodes(graph, nodes):
    n = numpy.shape(nodes)[0];
    for i in range(0,n-1):
        nh = nodes[i]
        nt = nodes[i+1]

        if isinstance(nh, tuple):
            nhname = nh[0]
            hd = nh[1]
        else:
            nhname = nh
            hd = {}

        if isinstance(nt, tuple):
            ntname = nt[0]
            td = nt[1]
        else:
            ntname = nt
            td = {}

        hcolor = 'vis'
        tcolor = 'vis'

        if 'color' in hd:
            hcolor = hd['color']
        if 'color' in td:
            tcolor = td['color']
            
        if hcolor != 'invis' and tcolor != 'invis':
            if i == 0:
                graph.edge(nhname, ntname, '', {'arrowhead':'none'})
            else:
                graph.edge(nhname, ntname)
        
    return graph

def createDigraph(nodelists):

    dg = gv.Digraph('root')
    
    #------------------------------------------------------------
    # Get the maximum list length over all lists
    #------------------------------------------------------------

    mx = 0

    for l in nodelists:
        len = numpy.shape(l)[0]
        if len > mx:
            mx = len

    #------------------------------------------------------------
    # Iterate over all lists, filling in shorter lists with invisible nodes
    #------------------------------------------------------------

    copylist = nodelists
    for l in copylist:
        len = numpy.shape(l)[0]
        if len < mx:
            for i in range(len, mx):
                basename = l[0][0]
                l.append((basename + str(i), {'label':'', 'color':'invis'}))

    # Change all but the first node in each list to a rectangle

    for l in nodelists:
        len = numpy.shape(l)[0]
        for i in range(1,len):
            nd = l[i][1]
            nd['shape'] = 'rectangle'

    #------------------------------------------------------------
    # Now for each tier in each node list, create a
    # subgraph with same rank, to force nodes to lie
    # side-by-side
    #------------------------------------------------------------

    for i in range(0, mx):
        nodes = []
        for l in copylist:
            nd = l[i][1]
            if 'color' not in nd.keys() or nd['color'] != 'invis':
                nodes.append(l[i])

        sg = gv.Digraph('subgraph_' + str(i))
        sg = add_nodes(sg, nodes)
        sg.graph_attr['rank'] = 'same'

        dg.subgraph(sg)

    # Finally, connect all related lists of nodes

    for l in nodelists:
        connect_nodes(dg, l)
        
    return dg

def printStats(totalTime, labelDict, excDict, compTotalTime):
    fracTime = 0
    for key in labelDict.keys():
        if key not in excDict.keys():
            fracTime += labelDict[key]['val']
    print 'Total = ' + str(totalTime) + ' Frac = ' + str(fracTime) + ' Ratio = ' + str(fracTime/totalTime)
    print 'Estimated ' + str(100*(totalTime - compTotalTime)/totalTime) + '% spent profiling'

    start_child = labelDict['5']['val'] + labelDict['riak_kv_index_fsm:module_info']['val']
    print 'start_child(1) = ' + str(labelDict['supervisor:start_child']['val']/totalTime)
    print 'start_child(2) = ' + str(start_child/totalTime)
    
def makePlots(clientFileName, serverFileName, clientBaseFileName, serverBaseFileName, clientCompFileName, profilerBaseFileName):

    global globalLabelDict
    global globalTotalTime
    global globalUsecPerCount

    profLabelDict = {}
    profTotalTime, profLabelDict = parseProfilerOutput(profilerBaseFileName, profLabelDict)

    print 'DICT = ' + str(profLabelDict)
    baseUsec   = profLabelDict['ts_query_profiler_baseline:confirm']['val']
    baseCounts = profLabelDict['ts_query_profiler_baseline:confirm']['count']
    print 'baseUsec = ' + str(baseUsec) + ' baseCounts = ' + str(baseCounts)
    globalUsecPerCount = float(baseUsec) / float(baseCounts)
    print 'ratio = ' + str(globalUsecPerCount)
        
    compLabelDict = {}
    compTotalTime, compLabelDict = parseProfilerOutput(clientCompFileName, compLabelDict)

    baseLabelDict = {}
    globalTotalTime, baseLabelDict = parseProfilerOutput(serverBaseFileName, baseLabelDict)
    globalTotalTime, baseLabelDict = parseProfilerOutput(clientBaseFileName, baseLabelDict)
    
    globalTotalTime, globalLabelDict = parseProfilerOutput(serverFileName, globalLabelDict)
    globalTotalTime, globalLabelDict = parseProfilerOutput(clientFileName, globalLabelDict)

    excDict = {}
    excDict['riak_api_pb_server:connected'] = 1
    excDict['riak_api_pb_server:process_message'] = 1
    excDict['riak_kv_qry_worker:execute_query'] = 1
    excDict['riak_kv_qry:maybe_await_query_results'] = 1
    excDict['riak_core_vnode_worker:handle_cast'] = 1
    excDict['riak_core_coverage_fsm:init'] = 1
    excDict['riak_kv_index_fsm:module_info'] = 1
    excDict['5'] = 1

    print 'TIME = ' + str(globalTotalTime)
    
    printStats(globalTotalTime, globalLabelDict, excDict, compTotalTime)
    
    #------------------------------------------------------------
    # Subtract off baselines
    #------------------------------------------------------------

    for key in baseLabelDict.keys():
        if key in globalLabelDict.keys():
            globalLabelDict[key]['val'] -= baseLabelDict[key]['val']
    
    #------------------------------------------------------------
    # Start of script
    #------------------------------------------------------------
    
    service_color = 'blue'
    fsm_color     = 'red'
    server_color  = 'cyan'
    
    riakc_funs = [
        ('riakc_0',  {'label': 'riakc',       'color': service_color}),
        ('riakc_1',  {'label': labelWpix(0,'riakc:query')}),
        ('riakc_2',  {'label': labelWpix(0,'riakc:server_call')}),
        ('riakc_3',  {'label': labelWpix(0,'gen_server:call')})
    ]
    
    riakpb_funs = [
        ('riakpb_0',  {'label': 'riakc_pb_socket',       'color': server_color}),
        ('riakpb_1',  {'label': labelWpix(0,'riakc_pb_socket:handle_call')}),
        ('riakpb_2',  {'label': labelWpix(0,'riakc_pb_socket:send_request')})]

    riakpb1_funs = [
        ('riakpb1_0',  {'label': '',       'color':'invis'}),
        ('riakpb1_1',  {'label': '',       'color':'invis'}),
        ('riakpb1_2',  {'label': '',       'color':'invis'}),
        ('riakpb1_3',  {'label': labelWpix(0,'riak_pb_codec:encode')})]

    riakpb4_funs = [
        ('riakpb4_0',  {'label': '',       'color':'invis'}),
        ('riakpb4_1',  {'label': '',       'color':'invis'}),
        ('riakpb4_2',  {'label': '',       'color':'invis'}),
        ('riakpb4_3',  {'label': '',       'color':'invis'}),
        ('riakpb4_4',  {'label': labelWpix(0,'gen_tcp:send')})]
    
    riakpb_funs2 = [
        ('riakpb_4',  {'label': '', 'color':'invis'}),
        ('riakpb_5',  {'label': labelWpix(0,'riakc_pb_socket:handle_info')})]

    riakpb3_funs = [
        ('riakpb3_0',  {'label': '', 'color':'invis'}),
        ('riakpb3_1',  {'label': '', 'color':'invis'}),
        ('riakpb3_2',  {'label': labelWpix(0,'riak_pb_codec:decode')})]

    riakpb5_funs = [
        ('riakpb5_0',  {'label': '', 'color':'invis'}),
        ('riakpb5_1',  {'label': '', 'color':'invis'}),
        ('riakpb5_2',  {'label': '', 'color':'invis'}),
        ('riakpb5_3',  {'label': labelWpix(0,'riakc_pb_socket:send_caller')}),
        ('riakpb5_4',  {'label': labelWpix(0,'gen_server:reply')})
    ]
    
    kvp_funs = [
        ('kvpb_0',  {'label': 'riak_api_pb_server',         'color': fsm_color}),
        ('kvpb_1',  {'label': labelWpix(0,'riak_api_pb_server:connected')})]

    kvp4_funs = [
        ('kvpb4_0',  {'label': '',         'color': 'invis'}),
        ('kvpb4_1',  {'label': '',         'color': 'invis'}),
        ('kvpb4_2',  {'label': labelWpix(0,'riak_kv_pb_timeseries:decode')})]

    kvp5_funs = [
        ('kvpb5_0',  {'label': '',         'color': 'invis'}),
        ('kvpb5_1',  {'label': '',         'color': 'invis'}),
        ('kvpb5_2',  {'label': '',         'color': 'invis'}),
        ('kvpb5_3',  {'label': labelWpix(0,'riak_api_pb_server:process_message')})]

    kvp3_funs = [
        ('kvpb3_0',  {'label': '', 'color':'invis'}),
        ('kvpb3_1',  {'label': '', 'color':'invis'}),
        ('kvpb3_2',  {'label': '', 'color':'invis'}),
        ('kvpb3_3',  {'label': '', 'color':'invis'}),
        ('kvpb3_4',  {'label': labelWpix(0,'riak_kv_pb_timeseries:process')}),
        ('kvpb3_5',  {'label': labelWpix(0,'riak_kv_pb_timeseries:check_table_and_call')})]
    
    kvp8_funs = [
        ('kvpb8_0',  {'label': '', 'color':'invis'}),
        ('kvpb8_1',  {'label': '', 'color':'invis'}),
        ('kvpb8_2',  {'label': '', 'color':'invis'}),
        ('kvpb8_3',  {'label': '', 'color':'invis'}),
        ('kvpb8_4',  {'label': '', 'color':'invis'}),
        ('kvpb8_5',  {'label': '', 'color':'invis'}),
        ('kvpb8_6',  {'label': labelWpix(0,'riak_kv_ts_util:get_table_ddl')})]

    kvp7_funs = [
        ('kvpb7_0',  {'label': '', 'color':'invis'}),
        ('kvpb7_1',  {'label': '', 'color':'invis'}),
        ('kvpb7_2',  {'label': '', 'color':'invis'}),
        ('kvpb7_3',  {'label': '', 'color':'invis'}),
        ('kvpb7_4',  {'label': '', 'color':'invis'}),
        ('kvpb7_5',  {'label': '', 'color':'invis'}),
        ('kvpb7_6',  {'label': '', 'color':'invis'}),
        ('kvpb7_7',  {'label': labelWpix(0,'riak_kv_pb_timeseries:sub_tsqueryreq')}),
        ('kvpb7_8',  {'label': labelWpix(0,'riak_kv_qry:submit')})]

    kvp9_funs = [
        ('kvpb9_0',  {'label': '', 'color':'invis'}),
        ('kvpb9_1',  {'label': '', 'color':'invis'}),
        ('kvpb9_2',  {'label': '', 'color':'invis'}),
        ('kvpb9_3',  {'label': '', 'color':'invis'}),
        ('kvpb9_4',  {'label': '', 'color':'invis'}),
        ('kvpb9_5',  {'label': '', 'color':'invis'}),
        ('kvpb9_6',  {'label': '', 'color':'invis'}),
        ('kvpb9_7',  {'label': '', 'color':'invis'}),
        ('kvpb9_8',  {'label': '', 'color':'invis'}),
        ('kvpb9_9',  {'label': labelWpix(0,'riak_ql_lexer:get_tokens')}),
        ('kvpb9_10', {'label': labelWpix(0,'riak_ql_parser:parse')})]

    kvp10_funs = [
        ('kvpb10_0',  {'label': '', 'color':'invis'}),
        ('kvpb10_1',  {'label': '', 'color':'invis'}),
        ('kvpb10_2',  {'label': '', 'color':'invis'}),
        ('kvpb10_3',  {'label': '', 'color':'invis'}),
        ('kvpb10_4',  {'label': '', 'color':'invis'}),
        ('kvpb10_5',  {'label': '', 'color':'invis'}),
        ('kvpb10_6',  {'label': '', 'color':'invis'}),
        ('kvpb10_7',  {'label': '', 'color':'invis'}),
        ('kvpb10_8',  {'label': '', 'color':'invis'}),
        ('kvpb10_9',  {'label': '', 'color':'invis'}),
        ('kvpb10_10', {'label': labelWpix(0,'riak_kv_qry:maybe_submit_to_queue')})]

    kvp1_funs = [
        ('kvpb1_0',   {'label': '', 'color':'invis'}),
        ('kvpb1_1',   {'label': '', 'color':'invis'}),
        ('kvpb1_3',   {'label': '', 'color':'invis'}),
        ('kvpb1_4',   {'label': '', 'color':'invis'}),
        ('kvpb1_5',   {'label': '', 'color':'invis'}),
        ('kvpb1_6',   {'label': labelWpix(0,'riak_api_pb_server:send_encoded_message_or_error')})]
    
    kvp2_funs = [
        ('kvpb2_0',   {'label': '', 'color':'invis'}),
        ('kvpb2_1',   {'label': '', 'color':'invis'}),
        ('kvpb2_2',   {'label': '', 'color':'invis'}),
        ('kvpb2_3',   {'label': '', 'color':'invis'}),
        ('kvpb2_4',   {'label': '', 'color':'invis'}),
        ('kvpb2_5',   {'label': '', 'color':'invis'}),
        ('kvpb2_6',   {'label': '', 'color':'invis'}),
        ('kvpb2_7',   {'label': '', 'color':'invis'}),
        ('kvpb2_8',   {'label': '', 'color':'invis'}),
        ('kvpb2_9',   {'label': '', 'color':'invis'}),
        ('kvpb2_10',  {'label': '', 'color':'invis'}),
        ('kvpb2_11',  {'label': labelWpix(0,'riak_kv_qry_queue:put_on_queue')}),
        ('kvpb2_12',  {'label': labelWpix(0,'gen_server:call')})]

    kvp6_funs = [
        ('kvpb6_0',   {'label': '', 'color':'invis'}),
        ('kvpb6_1',   {'label': '', 'color':'invis'}),
        ('kvpb6_2',   {'label': '', 'color':'invis'}),
        ('kvpb6_3',   {'label': '', 'color':'invis'}),
        ('kvpb6_4',   {'label': '', 'color':'invis'}),
        ('kvpb6_5',   {'label': '', 'color':'invis'}),
        ('kvpb6_6',   {'label': '', 'color':'invis'}),
        ('kvpb6_7',   {'label': '', 'color':'invis'}),
        ('kvpb6_8',   {'label': '', 'color':'invis'}),
        ('kvpb6_9',   {'label': '', 'color':'invis'}),
        ('kvpb6_10',   {'label': '', 'color':'invis'}),
        ('kvpb6_11',   {'label': '', 'color':'invis'}),
        ('kvpb6_12',  {'label': labelWpix(0,'riak_kv_qry:maybe_await_query_results')})]
    
    kvqryqueue_funs = [
        ('kvqryqueue_0',  {'label': 'riak_kv_qry_queue',           'color': server_color}),
        ('kvqryqueue_1',  {'label': labelWpix(0,'riak_kv_qry_queue:handle_call')}),
        ('kvqryqueue_2',  {'label': labelWpix(0,'riak_kv_qry_queue:do_push_query')}),
        ('kvqryqueue_3',  {'label': labelWpix(0,'queue:in')})]
    
    kvqryworker_funs = [
        ('kvqryworker_0',  {'label': 'riak_kv_qry_worker',          'color': server_color}),
        ('kvqryworker_1',  {'label': labelWpix(0,'riak_kv_qry_worker:handle_info')})]
    
    kvqryworker1_funs = [
        ('kvqryworker1_0',  {'label': '', 'color':'invis'}),
        ('kvqryworker1_1',  {'label': '', 'color':'invis'}),
        #    ('kvqryworker1_11', {'label': '', 'color':'invis'}),
        ('kvqryworker1_2',  {'label': labelWpix(0,'riak_kv_qry_worker:pop_next_query')}),
        ('kvqryworker1_3',  {'label': labelWpix(0,'riak_kv_qry_worker:execute_query')}),
        ('kvqryworker1_4',  {'label': labelWpix(0,'riak_kv_qry_worker:run_sub_qs_fn')}),
        ('kvqryworker1_5',  {'label': labelWpix(0,'riak_kv_index_fsm_sup:start_index_fsm')})]

    kvqryworker4_funs = [
        ('kvqryworker4_0',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_1',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_2',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_3',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_4',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_5',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_6',  {'label': labelWpix(0,'supervisor:start_child')})]

    kvqryworker5_funs = [
        ('kvqryworker5_0',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_1',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_2',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_3',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_4',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_5',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_6',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_7',  {'label': labelWpix(0,'riak_kv_stat:update')})]

    kvqryworker2_funs = [
        ('kvqryworker2_0',    {'label': '', 'color':'invis'}),
        ('kvqryworker2_1',    {'label': '', 'color':'invis'}),
        #   ('kvqryworker2_11',   {'label': '', 'color':'invis'}),
        ('kvqryworker2_2',    {'label': labelWpix(0,'riak_kv_qry_worker:subqueries_done')})]
    
    kvqryworker3_funs = [
        ('kvqryworker3_0',    {'label': '', 'color':'invis'}),
        ('kvqryworker3_1',    {'label': '', 'color':'invis'}),
        #  ('kvqryworker2_11',   {'label':'', 'color':'invis'}),
        ('kvqryworker3_2',    {'label': labelWpix(0,'riak_kv_qry_worker:add_subquery_result')})]
    
    kvindexfsm_funs = [
        ('kvindexfsm_0',  {'label': 'riak_kv_index_fsm',           'color': fsm_color}),
        ('kvindexfsm_1',  {'label': labelWpix(0,'riak_core_coverage_fsm:init')})]

    cc0_funs = [
        ('cc0_0',  {'label': '',           'color':'invis'}),
        ('cc0_1',  {'label': '',           'color':'invis'}),
        ('cc0_2',  {'label': labelWpix(0,'riak_kv_index_fsm:module_info')})]
    
    cc1_funs = [
        ('cc1_0',  {'label': '',           'color':'invis'}),
        ('cc1_1',  {'label': '',           'color':'invis'}),
        ('cc1_2',  {'label': '',           'color':'invis'}),
        ('cc1_3',  {'label': labelWpix(0,'riak_kv_index_fsm:init')})]

    cc1_1_funs = [
        ('cc1_1_0',  {'label': '',           'color':'invis'}),
        ('cc1_1_1',  {'label': '',           'color':'invis'}),
        ('cc1_1_2',  {'label': '',           'color':'invis'}),
        ('cc1_1_3',  {'label': '',           'color':'invis'}),
        ('cc1_1_4',  {'label': labelWpix(0,'riak_core_coverage_fsm:maybe_start_timeout_timer')})]

    cc2_funs = [
        ('cc2_0',  {'label': '',           'color':'invis'}),
        ('cc2_1',  {'label': '',           'color':'invis'}),
        ('cc2_2',  {'label': '',           'color':'invis'}),
        ('cc2_3',  {'label': '',           'color':'invis'}),
        ('cc2_4',  {'label': '',           'color':'invis'}),
        ('cc2_5',  {'label': labelWpix(0,'riak_core_coverage_fsm:plan_callback')})]

    cc3_funs = [
        ('cc3_0',  {'label': '',           'color':'invis'}),
        ('cc3_1',  {'label': '',           'color':'invis'}),
        ('cc3_2',  {'label': '',           'color':'invis'}),
        ('cc3_3',  {'label': '',           'color':'invis'}),
        ('cc3_4',  {'label': '',           'color':'invis'}),
        ('cc3_5',  {'label': '',           'color':'invis'}),
        ('cc3_6',  {'label': labelWpix(0,'riak_core_coverage_fsm:process_results_callback')})]

    kvindexfsm4_funs = [
        ('kvindexfsm4_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm4_1',  {'label': labelWpix(0,'riak_core_coverage_fsm:initialize')}),
        ('kvindexfsm4_2',  {'label': labelWpix(0,'riak_core_vnode_master:coverage')}),
        ('kvindexfsm4_3',  {'label': labelWpix(0,'riak_core_vnode_master:proxy_cast')}),
        ('kvindexfsm4_4',  {'label': labelWpix(0,'gen_fsm:send_event')})]
    
    kvindexfsm1_funs = [
        ('kvindexfsm1_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm1_1',  {'label': labelWpix(0,'riak_core_coverage_fsm:waiting_results')})]
    
    kvindexfsm2_funs = [
        ('kvindexfsm2_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm2_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm2_2',  {'label': labelWpix(0,'riak_kv_index_fsm:process_results')})]
    
    kvindexfsm5_funs = [
        ('kvindexfsm5_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm5_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm5_2',  {'label': '',           'color':'invis'}),
        ('kvindexfsm5_3',  {'label': labelWpix(0,'riak_kv_index_fsm:process_query_results')})]

    kvindexfsm6_funs = [
        ('kvindexfsm6_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_2',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_3',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_4',  {'label': labelWpix(0,'riak_kv_vnode:ack_keys')})]

    kvindexfsm3_funs = [
        ('kvindexfsm3_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm3_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm3_2',  {'label': labelWpix(0,'riak_kv_index_fsm:finish')})]
    
    
    corevnode_funs = [
        ('corevnode_0',  {'label': 'riak_core_vnode',             'color': fsm_color}),
        ('corevnode_01', {'label': labelWpix(0,'riak_core_vnode:handle_event')}),
        ('corevnode_1',  {'label': labelWpix(0,'riak_core_vnode:active')}),
        ('corevnode_2',  {'label': labelWpix(0,'riak_core_vnode:vnode_coverage')}),
        #    ('corevnode_3',  {'label': 'riak_kv_vnode:\nhandle_coverage'}),
        #    ('corevnode_4',  {'label': 'riak_kv_vnode:\nhandle_range_scan'}),
        #    ('corevnode_5',  {'label': 'riak_kv_vnode:\nhandle_coverage_range_scan'}),
        ('corevnode_6',  {'label': labelWpix(0,'riak_core_vnode_worker_pool:handle_work')}),
        ('corevnode_7',  {'label': labelWpix(0,'gen_fsm:send_event')})]
    
    corevnodeworkerpool_funs = [
        ('corevnodeworkerpool_0', {'label': 'riak_core_vnode_worker_pool', 'color': fsm_color}),
        ('corevnodeworkerpool_1', {'label': labelWpix(0,'riak_core_vnode_worker_pool:handle_event')}),
        ('corevnodeworkerpool_2', {'label': labelWpix(0,'riak_core_vnode_worker:handle_work')}),
        ('corevnodeworkerpool_3', {'label': labelWpix(0,'gen_server:cast')})]
    
    testLabel = '<<TABLE border="0" cellborder="0"><TR><TD>Hello</TD></TR><TR><TD width="30" height="30" fixedsize="true"><IMG SRC="test.png" scale="true"/></TD></TR></TABLE>>'
    
    corevnodeworker_funs = [
        ('corevnodeworker_0',  {'label': 'riak_core_vnode_worker',      'color': server_color}),
        ('corevnodeworker_1',  {'label': labelWpix(0, 'riak_core_vnode_worker:handle_cast')}),
        ('corevnodeworker_2',  {'label': labelWpix(0, 'riak_kv_worker:handle_work')})]

    
    corevnodeworker1_funs = [
        ('corevnodeworker1_0',  {'label': '',           'color':'invis'}),
        ('corevnodeworker1_1',  {'label': '',           'color':'invis'}),
        ('corevnodeworker1_2',  {'label': '',           'color':'invis'}),
        ('corevnodeworker1_3',  {'label': labelWpix(0, 'eleveldb:fold')})]
    
    corevnodeworker2_funs = [
        ('corevnodeworker2_0',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_1',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_2',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_3',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_4',  {'label': labelWpix(0, 'riak_kv_vnode:result_fun_ack')}),
        ('corevnodeworker2_5',  {'label': labelWpix(0, 'riak_core_vnode:reply')})]

    corevnodeworker3_funs = [
        ('corevnodeworker3_0',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_1',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_2',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_3',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_4',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_5',  {'label': labelWpix(0, 'riak_kv_vnode:finish_fold')}),
        ('corevnodeworker3_6',  {'label': labelWpix(0, 'riak_core_vnode:reply')})]

    dg = createDigraph([
        riakc_funs,
        riakpb_funs,
        riakpb1_funs,
        riakpb_funs2,
        riakpb3_funs,
        riakpb4_funs,
        riakpb5_funs,
        kvp_funs,
        kvp4_funs,
        kvp5_funs,
        kvp3_funs,
        kvp1_funs,
        kvp2_funs,
        kvp6_funs,
        kvp7_funs,
        kvp8_funs,
        kvp9_funs,
        kvp10_funs,
        kvqryqueue_funs,
        kvqryworker_funs,
        kvqryworker1_funs,
        kvqryworker2_funs,
        kvqryworker3_funs,
        kvqryworker4_funs,
        kvqryworker5_funs,
        kvindexfsm_funs,
        kvindexfsm1_funs,
        kvindexfsm2_funs,
        kvindexfsm3_funs,
        kvindexfsm4_funs,
        kvindexfsm5_funs,
        kvindexfsm6_funs,
        cc0_funs,
        cc1_funs,
        cc1_1_funs,
        cc2_funs,
        cc3_funs,
        corevnode_funs,
        corevnodeworkerpool_funs,
        corevnodeworker_funs,
        corevnodeworker1_funs,
        corevnodeworker2_funs,
        corevnodeworker3_funs])

    ortho = False
    #ortho = True

    if ortho:
        lab = 'xlabel'
    else:
        lab = 'label'

    # This is just to force graphviz to place 4_6 lower than 5_7
    
    dg.edge('kvqryworker5_7', 'kvqryworker4_6', '', {'color':'invis'})
    dg.edge('kvpb8_6', 'kvpb7_7', '', {'color':'invis'})
    
    dg.edge('riakpb_0', 'riakpb_5', '', {'arrowhead':'none'})

    dg.edge('riakpb_2', 'riakpb1_3')
    dg.edge('riakpb_2', 'riakpb4_4')
    dg.edge('riakpb_5', 'riakpb3_2')
    dg.edge('riakpb_5', 'riakpb5_3')

    dg.edge('kvqryworker_1', 'kvqryworker2_2')
    dg.edge('kvqryworker_1', 'kvqryworker1_2')
    dg.edge('kvqryworker_1', 'kvqryworker3_2')

    dg.edge('kvqryworker1_5', 'kvqryworker4_6')
    dg.edge('kvqryworker1_5', 'kvqryworker5_7')

    dg.edge('kvpb5_3', 'kvpb3_4')
    dg.edge('kvpb5_3', 'kvpb1_6')
    dg.edge('kvpb10_10', 'kvpb2_11')
    dg.edge('kvpb10_10', 'kvpb6_12')
    dg.edge('kvpb_1',  'kvpb4_2')
    dg.edge('kvpb_1',  'kvpb5_3')

    dg.edge('kvpb3_5',  'kvpb8_6')
    dg.edge('kvpb3_5',  'kvpb7_7')
    dg.edge('kvpb7_8',  'kvpb9_9')
    dg.edge('kvpb7_8',  'kvpb10_10')
    
    dg.edge('kvindexfsm_0',  'kvindexfsm1_1', '', {'arrowhead':'none'})
    dg.edge('kvindexfsm_0',  'kvindexfsm4_1', '', {'arrowhead':'none'})
    dg.edge('kvindexfsm1_1', 'kvindexfsm2_2')
    dg.edge('kvindexfsm1_1', 'kvindexfsm3_2')
    dg.edge('kvindexfsm2_2', 'kvindexfsm5_3')
    dg.edge('kvindexfsm2_2', 'kvindexfsm6_4')

    dg.edge('kvindexfsm_1', 'cc0_2')
    dg.edge('kvindexfsm_1', 'cc1_3')
    dg.edge('kvindexfsm_1', 'cc1_1_4')
    dg.edge('kvindexfsm_1', 'cc2_5')
    dg.edge('kvindexfsm_1', 'cc3_6')
    
    dg.edge('corevnodeworker_2', 'corevnodeworker1_3')
    dg.edge('corevnodeworker_2', 'corevnodeworker2_4')
    dg.edge('corevnodeworker_2', 'corevnodeworker3_5')

    dg.edge('riakc_3',               'riakpb_2',              '', {'color':server_color, lab:'    1 '})
    dg.edge('riakpb4_4',             'kvpb_1',                '', {'color':fsm_color,    lab:'    2 '})
    dg.edge('kvpb2_12',              'kvqryqueue_2',          '', {'color':server_color, lab:'    3 '})
    dg.edge('kvqryqueue_3',          'kvqryworker1_2',        '', {'color':server_color, lab:'    4 '})
    dg.edge('kvqryworker4_6',        'kvindexfsm_1',          '', {'color':fsm_color,    lab:labelWpix(0,'    5 '), 'dir':'both'})
    dg.edge('kvindexfsm4_4',         'corevnode_1',           '', {'color':fsm_color,    lab:'    6 '})
    dg.edge('corevnode_7',           'corevnodeworkerpool_2', '', {'color':fsm_color,    lab:'    7 '})
    dg.edge('corevnodeworkerpool_3', 'corevnodeworker_2',     '', {'color':server_color, lab:'    8 '})
    dg.edge('corevnodeworker2_5',    'kvindexfsm2_2',         '', {'color':fsm_color,    lab:'    9 '})
    dg.edge('kvindexfsm5_3',         'kvqryworker3_2',        '', {'color':server_color, lab:'   10 '})
    dg.edge('kvindexfsm6_4',         'corevnodeworker2_4',    '', {'color':server_color, lab:'   11 '})
    dg.edge('corevnodeworker3_6',    'kvindexfsm3_2',         '', {'color':fsm_color,    lab:'   12 '})
    dg.edge('kvindexfsm3_2',         'kvqryworker2_2',        '', {'color':server_color, lab:'   13 '})
    dg.edge('kvqryworker2_2',        'kvpb6_12',              '', {'color':server_color, lab:'   14 '})
    dg.edge('kvpb1_6',               'riakpb_5',              '', {'color':server_color, lab:'   15 '})
    dg.edge('riakpb5_4',             'riakc_3',               '', {'color':server_color, lab:'   16 '})
    
    if ortho:
        dg.graph_attr['splines'] = 'ortho'

    dg.graph_attr['label'] = 'RiakTS Query Path'
    dg.graph_attr['labelloc'] = 't'
    
    dg.render('riak_ts_query')
    
    return dg

def makePlots2(clientFileName,     serverFileName,
               clientBaseFileName, serverBaseFileName,
               clientCompFileName, profilerBaseFileName):

    test = DiGraph()

    test.ingestProfilerOutput(clientFileName,     serverFileName,
                              clientBaseFileName, serverBaseFileName,
                              clientCompFileName, profilerBaseFileName)
    #------------------------------------------------------------
    # Start of script
    #------------------------------------------------------------
    
    service_color = 'blue'
    fsm_color     = 'red'
    server_color  = 'cyan'

    #------------------------------------------------------------
    # riakc
    #------------------------------------------------------------
        
    riakc = Node({'label': 'riakc',       'color': service_color})

    riakc.append(({'label': 'riakc:query'},
                  {'label': 'riakc:server_call'},
                  {'tag':'gen_server_call1', 'label': 'gen_server:call'}))

    #------------------------------------------------------------
    # riak_pc_socket
    #------------------------------------------------------------

    riakpb = Node({'label': 'riakc_pb_socket',       'color': server_color})

    riakpb.setNodeAttr('riakc_pb_socket', 'rank', 'same')
                       
    riakpb.append(
        [
            (
                {'label': 'riakc_pb_socket:handle_call'},
                {'label': 'riakc_pb_socket:send_request'},
                [
                    {'label': 'riakc_pb_socket:encode_request_message'},
                    {'label': 'gen_tcp:send'}
                ]
            ),
            (
                {'label': 'riakc_pb_socket:handle_info'},
                [
                    {'label': 'riak_pb_codec:decode'},
                    (
                        {'label': 'riakc_pb_socket:send_caller'},
                        {'label' : 'gen_server:reply'}
                    )
                ]
            )
        ]
    )
    
    #------------------------------------------------------------
    # riak_api_pb_server
    #------------------------------------------------------------

    riakapi = Node({'label': 'riak_api_pb_server',       'color': fsm_color})

    riakapi.append(
        (
            {'label': 'riak_api_pb_server:connected'},
            [
                {'label': 'riak_kv_pb_timeseries:decode'},
                {'label': 'riak_api_pb_server:process_message'},
            ],
            [
                (
                    {'label': 'riak_kv_pb_timeseries:process'},
                    {'label': 'riak_kv_pb_timeseries:check_table_and_call'},
                    [
                        {'label': 'riak_kv_ts_util:get_table_ddl'},
                        (
                            {'label': 'riak_kv_pb_timeseries:sub_tsqueryreq'},
                            {'label': 'riak_kv_qry:submit'},
                            [
                                (
                                    {'label': 'riak_ql_lexer:get_tokens'},
                                    {'label': 'riak_ql_parser:parse'},
                                ),
                                (
                                    {'label': 'riak_kv_qry:maybe_submit_to_queue'},
                                    [
                                        (
                                            {'label': 'riak_kv_qry_queue:put_on_queue'},
                                            {'tag':'gen_server_call2', 'label': 'gen_server:call'}
                                        ),
                                        {'label': 'riak_kv_qry:maybe_await_query_results'}
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                {'label': 'riak_api_pb_server:send_encoded_message_or_error'}
            ]
        )
    )

    #------------------------------------------------------------
    # riak_kv_qry_queue
    #------------------------------------------------------------

    riak_kv_qry_queue = Node({'label': 'riak_kv_qry_queue',       'color': server_color})
    riak_kv_qry_queue.append(({'label': 'riak_kv_qry_queue:handle_call'},
                              {'label': 'riak_kv_qry_queue:do_push_query'},
                              {'label': 'queue:in'}))

    #------------------------------------------------------------
    # riak_kv_qry_worker
    #------------------------------------------------------------

    riak_kv_qry_worker = Node({'label': 'riak_kv_qry_worker',       'color': server_color})

    handle_info = riak_kv_qry_worker.append({'label':'riak_kv_qry_worker:handle_info'})

    riak_kv_qry_worker.setNodeAttr('riak_kv_qry_worker:handle_info', 'rank', 'same')

    handle_info.append(
        [
            (
                {'label': 'riak_kv_qry_worker:pop_next_query'},
                {'label': 'riak_kv_qry_worker:execute_query'},
                {'label': 'riak_kv_qry_worker:run_sub_qs_fn'},
                (
                    {'label': 'riak_kv_index_fsm_sup:start_index_fsm'},
                    [
                        {'label': 'supervisor:start_child'},
                        {'label': 'riak_kv_stat:update'},
                    ]
                ),
            ),
            {'label': 'riak_kv_qry_worker:add_subquery_result'},
            {'label': 'riak_kv_qry_worker:subqueries_done'},
        ]
    )

    #------------------------------------------------------------
    # riak_kv_index_fsm
    #------------------------------------------------------------

    riak_kv_index_fsm = Node({'label':'riak_kv_index_fsm', 'color':fsm_color})
    riak_kv_index_fsm.setNodeAttr('riak_kv_index_fsm', 'rank', 'same')

    riak_kv_index_fsm.append(
        [
            (
                (
                    {'label':'riak_core_coverage_fsm:waiting_results'},
                    [
                        (
                            {'label':'riak_kv_index_fsm:process_results'},
                            [
                                {'label':'riak_kv_index_fsm:process_query_results'},
                                {'label':'riak_kv_vnode:ack_keys'},
                            ]
                        ),
                        {'label':'riak_kv_index_fsm:finish'},
                    ]
                ),
            ),

            (
                {'label':'riak_core_coverage_fsm:init'},
                [
                    {'label':'riak_kv_index_fsm:module_info'},
                    {'label':'riak_kv_index_fsm:init'},
                    {'label':'riak_core_coverage_fsm:maybe_start_timeout_timer'},
                    {'label':'riak_core_coverage_fsm:plan_callback'},
                    {'label':'riak_core_coverage_fsm:plan_results_callback'}
                ]
            ),
            (
                {'label':'riak_core_coverage_fsm:initialize'},
                {'label':'riak_core_vnode_master:coverage'},
                {'label':'riak_core_vnode_master:proxy_cast'},
                {'tag':'gen_fsm1', 'label':'gen_fsm:send_event'}
            )
    ])

    riak_kv_index_fsm.setNodeAttr('riak_core_coverage_fsm:waiting_results', 'rank', 'same')

    #------------------------------------------------------------
    # riak_core_vnode_worker
    #------------------------------------------------------------
    
    riak_core_vnode_worker = Node({'label':'riak_core_vnode_worker', 'color':server_color})
    riak_core_vnode_worker.append(
        (
            {'label':'riak_core_vnode_worker:handle_cast'},
            {'label':'riak_kv_worker:handle_work'},
            [
                {'label':'eleveldb:fold'},
                (
                    {'label':'riak_kv_vnode:result_fun_ack'},
                    {'tag':'vnode_reply1', 'label':'riak_core_vnode:reply'}
                ),
                (
                    {'label':'riak_kv_vnode:finish_fold'},
                    {'tag':'vnode_reply2', 'label':'riak_core_vnode:reply'}
                )
            ]
        )
    )

    #------------------------------------------------------------
    # riak_core_vnode_worker_pool
    #------------------------------------------------------------
    
    riak_core_vnode_worker_pool = Node({'label':'riak_core_vnode_worker_pool', 'color':fsm_color})
    riak_core_vnode_worker_pool.append(
        (
            {'label':'riak_core_vnode_worker_pool:handle_event'},
            {'label':'riak_core_vnode_worker:handle_work'},
            {'label':'gen_server:cast'},
        )
    )

    #------------------------------------------------------------
    # riak_core_vnode
    #------------------------------------------------------------
    
    riak_core_vnode = Node({'label':'riak_core_vnode', 'color':fsm_color})
    riak_core_vnode.append(
        (
            {'label':'riak_core_vnode:handle_event'},
            {'label':'riak_core_vnode:active'},
            {'label':'riak_core_vnode:vnode_coverage'},
            {'label':'riak_core_vnode_worker_pool:handle_work'},
            {'tag':'gen_fsm2', 'label':'gen_fsm:send_event'},
        )
    )
        
    test.append(riakc)
    test.append(riakpb)
    test.append(riakapi)
    test.append(riak_kv_qry_queue)
    test.append(riak_kv_qry_worker)
    test.append(riak_kv_index_fsm)
    test.append(riak_core_vnode_worker)
    test.append(riak_core_vnode_worker_pool)
    test.append(riak_core_vnode)
    
    test.edge('gen_server_call1',                                 'riakc_pb_socket:send_request',          {'color':server_color, 'label':' 1 '})
    test.edge('gen_tcp:send',                                     'riak_api_pb_server:connected',          {'color':fsm_color,    'label':' 2 '})
    test.edge('gen_server:call2',                                 'riak_kv_qry_queue:do_push_query',       {'color':server_color, 'label':' 3 '})
    test.edge('queue:in',                                         'riak_kv_qry_worker:pop_next_query',     {'color':server_color, 'label':' 4 '})
    test.edge('supervisor:start_child',                           'riak_core_coverage_fsm:init',           {'color':fsm_color,    'label':' 5 ', 'dir':'both'})
    test.edge('gen_fsm1',                                         'riak_core_vnode:active',                {'color':fsm_color,    'label':' 6 '})
    test.edge('gen_fsm2',                                         'riak_core_vnode_worker:handle_work',    {'color':fsm_color,    'label':' 7 '})
    test.edge('gen_server:cast',                                  'riak_kv_worker:handle_work',            {'color':server_color, 'label':' 8 '})
    test.edge('vnode_reply1',                                     'riak_kv_index_fsm:process_results',     {'color':fsm_color,    'label':' 9 '})
    test.edge('riak_kv_index_fsm:process_query_results',          'riak_kv_qry_worker:add_subquery_result',{'color':server_color, 'label':' 10 '})
    test.edge('riak_kv_vnode:ack_keys',                           'riak_kv_vnode:result_fun_ack',          {'color':server_color, 'label':' 11 '})
    test.edge('vnode_reply2',                                     'riak_kv_index_fsm:finish',              {'color':fsm_color,    'label':' 12 '})
    test.edge('riak_kv_index_fsm:finish',                         'riak_kv_qry_worker:subqueries_done',    {'color':server_color, 'label':' 13 '})
    test.edge('riak_kv_qry_worker:subqueries_done',               'riak_kv_qry:maybe_await_query_results', {'color':server_color, 'label':' 14 '})
    test.edge('riak_api_pb_server:send_encoded_message_or_error', 'riakc_pb_socket:handle_info',           {'color':server_color, 'label':' 15 '})
    test.edge('gen_server:reply',                                  'gen_server_call1',                     {'color':server_color, 'label':' 16 '})

    test.title('RiakTS Query Path' + ' (' + str(int(test.totalUsec/(10000))) + ' &mu;s)')
    test.render('test')
    
    return

    riakpb1_funs = [
        ('riakpb1_0',  {'label': '',       'color':'invis'}),
        ('riakpb1_1',  {'label': '',       'color':'invis'}),
        ('riakpb1_2',  {'label': '',       'color':'invis'}),
        ('riakpb1_3',  {'label': labelWpix(0,'riak_pb_codec:encode')})]

    riakpb4_funs = [
        ('riakpb4_0',  {'label': '',       'color':'invis'}),
        ('riakpb4_1',  {'label': '',       'color':'invis'}),
        ('riakpb4_2',  {'label': '',       'color':'invis'}),
        ('riakpb4_3',  {'label': '',       'color':'invis'}),
        ('riakpb4_4',  {'label': labelWpix(0,'gen_tcp:send')})]
    
    riakpb_funs2 = [
        ('riakpb_4',  {'label': '', 'color':'invis'}),
        ('riakpb_5',  {'label': labelWpix(0,'riakc_pb_socket:handle_info')})]

    riakpb3_funs = [
        ('riakpb3_0',  {'label': '', 'color':'invis'}),
        ('riakpb3_1',  {'label': '', 'color':'invis'}),
        ('riakpb3_2',  {'label': labelWpix(0,'riak_pb_codec:decode')})]

    riakpb5_funs = [
        ('riakpb5_0',  {'label': '', 'color':'invis'}),
        ('riakpb5_1',  {'label': '', 'color':'invis'}),
        ('riakpb5_2',  {'label': '', 'color':'invis'}),
        ('riakpb5_3',  {'label': labelWpix(0,'riakc_pb_socket:send_caller')}),
        ('riakpb5_4',  {'label': labelWpix(0,'gen_server:reply')})
    ]
    
    kvp_funs = [
        ('kvpb_0',  {'label': 'riak_api_pb_server',         'color': fsm_color}),
        ('kvpb_1',  {'label': labelWpix(0,'riak_api_pb_server:connected')})]

    kvp4_funs = [
        ('kvpb4_0',  {'label': '',         'color': 'invis'}),
        ('kvpb4_1',  {'label': '',         'color': 'invis'}),
        ('kvpb4_2',  {'label': labelWpix(0,'riak_kv_pb_timeseries:decode')})]

    kvp5_funs = [
        ('kvpb5_0',  {'label': '',         'color': 'invis'}),
        ('kvpb5_1',  {'label': '',         'color': 'invis'}),
        ('kvpb5_2',  {'label': '',         'color': 'invis'}),
        ('kvpb5_3',  {'label': labelWpix(0,'riak_api_pb_server:process_message')})]

    kvp3_funs = [
        ('kvpb3_0',  {'label': '', 'color':'invis'}),
        ('kvpb3_1',  {'label': '', 'color':'invis'}),
        ('kvpb3_2',  {'label': '', 'color':'invis'}),
        ('kvpb3_3',  {'label': '', 'color':'invis'}),
        ('kvpb3_4',  {'label': labelWpix(0,'riak_kv_pb_timeseries:process')}),
        ('kvpb3_5',  {'label': labelWpix(0,'riak_kv_pb_timeseries:check_table_and_call')})]
    
    kvp8_funs = [
        ('kvpb8_0',  {'label': '', 'color':'invis'}),
        ('kvpb8_1',  {'label': '', 'color':'invis'}),
        ('kvpb8_2',  {'label': '', 'color':'invis'}),
        ('kvpb8_3',  {'label': '', 'color':'invis'}),
        ('kvpb8_4',  {'label': '', 'color':'invis'}),
        ('kvpb8_5',  {'label': '', 'color':'invis'}),
        ('kvpb8_6',  {'label': labelWpix(0,'riak_kv_ts_util:get_table_ddl')})]

    kvp7_funs = [
        ('kvpb7_0',  {'label': '', 'color':'invis'}),
        ('kvpb7_1',  {'label': '', 'color':'invis'}),
        ('kvpb7_2',  {'label': '', 'color':'invis'}),
        ('kvpb7_3',  {'label': '', 'color':'invis'}),
        ('kvpb7_4',  {'label': '', 'color':'invis'}),
        ('kvpb7_5',  {'label': '', 'color':'invis'}),
        ('kvpb7_6',  {'label': '', 'color':'invis'}),
        ('kvpb7_7',  {'label': labelWpix(0,'riak_kv_pb_timeseries:sub_tsqueryreq')}),
        ('kvpb7_8',  {'label': labelWpix(0,'riak_kv_qry:submit')})]

    kvp9_funs = [
        ('kvpb9_0',  {'label': '', 'color':'invis'}),
        ('kvpb9_1',  {'label': '', 'color':'invis'}),
        ('kvpb9_2',  {'label': '', 'color':'invis'}),
        ('kvpb9_3',  {'label': '', 'color':'invis'}),
        ('kvpb9_4',  {'label': '', 'color':'invis'}),
        ('kvpb9_5',  {'label': '', 'color':'invis'}),
        ('kvpb9_6',  {'label': '', 'color':'invis'}),
        ('kvpb9_7',  {'label': '', 'color':'invis'}),
        ('kvpb9_8',  {'label': '', 'color':'invis'}),
        ('kvpb9_9',  {'label': labelWpix(0,'riak_ql_lexer:get_tokens')}),
        ('kvpb9_10', {'label': labelWpix(0,'riak_ql_parser:parse')})]

    kvp10_funs = [
        ('kvpb10_0',  {'label': '', 'color':'invis'}),
        ('kvpb10_1',  {'label': '', 'color':'invis'}),
        ('kvpb10_2',  {'label': '', 'color':'invis'}),
        ('kvpb10_3',  {'label': '', 'color':'invis'}),
        ('kvpb10_4',  {'label': '', 'color':'invis'}),
        ('kvpb10_5',  {'label': '', 'color':'invis'}),
        ('kvpb10_6',  {'label': '', 'color':'invis'}),
        ('kvpb10_7',  {'label': '', 'color':'invis'}),
        ('kvpb10_8',  {'label': '', 'color':'invis'}),
        ('kvpb10_9',  {'label': '', 'color':'invis'}),
        ('kvpb10_10', {'label': labelWpix(0,'riak_kv_qry:maybe_submit_to_queue')})]

    kvp1_funs = [
        ('kvpb1_0',   {'label': '', 'color':'invis'}),
        ('kvpb1_1',   {'label': '', 'color':'invis'}),
        ('kvpb1_3',   {'label': '', 'color':'invis'}),
        ('kvpb1_4',   {'label': '', 'color':'invis'}),
        ('kvpb1_5',   {'label': '', 'color':'invis'}),
        ('kvpb1_6',   {'label': labelWpix(0,'riak_api_pb_server:send_encoded_message_or_error')})]
    
    kvp2_funs = [
        ('kvpb2_0',   {'label': '', 'color':'invis'}),
        ('kvpb2_1',   {'label': '', 'color':'invis'}),
        ('kvpb2_2',   {'label': '', 'color':'invis'}),
        ('kvpb2_3',   {'label': '', 'color':'invis'}),
        ('kvpb2_4',   {'label': '', 'color':'invis'}),
        ('kvpb2_5',   {'label': '', 'color':'invis'}),
        ('kvpb2_6',   {'label': '', 'color':'invis'}),
        ('kvpb2_7',   {'label': '', 'color':'invis'}),
        ('kvpb2_8',   {'label': '', 'color':'invis'}),
        ('kvpb2_9',   {'label': '', 'color':'invis'}),
        ('kvpb2_10',  {'label': '', 'color':'invis'}),
        ('kvpb2_11',  {'label': labelWpix(0,'riak_kv_qry_queue:put_on_queue')}),
        ('kvpb2_12',  {'label': labelWpix(0,'gen_server:call')})]

    kvp6_funs = [
        ('kvpb6_0',   {'label': '', 'color':'invis'}),
        ('kvpb6_1',   {'label': '', 'color':'invis'}),
        ('kvpb6_2',   {'label': '', 'color':'invis'}),
        ('kvpb6_3',   {'label': '', 'color':'invis'}),
        ('kvpb6_4',   {'label': '', 'color':'invis'}),
        ('kvpb6_5',   {'label': '', 'color':'invis'}),
        ('kvpb6_6',   {'label': '', 'color':'invis'}),
        ('kvpb6_7',   {'label': '', 'color':'invis'}),
        ('kvpb6_8',   {'label': '', 'color':'invis'}),
        ('kvpb6_9',   {'label': '', 'color':'invis'}),
        ('kvpb6_10',   {'label': '', 'color':'invis'}),
        ('kvpb6_11',   {'label': '', 'color':'invis'}),
        ('kvpb6_12',  {'label': labelWpix(0,'riak_kv_qry:maybe_await_query_results')})]
    
    kvqryqueue_funs = [
        ('kvqryqueue_0',  {'label': 'riak_kv_qry_queue',           'color': server_color}),
        ('kvqryqueue_1',  {'label': labelWpix(0,'riak_kv_qry_queue:handle_call')}),
        ('kvqryqueue_2',  {'label': labelWpix(0,'riak_kv_qry_queue:do_push_query')}),
        ('kvqryqueue_3',  {'label': labelWpix(0,'queue:in')})]
    
    kvqryworker_funs = [
        ('kvqryworker_0',  {'label': 'riak_kv_qry_worker',          'color': server_color}),
        ('kvqryworker_1',  {'label': labelWpix(0,'riak_kv_qry_worker:handle_info')})]
    
    kvqryworker1_funs = [
        ('kvqryworker1_0',  {'label': '', 'color':'invis'}),
        ('kvqryworker1_1',  {'label': '', 'color':'invis'}),
        #    ('kvqryworker1_11', {'label': '', 'color':'invis'}),
        ('kvqryworker1_2',  {'label': labelWpix(0,'riak_kv_qry_worker:pop_next_query')}),
        ('kvqryworker1_3',  {'label': labelWpix(0,'riak_kv_qry_worker:execute_query')}),
        ('kvqryworker1_4',  {'label': labelWpix(0,'riak_kv_qry_worker:run_sub_qs_fn')}),
        ('kvqryworker1_5',  {'label': labelWpix(0,'riak_kv_index_fsm_sup:start_index_fsm')})]

    kvqryworker4_funs = [
        ('kvqryworker4_0',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_1',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_2',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_3',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_4',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_5',  {'label': '', 'color':'invis'}),
        ('kvqryworker4_6',  {'label': labelWpix(0,'supervisor:start_child')})]

    kvqryworker5_funs = [
        ('kvqryworker5_0',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_1',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_2',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_3',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_4',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_5',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_6',  {'label': '', 'color':'invis'}),
        ('kvqryworker5_7',  {'label': labelWpix(0,'riak_kv_stat:update')})]

    kvqryworker2_funs = [
        ('kvqryworker2_0',    {'label': '', 'color':'invis'}),
        ('kvqryworker2_1',    {'label': '', 'color':'invis'}),
        #   ('kvqryworker2_11',   {'label': '', 'color':'invis'}),
        ('kvqryworker2_2',    {'label': labelWpix(0,'riak_kv_qry_worker:subqueries_done')})]
    
    kvqryworker3_funs = [
        ('kvqryworker3_0',    {'label': '', 'color':'invis'}),
        ('kvqryworker3_1',    {'label': '', 'color':'invis'}),
        #  ('kvqryworker2_11',   {'label':'', 'color':'invis'}),
        ('kvqryworker3_2',    {'label': labelWpix(0,'riak_kv_qry_worker:add_subquery_result')})]
    
    kvindexfsm_funs = [
        ('kvindexfsm_0',  {'label': 'riak_kv_index_fsm',           'color': fsm_color}),
        ('kvindexfsm_1',  {'label': labelWpix(0,'riak_core_coverage_fsm:init')})]

    cc0_funs = [
        ('cc0_0',  {'label': '',           'color':'invis'}),
        ('cc0_1',  {'label': '',           'color':'invis'}),
        ('cc0_2',  {'label': labelWpix(0,'riak_kv_index_fsm:module_info')})]
    
    cc1_funs = [
        ('cc1_0',  {'label': '',           'color':'invis'}),
        ('cc1_1',  {'label': '',           'color':'invis'}),
        ('cc1_2',  {'label': '',           'color':'invis'}),
        ('cc1_3',  {'label': labelWpix(0,'riak_kv_index_fsm:init')})]

    cc1_1_funs = [
        ('cc1_1_0',  {'label': '',           'color':'invis'}),
        ('cc1_1_1',  {'label': '',           'color':'invis'}),
        ('cc1_1_2',  {'label': '',           'color':'invis'}),
        ('cc1_1_3',  {'label': '',           'color':'invis'}),
        ('cc1_1_4',  {'label': labelWpix(0,'riak_core_coverage_fsm:maybe_start_timeout_timer')})]

    cc2_funs = [
        ('cc2_0',  {'label': '',           'color':'invis'}),
        ('cc2_1',  {'label': '',           'color':'invis'}),
        ('cc2_2',  {'label': '',           'color':'invis'}),
        ('cc2_3',  {'label': '',           'color':'invis'}),
        ('cc2_4',  {'label': '',           'color':'invis'}),
        ('cc2_5',  {'label': labelWpix(0,'riak_core_coverage_fsm:plan_callback')})]

    cc3_funs = [
        ('cc3_0',  {'label': '',           'color':'invis'}),
        ('cc3_1',  {'label': '',           'color':'invis'}),
        ('cc3_2',  {'label': '',           'color':'invis'}),
        ('cc3_3',  {'label': '',           'color':'invis'}),
        ('cc3_4',  {'label': '',           'color':'invis'}),
        ('cc3_5',  {'label': '',           'color':'invis'}),
        ('cc3_6',  {'label': labelWpix(0,'riak_core_coverage_fsm:process_results_callback')})]

    kvindexfsm4_funs = [
        ('kvindexfsm4_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm4_1',  {'label': labelWpix(0,'riak_core_coverage_fsm:initialize')}),
        ('kvindexfsm4_2',  {'label': labelWpix(0,'riak_core_vnode_master:coverage')}),
        ('kvindexfsm4_3',  {'label': labelWpix(0,'riak_core_vnode_master:proxy_cast')}),
        ('kvindexfsm4_4',  {'label': labelWpix(0,'gen_fsm:send_event')})]
    
    kvindexfsm1_funs = [
        ('kvindexfsm1_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm1_1',  {'label': labelWpix(0,'riak_core_coverage_fsm:waiting_results')})]
    
    kvindexfsm2_funs = [
        ('kvindexfsm2_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm2_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm2_2',  {'label': labelWpix(0,'riak_kv_index_fsm:process_results')})]
    
    kvindexfsm5_funs = [
        ('kvindexfsm5_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm5_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm5_2',  {'label': '',           'color':'invis'}),
        ('kvindexfsm5_3',  {'label': labelWpix(0,'riak_kv_index_fsm:process_query_results')})]

    kvindexfsm6_funs = [
        ('kvindexfsm6_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_2',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_3',  {'label': '',           'color':'invis'}),
        ('kvindexfsm6_4',  {'label': labelWpix(0,'riak_kv_vnode:ack_keys')})]

    kvindexfsm3_funs = [
        ('kvindexfsm3_0',  {'label': '',           'color':'invis'}),
        ('kvindexfsm3_1',  {'label': '',           'color':'invis'}),
        ('kvindexfsm3_2',  {'label': labelWpix(0,'riak_kv_index_fsm:finish')})]
    
    
    corevnode_funs = [
        ('corevnode_0',  {'label': 'riak_core_vnode',             'color': fsm_color}),
        ('corevnode_01', {'label': labelWpix(0,'riak_core_vnode:handle_event')}),
        ('corevnode_1',  {'label': labelWpix(0,'riak_core_vnode:active')}),
        ('corevnode_2',  {'label': labelWpix(0,'riak_core_vnode:vnode_coverage')}),
        #    ('corevnode_3',  {'label': 'riak_kv_vnode:\nhandle_coverage'}),
        #    ('corevnode_4',  {'label': 'riak_kv_vnode:\nhandle_range_scan'}),
        #    ('corevnode_5',  {'label': 'riak_kv_vnode:\nhandle_coverage_range_scan'}),
        ('corevnode_6',  {'label': labelWpix(0,'riak_core_vnode_worker_pool:handle_work')}),
        ('corevnode_7',  {'label': labelWpix(0,'gen_fsm:send_event')})]
    
    corevnodeworkerpool_funs = [
        ('corevnodeworkerpool_0', {'label': 'riak_core_vnode_worker_pool', 'color': fsm_color}),
        ('corevnodeworkerpool_1', {'label': labelWpix(0,'riak_core_vnode_worker_pool:handle_event')}),
        ('corevnodeworkerpool_2', {'label': labelWpix(0,'riak_core_vnode_worker:handle_work')}),
        ('corevnodeworkerpool_3', {'label': labelWpix(0,'gen_server:cast')})]
    
    testLabel = '<<TABLE border="0" cellborder="0"><TR><TD>Hello</TD></TR><TR><TD width="30" height="30" fixedsize="true"><IMG SRC="test.png" scale="true"/></TD></TR></TABLE>>'
    
    corevnodeworker_funs = [
        ('corevnodeworker_0',  {'label': 'riak_core_vnode_worker',      'color': server_color}),
        ('corevnodeworker_1',  {'label': labelWpix(0, 'riak_core_vnode_worker:handle_cast')}),
        ('corevnodeworker_2',  {'label': labelWpix(0, 'riak_kv_worker:handle_work')})]

    
    corevnodeworker1_funs = [
        ('corevnodeworker1_0',  {'label': '',           'color':'invis'}),
        ('corevnodeworker1_1',  {'label': '',           'color':'invis'}),
        ('corevnodeworker1_2',  {'label': '',           'color':'invis'}),
        ('corevnodeworker1_3',  {'label': labelWpix(0, 'eleveldb:fold')})]
    
    corevnodeworker2_funs = [
        ('corevnodeworker2_0',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_1',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_2',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_3',  {'label': '',           'color':'invis'}),
        ('corevnodeworker2_4',  {'label': labelWpix(0, 'riak_kv_vnode:result_fun_ack')}),
        ('corevnodeworker2_5',  {'label': labelWpix(0, 'riak_core_vnode:reply')})]

    corevnodeworker3_funs = [
        ('corevnodeworker3_0',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_1',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_2',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_3',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_4',  {'label': '',           'color':'invis'}),
        ('corevnodeworker3_5',  {'label': labelWpix(0, 'riak_kv_vnode:finish_fold')}),
        ('corevnodeworker3_6',  {'label': labelWpix(0, 'riak_core_vnode:reply')})]

    dg = createDigraph([
        riakc_funs,
        riakpb_funs,
        riakpb1_funs,
        riakpb_funs2,
        riakpb3_funs,
        riakpb4_funs,
        riakpb5_funs,
        kvp_funs,
        kvp4_funs,
        kvp5_funs,
        kvp3_funs,
        kvp1_funs,
        kvp2_funs,
        kvp6_funs,
        kvp7_funs,
        kvp8_funs,
        kvp9_funs,
        kvp10_funs,
        kvqryqueue_funs,
        kvqryworker_funs,
        kvqryworker1_funs,
        kvqryworker2_funs,
        kvqryworker3_funs,
        kvqryworker4_funs,
        kvqryworker5_funs,
        kvindexfsm_funs,
        kvindexfsm1_funs,
        kvindexfsm2_funs,
        kvindexfsm3_funs,
        kvindexfsm4_funs,
        kvindexfsm5_funs,
        kvindexfsm6_funs,
        cc0_funs,
        cc1_funs,
        cc1_1_funs,
        cc2_funs,
        cc3_funs,
        corevnode_funs,
        corevnodeworkerpool_funs,
        corevnodeworker_funs,
        corevnodeworker1_funs,
        corevnodeworker2_funs,
        corevnodeworker3_funs])

    ortho = False
    #ortho = True

    if ortho:
        lab = 'xlabel'
    else:
        lab = 'label'

    # This is just to force graphviz to place 4_6 lower than 5_7
    
    dg.edge('kvqryworker5_7', 'kvqryworker4_6', '', {'color':'invis'})
    dg.edge('kvpb8_6', 'kvpb7_7', '', {'color':'invis'})
    
    dg.edge('riakpb_0', 'riakpb_5', '', {'arrowhead':'none'})

    dg.edge('riakpb_2', 'riakpb1_3')
    dg.edge('riakpb_2', 'riakpb4_4')
    dg.edge('riakpb_5', 'riakpb3_2')
    dg.edge('riakpb_5', 'riakpb5_3')

    dg.edge('kvqryworker_1', 'kvqryworker2_2')
    dg.edge('kvqryworker_1', 'kvqryworker1_2')
    dg.edge('kvqryworker_1', 'kvqryworker3_2')

    dg.edge('kvqryworker1_5', 'kvqryworker4_6')
    dg.edge('kvqryworker1_5', 'kvqryworker5_7')

    dg.edge('kvpb5_3', 'kvpb3_4')
    dg.edge('kvpb5_3', 'kvpb1_6')
    dg.edge('kvpb10_10', 'kvpb2_11')
    dg.edge('kvpb10_10', 'kvpb6_12')
    dg.edge('kvpb_1',  'kvpb4_2')
    dg.edge('kvpb_1',  'kvpb5_3')

    dg.edge('kvpb3_5',  'kvpb8_6')
    dg.edge('kvpb3_5',  'kvpb7_7')
    dg.edge('kvpb7_8',  'kvpb9_9')
    dg.edge('kvpb7_8',  'kvpb10_10')
    
    dg.edge('kvindexfsm_0',  'kvindexfsm1_1', '', {'arrowhead':'none'})
    dg.edge('kvindexfsm_0',  'kvindexfsm4_1', '', {'arrowhead':'none'})
    dg.edge('kvindexfsm1_1', 'kvindexfsm2_2')
    dg.edge('kvindexfsm1_1', 'kvindexfsm3_2')
    dg.edge('kvindexfsm2_2', 'kvindexfsm5_3')
    dg.edge('kvindexfsm2_2', 'kvindexfsm6_4')

    dg.edge('kvindexfsm_1', 'cc0_2')
    dg.edge('kvindexfsm_1', 'cc1_3')
    dg.edge('kvindexfsm_1', 'cc1_1_4')
    dg.edge('kvindexfsm_1', 'cc2_5')
    dg.edge('kvindexfsm_1', 'cc3_6')
    
    dg.edge('corevnodeworker_2', 'corevnodeworker1_3')
    dg.edge('corevnodeworker_2', 'corevnodeworker2_4')
    dg.edge('corevnodeworker_2', 'corevnodeworker3_5')

    dg.edge('riakc_3',               'riakpb_2',              '', {'color':server_color, lab:'    1 '})
    dg.edge('riakpb4_4',             'kvpb_1',                '', {'color':fsm_color,    lab:'    2 '})
    dg.edge('kvpb2_12',              'kvqryqueue_2',          '', {'color':server_color, lab:'    3 '})
    dg.edge('kvqryqueue_3',          'kvqryworker1_2',        '', {'color':server_color, lab:'    4 '})
    dg.edge('kvqryworker4_6',        'kvindexfsm_1',          '', {'color':fsm_color,    lab:labelWpix(0,'    5 '), 'dir':'both'})
    dg.edge('kvindexfsm4_4',         'corevnode_1',           '', {'color':fsm_color,    lab:'    6 '})
    dg.edge('corevnode_7',           'corevnodeworkerpool_2', '', {'color':fsm_color,    lab:'    7 '})
    dg.edge('corevnodeworkerpool_3', 'corevnodeworker_2',     '', {'color':server_color, lab:'    8 '})
    dg.edge('corevnodeworker2_5',    'kvindexfsm2_2',         '', {'color':fsm_color,    lab:'    9 '})
    dg.edge('kvindexfsm5_3',         'kvqryworker3_2',        '', {'color':server_color, lab:'   10 '})
    dg.edge('kvindexfsm6_4',         'corevnodeworker2_4',    '', {'color':server_color, lab:'   11 '})
    dg.edge('corevnodeworker3_6',    'kvindexfsm3_2',         '', {'color':fsm_color,    lab:'   12 '})
    dg.edge('kvindexfsm3_2',         'kvqryworker2_2',        '', {'color':server_color, lab:'   13 '})
    dg.edge('kvqryworker2_2',        'kvpb6_12',              '', {'color':server_color, lab:'   14 '})
    dg.edge('kvpb1_6',               'riakpb_5',              '', {'color':server_color, lab:'   15 '})
    dg.edge('riakpb5_4',             'riakc_3',               '', {'color':server_color, lab:'   16 '})
    
    if ortho:
        dg.graph_attr['splines'] = 'ortho'

    dg.graph_attr['label'] = 'RiakTS Query Path'
    dg.graph_attr['labelloc'] = 't'
    
    dg.render('riak_ts_query')
    
    return dg

#makePlots('client.txt', 'server.txt', 'clientbase.txt', 'serverbase.txt', 'clientcomp.txt', 'profbase.txt')
#parseTest()

def doit():
    makePlots2('client.txt', 'server.txt', 'clientbase.txt', 'serverbase.txt', 'clientcomp.txt', 'profbase.txt')

doit()



                            
