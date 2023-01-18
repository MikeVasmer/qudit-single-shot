import networkx as nx
import numpy as np


def build_matching_graph(pcm, p):
    """Function to build a matching graph from a parity check matrix.

    Args:
        pcm (2d numpy array): Parity-check matrix.
        p (float): error probability

    Returns:
        A networkx (matching) graph.
    """
    g = nx.Graph()
    m, _ = pcm.shape
    q = 0
    b = 0
    for col in pcm.T:
        check_indices = [i for i, x in enumerate(col) if x != 0]
        if len(check_indices) == 1:
            g.add_edge(check_indices[0], m + b,
                       fault_ids=q, weight=np.log((1-p)/p))
            b += 1
        elif len(check_indices) == 2:
            g.add_edge(check_indices[0], check_indices[1],
                       fault_ids=q, weight=np.log((1-p)/p))
        else:
            raise ValueError('Each "bit" should be in one or two checks!')
        q += 1
    for i in range(m):
        g.nodes[i]['is_boundary'] = False
    for i in range(b):
        g.nodes[m + i]['is_boundary'] = True
        for j in range(i + 1, b):
            g.add_edge(m + i, m + j, fault_ids=set(), weight=0.0)
    return g
