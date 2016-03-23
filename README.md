# Synopsis

riak_graphviz is a python library, built on graphviz.py, to make generating graphviz diagrams for erlang easy.

# Examples

To create a new directional graph, and output the result as a .png file:

```python
from riak_graphviz import Node, DiGraph
digraph = DiGraph({'format':'png'})
```
Now we have our main digraph object.  Let's add some nodes to it

```python
node = Node({'label':'module1', 'color': 'red'})
node = Node({'label':'module2', 'color': 'blue'})
digraph.append(node)
```


![alt tag](https://github.com/erikleitch/riak_graphviz/blob/master/img/call_stack.png)

