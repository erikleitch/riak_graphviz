from riak_graphviz import Node, DiGraph

def graphModules(prefix):
    
    digraph = DiGraph({'format':'png'})

    node1 = Node({'label': 'module1', 'color': 'red'})
    node2 = Node({'label': 'module2', 'color': 'blue'})

    digraph.append(node1)
    digraph.append(node2)
    digraph.render(prefix)

def graphCallStack(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'module1', 'color': 'blue'})

    node.append(
        (
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            {'label': 'module1:fn3'},
        )
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphFunctionList(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'module1', 'color': 'blue'})

    node.append(
        [
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            {'label': 'module1:fn3'},
        ]
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphBoth(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'module1', 'color': 'blue'})

    node.append(
            (
                {'label': 'module1:fn1'},
                {'label': 'module1:fn2'},
                {'label': 'module1:fn3'},
            )
    )            

    node.append(
        [
                {'label': 'module2:fn1'},
                {'label': 'module2:fn2'},
                {'label': 'module2:fn3'},
        ]
    )

    digraph.append(node)
    digraph.render(prefix)

def graphFunctionList(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'module1', 'color': 'blue'})

    node.append(
        [
            {'label': 'module:fn1'},
            {'label': 'module:fn2'},
            {'label': 'module:fn3'},
        ]
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphFunctionListSameRank(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'module1', 'color': 'blue'})

    node.setNodeAttr('module1', 'rank', 'same')

    node.append(
        [
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            {'label': 'module1:fn3'},
        ]
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphNested(prefix):
    digraph = DiGraph({'format':'png'})
    
    node = Node({'label':'module1', 'color': 'blue'})
    node.append(
      (
        {'label': 'module1:fn1'},
	{'label': 'module1:fn2'},
	(
	  {'label': 'module1:fn3'},
	  [	  
	    {'label': 'module1:fn3_1'},
	    {'label': 'module1:fn3_2'},
	    {'label': 'module1:fn3_3'},
	  ]
	),
      )
    )
    digraph.append(node)
    digraph.render(prefix)

def graphMultiModule(prefix):
    
    digraph = DiGraph({'format':'png'})

    node1 = Node({'label':'module1', 'color': 'red'})

    node1.append(
        (
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
        )
    )

    node2 = Node({'label':'module2', 'color': 'blue'})

    node2.append(
        [
            {'label': 'module2:fn1'},
            {'label': 'module2:fn2'},
            {'label': 'module2:fn3'},
        ]
    )
    
    digraph.append(node1)
    digraph.append(node2)
    
    digraph.render(prefix)

def graphMultiModuleWithEdge(prefix):
    
    digraph = DiGraph({'format':'png'})

    node1 = Node({'label':'module1', 'color': 'red'})

    node1.append(
        (
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
        )
    )

    node2 = Node({'label':'module2', 'color': 'blue'})

    node2.append(
        [
            {'label': 'module2:fn1'},
            {'label': 'module2:fn2'},
            {'label': 'module2:fn3'},
        ]
    )
    
    digraph.append(node1)
    digraph.append(node2)
    
    digraph.edge('module2:fn3', 'module1:fn3_3', {'color':'green'})
    
    digraph.render(prefix)

def graphMultiModuleWithAttr(prefix):
    
    digraph = DiGraph({'format':'png'})

    node1 = Node({'label':'module1', 'color': 'red'})

    node1.append(
        (
            {'label': 'module1:fn1', 'color':'darkgreen'},
            {'label': 'module1:fn2'},
            ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
        )
    )

    node2 = Node({'label':'module2', 'color': 'blue'})

    node2.append(
        [
            {'label': 'module2:fn1'},
            {'label': 'module2:fn2', 'style':'filled', 'fillcolor':'mistyrose'},
            {'label': 'module2:fn3'},
        ]
    )
    
    digraph.append(node1)
    digraph.append(node2)
    
    digraph.edge('module2:fn3', 'module1:fn3_3', {'color':'green', 'dir':'both'})
    
    digraph.render(prefix)

graphModules('img/modules')
graphCallStack('img/call_stack')
graphFunctionList('img/function_list')
graphNested('img/nested')
graphBoth('img/both')
graphFunctionListSameRank('img/function_list_same_rank')
graphMultiModule('img/multi_module')
graphMultiModuleWithEdge('img/multi_module_with_edge')
graphMultiModuleWithAttr('img/multi_module_with_attr')


