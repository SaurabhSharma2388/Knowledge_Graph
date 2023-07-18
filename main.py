from flask import Flask, render_template, request
import openai
import networkx as nx
import matplotlib

matplotlib.use('Agg')  # Use the Agg backend

import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['DEBUG'] = True

# Set the maximum number of nodes and edges to limit the graph complexity
MAX_NODES = 100
MAX_EDGES = 200


@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
    return render_template('index.html')
  elif request.method == 'POST':
    url = request.form['url']
    openai.api_key = request.form['api_key']
    response = openai.Completion.create(
      engine='text-davinci-003',
      prompt=f"Generate a knowledge graph for {url}.",
      max_tokens=200,
      temperature=0.5,
      n=1,
      stop=None,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0)

    if len(response.choices) > 0:
      graph = response.choices[0].text.strip()
      graph = graph.replace(": ", ":\n")
      graph = graph.replace("- ", "-\n")
      graph = graph.split("\n")

      graph_data = convertGraphToTree(graph)

      # Limit the number of nodes and edges in the graph
      graph_data = limitGraphComplexity(graph_data, MAX_NODES, MAX_EDGES)

      # Generate the graph image
      fig, ax = plt.subplots(figsize=(20, 6), dpi=72)
      pos = nx.spring_layout(graph_data)
      nx.draw(graph_data, pos, with_labels=True, ax=ax)

      # Convert the graph image to base64 format
      buffer = BytesIO()
      plt.savefig(buffer, format='jpeg')
      buffer.seek(0)
      image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

      plt.close(fig)

      return render_template('result.html',
                             graph_data=graph_data,
                             image_base64=image_base64)

  return render_template('error.html',
                         message='Failed to generate the knowledge graph.')


def convertGraphToTree(graph):
  G = nx.DiGraph()
  for item in graph:
    if "->" in item:
      source, target = item.split("->")
      G.add_edge(source.strip(), target.strip())
  return G


def limitGraphComplexity(graph, max_nodes, max_edges):
  if graph.number_of_nodes() > max_nodes:
    # Remove nodes exceeding the maximum limit
    nodes_to_remove = list(graph.nodes())[max_nodes:]
    graph.remove_nodes_from(nodes_to_remove)

  if graph.number_of_edges() > max_edges:
    # Remove edges exceeding the maximum limit
    edges_to_remove = list(graph.edges())[max_edges:]
    graph.remove_edges_from(edges_to_remove)

  return graph


app.run(debug=True)
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
