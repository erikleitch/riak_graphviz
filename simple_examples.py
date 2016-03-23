from riak_graphviz import Node, DiGraph

def graphCallStack(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'some_module', 'color': 'red'})

    node.append(
        (
            {'label': 'module:fn1'},
            {'label': 'module:fn2'},
            {'label': 'module:fn3'},
        )
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphFunctionList(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'some_module', 'color': 'blue'})

    node.append(
        [
            {'label': 'module:fn1'},
            {'label': 'module:fn2'},
            {'label': 'module:fn3'},
        ]
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphBoth(prefix):
    
    digraph = DiGraph({'format':'png'})

    node = Node({'label':'some_module', 'color': 'red'})

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

    node = Node({'label':'some_module', 'color': 'blue'})

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

    node = Node({'label':'some_module', 'color': 'blue'})

    node.setNodeAttr('some_module', 'rank', 'same')

    node.append(
        [
            {'label': 'module:fn1'},
            {'label': 'module:fn2'},
            {'label': 'module:fn3'},
        ]
    )
    
    digraph.append(node)
    digraph.render(prefix)

def graphMultiModule(prefix):
    
    digraph = DiGraph({'format':'png'})

    node1 = Node({'label':'some_module1', 'color': 'red'})

    node1.append(
        (
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            {'label': 'module1:fn3'},
        )
    )

    node2 = Node({'label':'some_module2', 'color': 'blue'})

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

    node1 = Node({'label':'some_module1', 'color': 'red'})

    node1.append(
        (
            {'label': 'module1:fn1'},
            {'label': 'module1:fn2'},
            {'label': 'module1:fn3'},
        )
    )

    node2 = Node({'label':'some_module2', 'color': 'blue'})

    node2.append(
        [
            {'label': 'module2:fn1'},
            {'label': 'module2:fn2'},
            {'label': 'module2:fn3'},
        ]
    )
    
    digraph.append(node1)
    digraph.append(node2)

    digraph.edge('module1:fn1', 'module2:fn3', {'color':'green'})
    
    digraph.render(prefix)

graphCallStack('img/call_stack')
graphFunctionList('img/function_list')
graphBoth('img/both')
graphFunctionListSameRank('img/function_list_same_rank')
graphMultiModule('img/multi_module')
graphMultiModuleWithEdge('img/multi_module_with_edge')


