# Synopsis

riak_graphviz is a python library, built on graphviz.py, to make generating graphviz diagrams for erlang easy.

# Examples

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
```Node.append()``` function.

## Creating a call stack

```Node.append``` has flexible syntax: a tuple of values (i.e., ```(val1, val2,
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

## Creating a function list

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

## Nested node appends

Calls to ```append`` can be made sequentially on a node, or any
supported syntax may be arbitrarily nested.  Thus the following code
creates a call-stack of functions, the last of which itself calls
a list of three sub-functions:

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
