#!/usr/bin/python
import sys
import graphviz as gv
import functools
import numpy
import pylab

globalLabelDict = {}
globalTotalTime = 0

#graph = functools.partial(gv.Graph, format='pdf')
#digraph = functools.partial(gv.Digraph, format='pdf')

def parseTest():
    global globalLabelDict
    parseProfilerOutput('client.txt')
    parseProfilerOutput('server.txt')
    return globalLabelDict
        
def parseProfilerOutput(fileName, labelDict):

    with open(fileName) as f:
        content = f.readlines()

    nline = len(content)

    if nline == 2:
        labels = content[0].split(' ')
        vals   = content[1].split(' ')
        for i in range(2, len(labels)):
            label = labels[i].replace("'", "")
            label = label.replace("\n", "")
            labelDict[label] = float(vals[i-1])
            
    return float(vals[1]), labelDict

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

    if label in globalLabelDict.keys():
        frac = 100 * float(globalLabelDict[label])/globalTotalTime
        print 'Found frac = ' + str(frac) + ' for label = ' + label
        
    if frac > 0:
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

    if frac > 0:
        retLabel += '<TR><TD width="30" height="30" fixedsize="true">' + '<IMG SRC="figs/pc_' + str(int(frac)) + '.png" scale="true"/>' + '</TD></TR>'

    retLabel += '</TABLE>>'
    
    return retLabel

def add_nodes(graph, nodes):
    for n in nodes:
        if isinstance(n, tuple):
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
        
def makePlots(clientFileName, serverFileName, clientBaseFileName, serverBaseFileName):

    global globalLabelDict
    global globalTotalTime

    baseLabelDict = {}

    globalTotalTime, baseLabelDict = parseProfilerOutput(serverBaseFileName, baseLabelDict)
    globalTotalTime, baseLabelDict = parseProfilerOutput(clientBaseFileName, baseLabelDict)
    
    globalTotalTime, globalLabelDict = parseProfilerOutput(serverFileName, globalLabelDict)
    globalTotalTime, globalLabelDict = parseProfilerOutput(clientFileName, globalLabelDict)

    #------------------------------------------------------------
    # Subtract off baselines
    #------------------------------------------------------------

    for key in baseLabelDict.keys():
        if key in globalLabelDict.keys():
            globalLabelDict[key] -= baseLabelDict[key]
    
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
        ('kvpb2_10',   {'label': labelWpix(0,'riak_kv_qry_queue:put_on_queue')}),
        ('kvpb2_11',   {'label': labelWpix(0,'gen_server:call')})]

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
        ('kvpb6_11',  {'label': labelWpix(0,'riak_kv_qry:maybe_await_query_results')})]
    
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
        corevnode_funs,
        corevnodeworkerpool_funs,
        corevnodeworker_funs,
        corevnodeworker1_funs,
        corevnodeworker2_funs])

    ortho = False
    #ortho = True

    if ortho:
        lab = 'xlabel'
    else:
        lab = 'label'

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
    dg.edge('kvpb10_10', 'kvpb2_10')
    dg.edge('kvpb10_10', 'kvpb6_11')
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

    dg.edge('corevnodeworker_2', 'corevnodeworker1_3')
    dg.edge('corevnodeworker_2', 'corevnodeworker2_4')

    dg.edge('riakc_3',               'riakpb_2',              '', {'color':server_color, lab:'    1 '})
    dg.edge('riakpb4_4',             'kvpb_1',                '', {'color':fsm_color,    lab:'    2 '})
    dg.edge('kvpb2_11',              'kvqryqueue_2',          '', {'color':server_color, lab:'    3 '})
    dg.edge('kvqryqueue_3',          'kvqryworker1_2',        '', {'color':server_color, lab:'    4 '})
    dg.edge('kvqryworker4_6',        'kvindexfsm_0',          '', {'color':fsm_color,    lab:'    5 '})
    dg.edge('kvindexfsm4_4',         'corevnode_1',           '', {'color':fsm_color,    lab:'    6 '})
    dg.edge('corevnode_7',           'corevnodeworkerpool_2', '', {'color':fsm_color,    lab:'    7 '})
    dg.edge('corevnodeworkerpool_3', 'corevnodeworker_2',     '', {'color':server_color, lab:'    8 '})
    dg.edge('corevnodeworker2_5',    'kvindexfsm2_2',         '', {'color':fsm_color,    lab:'    9 '})
    dg.edge('kvindexfsm2_2',         'kvqryworker3_2',        '', {'color':server_color, lab:'   10 '})
    dg.edge('corevnodeworker2_5',    'kvindexfsm3_2',         '', {'color':fsm_color,    lab:'   11 '})
    dg.edge('kvindexfsm3_2',         'kvqryworker2_2',        '', {'color':server_color, lab:'   12 '})
    dg.edge('kvqryworker2_2',        'kvpb6_11',              '', {'color':server_color, lab:'   13 '})
    dg.edge('kvpb1_6',               'riakpb_5',              '', {'color':server_color, lab:'   14 '})
    dg.edge('riakpb5_4',             'riakc_3',               '', {'color':server_color, lab:'   15 '})
    
    if ortho:
        dg.graph_attr['splines'] = 'ortho'
    
    dg.render('riak_ts_query')
    
    return dg

makePlots('client.txt', 'server.txt', 'clientbase.txt', 'serverbase.txt')



