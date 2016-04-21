#!/usr/bin/python
import sys
import graphviz as gv
import functools
import numpy
import pylab
import os

#=======================================================================
# A class for managing a node in a digraph
#=======================================================================

class Node:

    def __init__(self, args):
        if isinstance(args, dict):
            self.nodes = []
            self.attr  = args
            self.node_attr = {'depth':0, 'frac':-1, 'rank':'descending'}
        elif isinstance(args, Node):
            self.nodes = args.nodes
            self.attr  = args.attr
            self.node_attr = args.node_attr
        else:
            raise TypeError("constructor must be called with either a dictionary or a Node object")
        
    def setFrac(self, frac):
        self.frac = frac
        
    def setDepth(self, depth):
        for i in range(len(self.nodes)):
            if self.node_attr['rank'] == 'same':
                if 'depth' not in self.node_attr.keys():
                    self.nodes[i].node_attr['depth'] = depth + 1
            else:
                if 'depth' not in self.node_attr.keys():
                    self.nodes[i].node_attr['depth'] = depth + i + 1
            self.nodes[i].setDepth(self.nodes[i].node_attr['depth'])

    def setShape(self, shape):
        for node in self.nodes:
            node.attr['shape'] = shape
            node.setShape(shape)

    def setArrowhead(self, shape):
        for node in self.nodes:
            node.attr['arrowhead'] = shape
            node.setArrowhead(shape)

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

    def appendTo(self, tag, node):
        appendNode = self.findNode(tag)
        if appendNode != None:
            return appendNode.append(node)

    def insertBetween(self, tag1, tag2, node):

        node1 = self.findNode(tag1)
        node2 = self.findNode(tag2)
        [parent1, index1] = self.findParentOfNode(tag1)
        [parent2, index2] = self.findParentOfNode(tag2)

        # Both nodes must exist in order to insert between them!
        
        if node1 == None or node2 == None:
            return None

        # Case 1: both nodes have the same parent.  In this case, insert at index1
        #
        # N1, N2  becomes N1, N, N2
        
        if parent1 == parent2:
            inNode = Node(node)
            return parent1.nodes.insert(index1+1,  inNode)
        
        # Case 2: node1 is parent of node2
        #
        # N1  becomes  N1
        # |            |
        # N2           N
        #              |
        #              N2
        
        elif parent2 == node1:
            inNode = Node(node)
            inNode.append(node2)
            node1.nodes.remove(node2)
            return node1.nodes.insert(index2+1, inNode)

        else:
            return None
            
    def findNode(self, tag):
        if getTag(self.attr) == sanitizeForGraphviz(tag):
            return self
        else:
            for n in self.nodes:
                node = n.findNode(tag)
                if node != None:
                    return node
        return None

    def findParentOfNode(self, tag):

        # See if we are the parent

        index=0
        for n in self.nodes:
            if getTag(n.attr) == sanitizeForGraphviz(tag):
                return [self, index]
            index = index+1

        # Else see if one of our children is the parent
        
        for n in self.nodes:
            [node, index] = n.findParentOfNode(tag)
            if node != None:
                return [node, index]

        # Else return None
        
        return [None, 0]

    #------------------------------------------------------------
    # Connect this node to its children, and its children to theirs
    #------------------------------------------------------------

    def connectNodes(self, graph, delta=False):

        # Connect this node to all of its children, and its children to theirs

        attr = {}
        for node in self.nodes:
            if delta:
                attr['color'] = 'gray'
            if 'arrowhead' in self.attr.keys():
                attr['arrowhead'] = self.attr['arrowhead']
            graph.edge(getTag(self.attr), getTag(node.attr), **attr)
            node.connectNodes(graph, delta)

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

    def setLabels(self, profilerActualDict, nQuery, deltaTuple):
        for node in self.nodes:
            node.renderLabel(profilerActualDict, nQuery, deltaTuple)
            node.setLabels(profilerActualDict, nQuery, deltaTuple)

    def constructLabel(self, tag, label, annotation, profilerActualDict, nQuery, deltaTuple, color=None):

        (delta, deltaFrac, refUsec, threshold) = deltaTuple
        
        if not os.path.isdir("figs"):
            os.mkdir("figs")
            
        if tag in profilerActualDict.keys():
            frac = profilerActualDict[tag]['frac']

            if deltaFrac:
                val = frac
            else:
                val = profilerActualDict[tag]['corrusec']
                print 'REFUSEC = ' + str(refUsec)
        else:
            frac = -1
            val = 0.0
            threshold = 0.0
            
        pieColor = 'red'
        if delta and (numpy.abs(val) < threshold or tag not in profilerActualDict.keys()):
            self.attr['color'] = 'gray'
            color = 'gray'
            pieColor = 'white'
        elif delta and val <= 0.0:
            self.attr['color'] = 'darkgreen'
            pieColor = 'darkgreen'
            self.attr['penwidth'] = '2'
            self.attr['style'] = 'filled'
            self.attr['fillcolor'] = 'darkseagreen1'
        elif delta and val > 0.0:
            self.attr['color'] = 'red'
            pieColor = 'red'
            self.attr['penwidth'] = '2'
            self.attr['style'] = 'filled'
            self.attr['fillcolor'] = 'mistyrose'
        
        if frac >= 0:
            pieGen(frac, pieColor)
        elif delta and tag in profilerActualDict.keys():
            pieGen(numpy.abs(frac), pieColor)
            
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

        if not delta and frac >= 0:

            if frac < 1.0:
                fracStr = '&lt; 1%'
            else:
                fracStr = str(int(frac)) + '%'

            retLabel += '<TR><TD width="30" height="30" fixedsize="true">' + '<IMG SRC="figs/pc_' + str(int(frac)) + '.png" scale="true"/>' + '</TD></TR>'
            retLabel += '<TR><TD><FONT color="gray">' + getTimeStr(profilerActualDict[tag]['corrusec']/nQuery) + ' (' + fracStr + ')</FONT></TD></TR>'

        elif delta and tag in profilerActualDict.keys():

            if numpy.abs(frac) < 1.0:
                if frac < 0.0:
                    fracStr = '- &lt; 1%'
                else:
                    fracStr = '+ &lt; 1%'
            elif frac < 0.0:
                fracStr = str(int(frac)) + '%'
            else:
                fracStr = '+' + str(int(frac)) + '%'

            timeStr = getTimeStr(profilerActualDict[tag]['corrusec']/nQuery, delta)
                
            retLabel += '<TR><TD width="30" height="30" fixedsize="true">' + '<IMG SRC="figs/pc_' + str(numpy.abs(int(frac))) + '.png" scale="true"/>' + '</TD></TR>'
            retLabel += '<TR><TD><FONT color="gray">' + timeStr + ' (' + fracStr + ')</FONT></TD></TR>'
            
        if annotation != None:
            retLabel += '<TR><TD><FONT color="blue">' + annotation + '</FONT></TD></TR>'
    
        retLabel += '</TABLE>>'

        return retLabel
    
    def renderLabel(self, profilerActualDict, nQuery, deltaTuple):

        label = self.attr['label']
        label = label.strip(' ')

        tag = getTag(self.attr, False)

        if 'annotation' in self.attr.keys():
            annotation = self.attr['annotation']
            annotation = annotation.strip(' ')
        else:
            annotation = None
            
        retLabel = self.constructLabel(tag, label, annotation, profilerActualDict, nQuery, deltaTuple)

        if 'tag' not in self.attr.keys():
            self.attr['tag'] = self.attr['label']
            
        self.attr['label'] = retLabel

#=======================================================================
# Class for managing a digraph
#=======================================================================

class DiGraph(Node):

    def __init__(self, attrDict={}):
        self.nodes = []
        self.attr = attrDict
        
        if 'format' in self.attr.keys():
            outputFormat=self.attr['format']
        else:
            outputFormat='png'
            
        self.dg   = gv.Digraph('root', format=outputFormat)
        self.node_attr = {'depth':0, 'frac':-1}
        self.edges = []
        self.profilerSelfDict     = {}
        self.profilerBaselineDict = {}
        self.profilerActualDict   = {}
        self.totalTime = 0
        self.usecPerCount = 0
        self.nQuery = 0
        self.isDelta = False
        self.deltaFrac = False
        self.refUsec = 0.0
        self.threshold = 1000
        
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
            base = 0.0
            if key in self.profilerBaselineDict.keys():
                if isinstance(self.profilerBaselineDict[key], dict):
                    base  = self.profilerBaselineDict[key]['usec']
                else:
                    base = 0.0

            if isinstance(self.profilerActualDict[key], dict):
                usec  = self.profilerActualDict[key]['usec']
                count = self.profilerActualDict[key]['count']

                self.profilerActualDict[key]['corrusec'] = (usec - base) - (self.usecPerCount * count)
                print 'UNCORR key = ' + key + ' val = ' + str(usec) + ' base = ' + str(base) + ' usecpercount = ' + str(self.usecPerCount) + ' count = ' + str(count) + ' CORR = ' + str(self.profilerActualDict[key]['corrusec'])
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
            
    def setArrowhead(self):
        for node in self.nodes:
            node.attr['arrowhead'] = 'none'
            node.setArrowhead('normal')

    def printNodes(self):
        for node in self.nodes:
            node.printNodes()

    def title(self, title):
        self.dg.graph_attr['label'] = self.tabularize(title)
        self.dg.graph_attr['labelloc'] = 't'
        self.dg.graph_attr['fontname'] = 'times'
        self.dg.graph_attr['fontsize'] = '18'

    def tabularize(self, l):
        if not isinstance(l, list):
            ret = l
        else:
            ret = '<<TABLE border="0" cellborder="0">'
            for el in l:
                if isinstance(el, tuple):
                    ret += '<TR><TD><FONT color="' + el[1] + '">' + el[0] + '</FONT></TD></TR>'
                else:
                    ret += '<TR><TD>' + el + '</TD></TR>'
            ret += '</TABLE>>'
        return ret

    def render(self, name):
        self.setDepth()
        self.setShape()
        self.setArrowhead()
        self.setLabels(self.profilerActualDict, self.nQuery, (self.isDelta, self.deltaFrac, self.refUsec, self.threshold))
        self.constructSubgraphs()
        self.connectNodes(self.isDelta)
        self.renderEdgeLabels()
        self.connectEdges()
        self.dg.render(filename=name)

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

    def connectNodes(self, delta=False):
        for node in self.nodes:
            node.connectNodes(self.dg, delta)

    def renderEdgeLabels(self):
        for edge in self.edges:
            attr = edge[2]
            if 'label' in attr.keys():
                tag = attr['label'].strip(' ')
                label = attr['label']
            else:
                tag = ' '
                label = ' '

            if 'color' in attr.keys():
                color = attr['color']

            if 'annotation' in self.attr.keys():
                annotation = self.attr['annotation']
                annotation = annotation.strip(' ')
            else:
                annotation = None

            attr['label'] = self.constructLabel(tag, label, annotation, self.profilerActualDict, self.nQuery, (self.isDelta, self.deltaFrac, self.refUsec, self.threshold), color)

    def connectEdges(self):
        for edge in self.edges:
            if self.isDelta:
                edge[2]['color'] = 'gray'
            self.dg.edge(sanitizeForGraphviz(edge[0]), sanitizeForGraphviz(edge[1]), **edge[2])

    def edge(self, head, tail, attr={}):
        self.edges.append((head, tail, attr))

#=======================================================================
# Global module functions
#=======================================================================

#-----------------------------------------------------------------------
# Sanitize a label to a valid string for graphviz (edge() for example,  interprets
# 'pref:sub' as a particular construct, which we don't want)
#-----------------------------------------------------------------------

def sanitizeForGraphviz(tag):
    return tag.replace(":", "_")

#-----------------------------------------------------------------------
# From a list of sttributes, return a tag if it is present, else a label
#-----------------------------------------------------------------------

def getTag(attr, sanitize=True):
    if 'tag' in attr.keys():
        tag = attr['tag']
    else:
        tag = attr['label']

    if sanitize:
        return sanitizeForGraphviz(tag)
    else:
        return tag

#-----------------------------------------------------------------------
# From a list of lines read from a profiler output file, return a labeled line
#-----------------------------------------------------------------------

def getLine(label, content):
    for line in content:
        if line.split(' ')[0] == label:
            return line.split(' ')
    return []

#-----------------------------------------------------------------------
# Parse a profiler output file
#-----------------------------------------------------------------------

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
            print 'READ LABEL ' + label + ' usec = ' + str(usec[i])
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

#-----------------------------------------------------------------------
# Generate a pie-chart of fractional time
#-----------------------------------------------------------------------

def getTimeStr(timeInUsec, delta=False):
    if numpy.abs(timeInUsec) < 1000:
        ts = str(int(timeInUsec)) + ' &mu;s'
    elif numpy.abs(timeInUsec) < 1000000:
        ts = str('%1.1f' % (float(timeInUsec)/1000)) + ' ms'
    else:
        ts = str(int(float(timeInUsec)/1000000)) + ' s'

    if delta and timeInUsec >= 0.0:
        return '+' + ts
    else:
        return ts

def pieGen(frac, color):
    frac = int(frac)
    colors = [color, 'w']
    fracs = [frac,100-frac]

    fig,ax = pylab.subplots(figsize=(1,1))
    pie = ax.pie(fracs,colors=colors, shadow=False, startangle=90, counterclock=False)

    fname = 'figs/pc_' + str(int(frac)) + '.png'
    pylab.savefig(fname)
    pylab.close(fig)

