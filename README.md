# Synopsis

riak_graphviz is a python library, built on graphviz.py, intended to
simplify generating diagrams for complex processes.  The primary
functionality it adds to graphviz.py is ease of construction of
complicated call stacks, and logical ordering of nodes through the use
of subgraphs under the hood.

You'll need graphviz installed to use this code, which you can get,
for example, via:

```pip install graphviz```

or see the official graphviz site for other download options: http://www.graphviz.org.

Extensive (but weirdly awkward to navigate) documentation about
graphviz can be found at the official graphviz site:
http://www.graphviz.org/Documentation.php

# <a name="examples">Examples</a>

* <a href="#digraph">Creating a Digraph</a>
* <a href="#callstack">Graphing a call stack</a>
* <a href="#fnlist">Graphing a function list</a>
* <a href="#nested">Nested node appends</a>
* <a href="#multi">Multiple modules</a>
* <a href="#edges">Edges</a>
* <a href="#attr">Attributes</a>
* <a href="#convenience">Convenience methods</a>

## <a name="digraph">Creating a Digraph</a>
Back to <a href="#examples">Examples</a>

To create a new directional graph, and output the result as a .png file:

```python
from riak_graphviz import Node, DiGraph
digraph = DiGraph({'format':'png'})
```
Now we have our main digraph object.  Let's add some nodes to it and render it:

```python
node1 = Node({'label':'module1', 'color': 'red'})
digraph.append(node1)

node2 = Node({'label':'module2', 'color': 'blue'})
digraph.append(node2)

digraph.render('img/modules.png')

```

All top-level nodes appended to a digraph are treated as modules, and
given the same rank, so when the plot is rendered, it will look like this:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/modules.png)

Each node object can have its own hierarchy of nodes.  You can
construct this hierarchy by appending to the nodes themselves, via the
```Node.append()``` function, as detailed below:

## <a name="callstack">Graphing a call stack</a>
Back to <a href="#examples">Examples</a>

```Node.append()``` takes a single argument with a flexible syntax: a tuple of values (i.e., ```(val1, val2,
val3)```) is interpreted as a call-stack, i.e., a set of nodes
representing functions that call each other in turn, so the following code:

```python
digraph = DiGraph({'format':'png'})
node = Node({'label':'module1', 'color': 'red'})
node.append(({'label': 'module:fn1'}, {'label': 'module:fn2'}, {'label': 'module:fn3'}))
digraph.append(node)
```

produces this diagram:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/call_stack.png)

## <a name="fnlist">Graphing a function list</a>
Back to <a href="#examples">Examples</a>

On the other hand, a list of values (i.e., ```[val1, val2, val3]```)
is interpreted as a simple list of functions, i.e., a set of nodes
representing functions that are called by the same function, one after
the other.  Thus the following code:

```python
digraph = DiGraph({'format':'png'})
node = Node({'label':'module1', 'color': 'red'})
node.append([{'label': 'module:fn1'}, {'label': 'module:fn2'}, {'label': 'module:fn3'}])
digraph.append(node)
```

produces this diagram:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/function_list.png)

where the rank of the nodes indicates the order in which the functions
are called (assumed to be represented by the order of the function in
the list).  Setting the ```rank``` attribute to ```same``` for any
node changes this behavior to put every list element at the same rank.
Thus the following code

```python
digraph = DiGraph({'format':'png'})
node = Node({'label':'module1', 'color': 'red'})
node.append([{'label': 'module:fn1'}, {'label': 'module:fn2'}, {'label': 'module:fn3'}])
node.setNodeAttr('module1', 'rank', 'same')
digraph.append(node)
```

produces this diagram instead:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/function_list_same_rank.png)

## <a name="nested">Nested node appends</a>
Back to <a href="#examples">Examples</a>

Calls to ```append``` can be made sequentially on a node, or any
supported syntax may be arbitrarily nested.  Thus the following code
creates a call-stack of functions, the last of which is itself another
call-stack, consisting of a function calling three sub-functions:

```python
    node = Node({'label':'module1', 'color': 'blue'})
    node.append(
      (
        {'label': 'module1:fn1'},
        {'label': 'module1:fn2'},
        ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
      )
    )
    digraph.append(node)
```
producing this diagram:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/nested.png)

## <a name="multi">Multiple modules</a>
Back to <a href="#examples">Examples</a>

Putting it all together, we can create a digraph with multiple modules
by instantiating separate nodes:

```python
node1 = Node({'label':'module1', 'color': 'red'})
node2 = Node({'label':'module2', 'color': 'blue'})
```

Each one can be configured as desired and appended to the digraph:

```python
node1.append(
  (
    {'label': 'module1:fn1'},
    {'label': 'module1:fn2'},
    ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
  )
)

node2.append([{'label': 'module2:fn1'}, {'label': 'module2:fn2'}, {'label': 'module2:fn3'}])
node2.setNodeAttr('module1', 'rank', 'same')

digraph.append(node1)
digraph.append(node2)
```
producing this diagram:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/multi_module.png)

## <a name="edges">Edges</a>
Back to <a href="#examples">Examples</a>

Edges can be added between arbitrary nodes by using the ```DiGraph.edge()``` function:

```python
digraph.edge('module2:fn3', 'module1:fn3_3', {'color':'green'})
```

would produce the following output:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/multi_module_with_edge.png)

## <a name="attr">Attributes</a>
Back to <a href="#examples">Examples</a>

The dictionary passed with a node or edge definition can contain any of the supported graphviz attributes.  Thus the following code:

```python
node1 = Node({'label':'module1', 'color': 'red'})
node2 = Node({'label':'module2', 'color': 'blue'})

node1.append(
  (
    {'label': 'module1:fn1', 'color':'darkgreen'},
    {'label': 'module1:fn2'},
    ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
  )
)

node2.append(
  [
    {'label': 'module2:fn1'},
    {'label': 'module2:fn2',  'style':'filled', 'fillcolor':'mistyrose'},
    {'label': 'module2:fn3'}
  ]
)
node2.setNodeAttr('module1', 'rank', 'same')

digraph.edge('module2:fn3', 'module1:fn3_3', {'color':'green', 'dir':'both', 'label':'gen_server:send'})

digraph.append(node1)
digraph.append(node2)
```

produces the following diagram:

![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/multi_module_with_attr.png)

NB: Graphviz attributes are documented at http://soc.if.usp.br/manual/graphviz/html/info/attrs.html.

## <a name="convenience">Convenience methods</a>
Back to <a href="#examples">Examples</a>

Constructing complicated calling sequences with a single call to
```Node.append()``` can be challenging to get right.  riak_graphviz provides some convenience methods to make this easier.

For example, the following code:

```python

    # Construct a single sequence all at one go:

    node = Node({'label':'module1', 'color': 'blue'})
    node.append(
      (
        {'label': 'module1:fn1'},
        {'label': 'module1:fn2'},
        ({'label': 'module1:fn3'}, [{'label': 'module1:fn3_1'}, {'label': 'module1:fn3_2'}, {'label': 'module1:fn3_3'}]),
      )
    )
    digraph.append(node)
```

and this code:

```python

    # Construct a single node
    
    node1 = Node({'label':'module1', 'color': 'blue'})
    node1.append({'label': 'module1:fn1'})

    # Construct another node
    
    node2 = Node({'label': 'module1:fn3'})
    node2.append([{'label':'module1:fn3_1'}, {'label':'module1:fn3_3'}])

    # Now append node2 to node1
    
    node1.appendTo('module1:fn1', node2)

    # Now insert on node1
    
    node1.insertBetween('module1:fn1', 'module1:fn3', {'label':'module:fn2'})
    node1.insertBetween('module1:fn3_1', 'module1:fn3_3', {'label':'module:fn3_2'})

    digraph.append(node1)
```

 both produce the same diagram below:
 
![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/nested2.png)
