#!/usr/bin/python
import sys
import graphviz as gv
import functools
import numpy

#graph = functools.partial(gv.Graph, format='pdf')
#digraph = functools.partial(gv.Digraph, format='pdf')

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
            nodes.append(l[i])

        sg = gv.Digraph('subgraph_' + str(i))
        sg = add_nodes(sg, nodes)
        sg.graph_attr['rank'] = 'same'

        dg.subgraph(sg)

    # Finally, connect all related lists of nodes

    for l in nodelists:
        connect_nodes(dg, l)
        
    return dg
        
#------------------------------------------------------------
# Start of script
#------------------------------------------------------------

service_color = 'blue'
fsm_color     = 'red'
server_color  = 'cyan'

client_funs = [
    ('client_0',  {'label': 'client',       'color': service_color})
    ]

kvp_funs = [
    ('kvpb_0',  {'label': 'riak_kv_pb_timeseries',       'color': service_color}),
    ('kvpb_1',  {'label': 'process()', 'shape':'rectangle'}),
    ('kvpb_2',  {'label': 'check_table_and_call()'}),
    ('kvpb_3',  {'label': 'sub_tsqueryreq()'}),
    ('kvpb_4',  {'label': 'riak_kv_qry:\n submit()'}),
    ('kvpb_5',  {'label': 'riak_kv_qry:\n maybe_submit_to_queue()'}),
    ('kvpb_7',  {'label': 'riak_kv_qry:\n put_on_queue()'}),
    ('kvpb_8',  {'label': 'riak_kv_qry:\n maybe_await_query_results()'})]

kvqryqueue_funs = [
    ('kvqryqueue_0',  {'label': 'riak_kv_qry_queue',           'color': server_color}),
    ('kvqryqueue_1',  {'label': 'handle_call()'}),
    ('kvqryqueue_2',  {'label': 'do_push_query()'})]

kvqryworker_funs = [
    ('kvqryworker_0',  {'label': 'riak_kv_qry_worker',          'color': server_color}),
    ('kvqryworker_1',  {'label': 'pop_next_query()'}),
    ('kvqryworker_2',  {'label': 'execute_query()'}),
    ('kvqryworker_3',  {'label': 'run_sub_qs_fn()'}),
    ('kvqryworker_4',  {'label': 'riak_kv_index_fsm_sup:\n start_index_fsm()'})]

kvqryworker_funs2 = [
    ('kvqryworker_5',    {'label': '', 'color':'invis'}),
    ('kvqryworker_6',    {'label': 'handle_info()'}),
    ('kvqryworker_7',    {'label': 'subqueries_done()'})]

kvqryworker_funs3 = [
    ('kvqryworker_9',    {'label': '', 'color':'invis'}),
    ('kvqryworker_10',    {'label': '', 'color':'invis'}),
    ('kvqryworker_11',    {'label': 'add_subquery_result()'})]

kvindexfsm_funs = [
    ('kvindexfsm_0',  {'label': 'riak_kv_index_fsm',           'color': fsm_color}),
    ('kvindexfsm_1',  {'label': 'riak_core_coverage_fsm:\n init()'}),
    ('kvindexfsm_2',  {'label': 'riak_core_coverage_fsm:\n initialize()'}),
    ('kvindexfsm_3',  {'label': 'riak_core_vnode_master:\n coverage()'}),
    ('kvindexfsm_4',  {'label': 'riak_core_vnode_master:\n proxy_cast()'}),
    ('kvindexfsm_5',  {'label': 'riak_core_coverage_fsm:\n waiting_results()'}),
    ('kvindexfsm_6',  {'label': 'riak_kv_index_fsm:\nprocess_results()'}),
    ('kvindexfsm_7',  {'label': 'riak_kv_index_fsm:\nfinish()'})]

corevnode_funs = [
    ('corevnode_0',  {'label': 'riak_core_vnode',             'color': fsm_color}),
    ('corevnode_1',  {'label': 'active(?COVERAGE_REQ)'}),
    ('corevnode_2',  {'label': 'vnode_coverage()'}),
#    ('corevnode_3',  {'label': 'riak_kv_vnode:\nhandle_coverage()'}),
#    ('corevnode_4',  {'label': 'riak_kv_vnode:\nhandle_range_scan()'}),
#    ('corevnode_5',  {'label': 'riak_kv_vnode:\nhandle_coverage_range_scan()'}),
    ('corevnode_6',  {'label': 'riak_core_vnode_worker_pool:\nhandle_work()'})]

corevnodeworkerpool_funs = [
    ('corevnodeworkerpool_0',{'label': 'riak_core_vnode_worker_pool', 'color': fsm_color}),
    ('corevnodeworkerpool_1',  {'label': 'ready({work, Work, From})'}),
    ('corevnodeworkerpool_2',  {'label': 'riak_core_vnode_worker:\nhandle_work()'})]

corevnodeworker_funs = [
    ('corevnodeworker_0',  {'label': 'riak_core_vnode_worker',      'color': server_color}),
    ('corevnodeworker_1',  {'label': 'handle_cast({work, Work, WorkFrom, Caller)'}),
    ('corevnodeworker_2',  {'label': 'riak_kv_worker:\nhandle_work()'}),
    ('corevnodeworker_3',  {'label': 'eleveldb:\nfold()'}),
    ('corevnodeworker_4',  {'label': 'riak_kv_vnode:\nresult_fun_ack()'}),
    ('corevnodeworker_5',  {'label': 'riak_core_vnode:\nreply()'})]

dg = createDigraph([client_funs, kvp_funs, kvqryqueue_funs, kvqryworker_funs, kvqryworker_funs2, kvqryworker_funs3, kvindexfsm_funs, corevnode_funs, corevnodeworkerpool_funs, corevnodeworker_funs])

dg.edge('kvqryworker_0', 'kvqryworker_6')
dg.edge('kvqryworker_6', 'kvqryworker_11')

dg.edge('client_0',              'kvpb_1',                '   1', {'color':service_color})
dg.edge('kvpb_7',                'kvqryqueue_1',          '   2', {'color':server_color})
dg.edge('kvqryqueue_2',          'kvqryworker_1',         '   3', {'color':server_color})
dg.edge('kvqryworker_4',         'kvindexfsm_1',          '   4', {'color':fsm_color})
dg.edge('kvindexfsm_4',          'corevnode_1',           '   5', {'color':fsm_color})
dg.edge('corevnode_6',           'corevnodeworkerpool_1', '   6', {'color':fsm_color})
dg.edge('corevnodeworkerpool_2', 'corevnodeworker_1',     '   7', {'color':server_color})
dg.edge('corevnodeworker_5',     'kvindexfsm_5',          '   8', {'color':fsm_color})
dg.edge('kvindexfsm_6',          'kvqryworker_11',        '   9', {'color':server_color})
dg.edge('kvindexfsm_7',          'kvqryworker_7',         '  10', {'color':server_color})
dg.edge('kvqryworker_7',         'kvpb_8',                '  11', {'color':service_color})
dg.edge('kvpb_8',                'client_0',              '  12', {'color':service_color})

dg.render('riak_ts_query')





