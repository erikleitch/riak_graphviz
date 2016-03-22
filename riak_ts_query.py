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

    def connectNodes(self, graph, delta=False):

        # Connect this node to all of its children, and its children to theirs

        attr = {}
        for node in self.nodes:
            if delta:
                attr['color'] = 'gray'
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

    def constructLabel(self, tag, label, profilerActualDict, nQuery, deltaTuple, color=None):

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
            print 'Tag = ' + tag + ' val = ' + str(val) + ' thres = ' + str(threshold) + ' color = green'
        elif delta and val > 0.0:
            self.attr['color'] = 'red'
            pieColor = 'red'
            self.attr['penwidth'] = '2'
            self.attr['style'] = 'filled'
            self.attr['fillcolor'] = 'mistyrose'
            print 'Tag = ' + tag + ' val = ' + str(val) + ' thres = ' + str(threshold) + ' color = red'
            
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
            
        retLabel += '</TABLE>>'

        return retLabel
    
    def renderLabel(self, profilerActualDict, nQuery, deltaTuple):

        label = self.attr['label']
        label = label.strip(' ')

        tag = getTag(self.attr, False)

        retLabel = self.constructLabel(tag, label, profilerActualDict, nQuery, deltaTuple)

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
        self.dg   = gv.Digraph('root')
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
        self.setLabels(self.profilerActualDict, self.nQuery, (self.isDelta, self.deltaFrac, self.refUsec, self.threshold))
        self.constructSubgraphs()
        self.connectNodes(self.isDelta)
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

    def connectNodes(self, delta=False):
        for node in self.nodes:
            node.connectNodes(self.dg, delta)

    def renderEdgeLabels(self):
        for edge in self.edges:
            attr = edge[2]
            tag = attr['label'].strip(' ')
            label = attr['label']

            if 'color' in attr.keys():
                color = attr['color']

            attr['label'] = self.constructLabel(tag, label, self.profilerActualDict, self.nQuery, (self.isDelta, self.deltaFrac, self.refUsec, self.threshold), color)

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
        ts = str(int(float(timeInUsec)/1000)) + ' ms'
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

def addQueryNodes(test):
    
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
                (
                    {'label': 'riak_api_pb_server:send_encoded_message_or_error'},
                    {'label': 'riak_pb_codec:encode'},
                    {'label': 'riak_api_pb_server:send_message'},
                )
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
    test.edge('riak_api_pb_server:send_message',                  'riakc_pb_socket:handle_info',           {'color':server_color, 'label':' 15 '})
    test.edge('gen_server:reply',                                 'gen_server_call1',                      {'color':server_color, 'label':' 16 '})

    return

#-----------------------------------------------------------------------
# Get a digraph object representing the query path
#-----------------------------------------------------------------------

def getQueryDiGraph(outputPrefix,
                    nRecord, nQuery,
                    clientFileName,     serverFileName,
                    clientBaseFileName, serverBaseFileName,
                    clientCompFileName, profilerBaseFileName):
    
    test = DiGraph()
    
    test.nRecord = int(nRecord)
    test.nQuery  = int(nQuery)
    
    test.ingestProfilerOutput(clientFileName,     serverFileName,
                              clientBaseFileName, serverBaseFileName,
                              clientCompFileName, profilerBaseFileName)

    addQueryNodes(test)

    return test

#-----------------------------------------------------------------------
# Make a graph of the query path
#-----------------------------------------------------------------------

def makeQueryGraph(outputPrefix,
                   nRecord, nQuery,
                   clientFileName,     serverFileName,
                   clientBaseFileName, serverBaseFileName,
                   clientCompFileName, profilerBaseFileName):

    test = getQueryDiGraph(outputPrefix,
                           nRecord, nQuery,
                           clientFileName,     serverFileName,
                           clientBaseFileName, serverBaseFileName,
                           clientCompFileName, profilerBaseFileName)

    if test.nRecord > 1:
        recStr = str(test.nRecord) + ' records per query'
    else:
        recStr = str(test.nRecord) + ' record per query'
        
    test.title(['RiakTS Query Path', recStr, getTimeStr(test.totalUsec/test.nQuery) + ' per query'])

    test.render(outputPrefix)

def getQueryDiGraphByConstruction(dirPrefix, optsList, outputPrefix):

    [nRecord, nQuery, useFilter, target] = getOptList(optsList)

    dirName = dirPrefix + '/ts_query_' + str(nRecord) + '_' + str(nQuery)
    if useFilter != None:
        dirName = dirName + '_' + str(useFilter)
    if target != None:
        dirName = dirName + '_' + str(target)

    dirName = dirName + '_output'
            
    clientFileName = dirName + '/client.txt'
    serverFileName = dirName + '/server.txt'

    clientBaseFileName = dirName + '/clientbase.txt'
    serverBaseFileName = dirName + '/serverbase.txt'

    clientCompFileName   = dirName + '/clientcomp.txt'
    profilerBaseFileName = dirName + '/profbase.txt'
    
    graph = getQueryDiGraph(outputPrefix,
                            nRecord, nQuery,
                            clientFileName,     serverFileName,
                            clientBaseFileName, serverBaseFileName,
                            clientCompFileName, profilerBaseFileName)
    return graph

#-----------------------------------------------------------------------
# Difference two digraphs
#-----------------------------------------------------------------------

def hasKey(d, key):
    if key in d.keys():
        return 'True'
    else:
        return 'False'

def getOptList(optList):
    useFilter=None
    target=None
    if len(optList) == 2:
        [nRecord, nQuery] = optList
    elif len(optList) == 3:
        [nRecord, nQuery, useFilter] = optList
    elif len(optList) == 4:
        [nRecord, nQuery, useFilter, target] = optList

    if useFilter != None:
        if useFilter:
            useFilter = 'true'
        else:
            useFilter = 'false'
            
    return [nRecord, nQuery, useFilter, target]

def getDeltaStr(list1, list2):

    [nRecord1, nQuery1, useFilter1, target1] = getOptList(list1)
    [nRecord2, nQuery2, useFilter2, target2] = getOptList(list2)

    deltaStr = str(nRecord2)
    openBrace = False
    if useFilter2 != None:
        deltaStr = deltaStr + ' (filter = ' + str(useFilter2)
        openBrace = True
    if target2 != None:
        if ~openBrace:
            deltaStr += '('
        else:
            deltaStr += ', '
        deltaStr = deltaStr + ', ' + target2

    if openBrace:
        deltaStr = deltaStr + ')'        

    deltaStr = deltaStr  + ' &rarr; '

    deltaStr = deltaStr + str(nRecord1)
    openBrace = False
    if useFilter1 != None:
        deltaStr = deltaStr + ' (filter = ' + str(useFilter1)
        openBrace = True
    if target1 != None:
        deltaStr = deltaStr + ', ' + target2
        if ~openBrace:
            deltaStr += '('
        else:
            deltaStr += ', '

    if openBrace:
        deltaStr = deltaStr + ')'        

    return deltaStr
    
def makeDiffGraph(dirPrefix, list1, list2, outputPrefix, deltaFrac, threshold):

    graph1 = getQueryDiGraphByConstruction(dirPrefix, list1, outputPrefix)
    graph2 = getQueryDiGraphByConstruction(dirPrefix, list2, outputPrefix)

    #------------------------------------------------------------
    # Construct delta string
    #------------------------------------------------------------
    
    deltaStr = getDeltaStr(list1, list2)
    
    deltaTimeStr = '&Delta;t = ' + getTimeStr(graph1.totalUsec/(graph1.nQuery) - graph2.totalUsec/(graph2.nQuery), True)

    delta = graph1.totalUsec/(graph1.nQuery) - graph2.totalUsec/(graph2.nQuery)
    if delta < 0:
        color = 'darkgreen'
    else:
        color = 'red'
        
    graph1.title(['RiakTS Query Path', deltaStr + ' records per query', (deltaTimeStr + ' per query', color)])

    for key in graph1.profilerActualDict.keys():
        if isinstance(graph1.profilerActualDict[key], dict):
            print 'Key = ' + key + ' t1 = ' + str(graph1.profilerActualDict[key]['corrusec']/graph1.nQuery)
            print 'Key = ' + key + ' t2 = ' + str(graph2.profilerActualDict[key]['corrusec']/graph2.nQuery)
            graph1.profilerActualDict[key]['corrusec'] = graph1.profilerActualDict[key]['corrusec']/graph1.nQuery - graph2.profilerActualDict[key]['corrusec']/graph2.nQuery
            graph1.profilerActualDict[key]['frac'] = graph1.profilerActualDict[key]['frac'] - graph2.profilerActualDict[key]['frac']

    graph1.refUsec   = graph1.totalUsec/graph1.nQuery
    graph1.threshold = threshold
    graph1.isDelta   = True
    graph1.deltaFrac = deltaFrac

    graph1.nQuery    = 1

                        
    graph1.render(outputPrefix)

def doit():
#    makeDiffGraph('/Users/eml/projects/riak/riak_test/riak_test_query/', [1, 10000], [100, 1000], 'ts_query_100-1')
#    makeDiffGraph('/Users/eml/projects/riak/riak_test/riak_test_query/', [100, 1000], [1000, 1000], 'ts_query_1000-100')
#    makeDiffGraph('/Users/eml/projects/riak/riak_test/riak_test_query/', [1000, 1000],               [1,   10000], 'ts_query_1000-1', True, 1.0)
#    makeDiffGraph('/Users/eml/projects/riak/riak_test/riak_test_query/', [1000, 1000,  'uc_debug7'], [1000, 1000], 'ts_query_1000_ttb-1000', False, 1000.0)
    makeDiffGraph('/Users/eml/projects/riak/riak_test/riak_test_query/', [1000, 1000,  True], [1000, 1000], 'ts_query_1000_filter-none', False, 1000.0)

doit()
