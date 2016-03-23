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

