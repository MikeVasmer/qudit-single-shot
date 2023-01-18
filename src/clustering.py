from dataclasses import dataclass
from anytree import Node, Walker
from typing import Dict, List, Tuple
import networkx as nx
import numpy as np
import random


@dataclass
class Cluster:
    """Cluster dataclass.

    Args:
        root (Node): root node of the cluster (tree).
        charge (int): total charge of the cluster.
        charged_nodes (List[Node]): charged nodes of the cluster.
        size (int): number of nodes in the cluster.
        boundary (bool): whether the cluster contains the boundary node.
    """
    root: Node
    charge: int
    charged_nodes: List[Tuple[Node, int]]
    size: int = 1
    boundary: bool = False


class Clustering:
    def __init__(self, pcm, decoding_graph, num_faults, local_dim, cutoff):
        self.pcm = pcm  # parity-check matrix
        self.decoding_graph = decoding_graph
        self.num_faults = num_faults
        self.local_dim = local_dim
        self.cutoff = cutoff

    def re_root(self, new_root: Node):
        """Re-root a tree.

        Args:
            new_root (Node): node to make the root.
        """
        ancestors = new_root.ancestors
        new_root.parent = None  # Disconnect
        # Reverse the original path from new_root to old_root
        v = new_root
        for node in reversed(ancestors):
            node.parent = v
            v = node

    def init_nodes(self, graph: nx.Graph):
        """Initialize nodes dictionary.

        Args:
            graph (networkx.Graph) decoding graph.
        """
        nodes = {}
        for v in graph:
            nodes[v] = Node(name=v)
        return nodes

    def graph_neighbors(self, node: Node, graph: nx.Graph) -> List[int]:
        """Get neighboring nodes according to a graph.

        Args:
            node (Node): node.
            graph (networkx.Graph): adjacency graph.

        Returns:
            A list of the neighboring node indices.
        """
        vertex = int(node.name)
        return [n for n in graph.neighbors(vertex)]

    def init_clusters(self, charge_data: List[Tuple[int]], nodes: Dict[int, Node]):
        """Create a cluster for each charge.

        Args:
            charge_data (List[Tuple[int]]): list of tuples of the index of the charged vertices and their charges.
            nodes (Dict[int, Node]): map from (vertex) indices to nodes.
        """
        clusters = {}
        for ci, cv in charge_data:
            cluster_root = nodes[ci]
            cluster = Cluster(root=cluster_root, charge=cv,
                              charged_nodes=[(cluster_root, cv)])
            clusters[cluster_root] = cluster
        return clusters

    def grow_clusters(self, clusters: Dict[int, Cluster], nodes: Dict[int, Node], boundary_index: int):
        """Attempt to grow each cluster one step and return clusters that need to be merged.

        Args:
            clusters (Dict[int, Cluster]): map from cluster tree roots to cluster objects.
            nodes (Dict[int, Node]): map from (vertex) indices to nodes.
            boundary_index (int): index of (min index) boundary node

        Returns:
            A list of merge data, each item formatted as [root of larger cluster, merge node (currently in smaller cluster), planned parent of merge node in larger cluster].
        """
        merge_list = []
        merge_pairs = []
        for root, cluster in clusters.items():
            # Don't grow neutral or boundary clusters
            if cluster.charge == 0 or cluster.boundary == True:
                continue
            for leaf in root.leaves:
                if leaf.name >= boundary_index:
                    continue
                neighbors = self.graph_neighbors(leaf, self.decoding_graph)
                for index in neighbors:
                    node = nodes[index]
                    # If node is a boundary node
                    if index >= boundary_index:
                        # and cluster does not already contain a boundary node
                        if not cluster.boundary:
                            cluster.boundary = True
                            node.parent = leaf
                    # If node is already in the cluster continue
                    elif node.root == root:
                        continue
                    else:
                        # If node is not in any cluster add it
                        if node.parent == None and node not in clusters.keys():
                            node.parent = leaf
                        # If node is part of neutral cluster skip it
                        elif clusters[node.root].charge == 0:
                            continue
                        else:
                            # If these clusters have already been merged don't merge again
                            if (node.root, root) in merge_pairs or (root, node.root) in merge_pairs:
                                pass
                            # Weighted merge (union)
                            else:
                                if cluster.size >= clusters[node.root].size:
                                    merge_list += [[node, leaf]]
                                else:
                                    merge_list += [[leaf, node]]
                                merge_pairs.append((root, node.root))
                                # If the merged cluster has charge = 0 stop growing
                                if (cluster.charge + clusters[node.root].charge) % self.local_dim == 0:
                                    cluster.charge = 0
                                    clusters[node.root].charge = 0
                                    break
            cluster.size = len(root.descendants) + 1
        return merge_list

    def merge_clusters(self, merge_node: Node, merge_parent: Node, clusters: Dict[int, Cluster]):
        """Merge two clusters.

        Args:
            merge_node (Node): node in the smaller cluster to be attached to the larger cluster.
            merge_parent (Node): planned parent of merge_node in the larger cluster.
            clusters (Dict[int, Cluster]): map from cluster tree roots to cluster objects.
        """
        root = merge_parent.root
        small_root = merge_node.root
        # This function might be called on already merged clusters
        if root != small_root:
            cluster = clusters[root]
            small_cluster = clusters[small_root]
            self.re_root(merge_node)
            merge_node.parent = merge_parent
            cluster.charged_nodes += small_cluster.charged_nodes
            # cluster.charge = (cluster.charge +
            #   small_cluster.charge) % local_dim
            cluster.charge = 0
            for _, charge in cluster.charged_nodes:
                cluster.charge += charge
            cluster.charge = cluster.charge % self.local_dim
            cluster.size = len(root.descendants) + 1
            clusters.pop(small_root, None)  # Remove the small cluster

    def neutralize_clusters(self, clusters: Dict[int, Cluster], boundary_index: int):
        """Compute a correction for a list of neutral clusters.

        Args:
            clusters (Dict[int, Cluster]): map from cluster tree roots to cluster objects.
            boundary_index (int): the index of the boundary vertex.

        Returns:
            A correction operator.
        """
        corr = np.zeros(self.num_faults, dtype=np.int32)
        for root, cluster in clusters.items():
            if cluster.charge == 0:
                target = root
            elif cluster.boundary == True:
                target = [
                    node for node in root.descendants if node.name >= boundary_index][0]
            else:
                continue
            w = Walker()
            for c_node, charge in cluster.charged_nodes:
                tmp = w.walk(c_node, target)
                # The return format here is stupid so we flatten it
                path = [list(tmp[0]) + [tmp[1]] + list(tmp[2])][0]
                for i in range(len(path) - 1):
                    current = int(path[i].name)
                    next = int(path[i+1].name)
                    index = self.decoding_graph[current][next]['fault_ids']
                    sign = -self.pcm[current][index]
                    corr[index] = (corr[index] + sign *
                                   charge) % self.local_dim
        return corr

    def decode(self, syndrome):
        """Clustering decoder.

        Args:
            syndrome (numpy.array): syndrome vector.
            h (numpy.array): parity-check matrix.
            graph (networkx.Graph): decoding graph.
            num_faults (int): the number of faults.
            local_dim (int): the local qudit dimension.
            cutoff (int): maximum number of growth steps.

        Returns:
            A correction operator.
        """
        cluster_indices = np.nonzero(syndrome)[0]
        cluster_charges = [syndrome[i] for i in cluster_indices]
        boundary_index = len(syndrome)
        nodes = self.init_nodes(self.decoding_graph)
        clusters = self.init_clusters(
            zip(cluster_indices, cluster_charges), nodes)
        corr = np.zeros((self.num_faults), dtype=np.int32)
        tmp = list(clusters.items())
        random.shuffle(tmp)  # Crucial to avoid biasing X vs Z!
        clusters = dict(tmp)
        for _ in range(self.cutoff):
            if not clusters:  # True if clusters is empty
                break
            merge_list = self.grow_clusters(clusters, nodes, boundary_index)
            for pair_data in merge_list:
                self.merge_clusters(*pair_data, clusters)
            neutral_roots = []
            for root, cluster in clusters.items():
                if cluster.boundary == True or cluster.charge == 0:
                    neutral_roots += [root]
            if len(neutral_roots) > 0:
                corr = np.mod(corr + self.neutralize_clusters(
                    clusters, boundary_index), self.local_dim)
                for root in neutral_roots:
                    for node in root.descendants:
                        node.parent = None
                        clusters.pop(root, None)
        return corr
