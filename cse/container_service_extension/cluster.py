# container-service-extension
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import json
import logging

TYPE_MASTER = 'master'
TYPE_NODE = 'node'
LOGGER = logging.getLogger(__name__)
MAX_VMS = 128


class Node(object):

    def __init__(self, name, node_type=TYPE_NODE, node_id='', href=''):
        self.name = name
        self.node_type = node_type
        self.node_id = node_id
        self.href = href
        self.status = ''
        self.ip = ''
        self.cluster_id = ''
        self.cluster_name = ''

    def __repr__(self):
        return self.toJSON()

    def toJSON(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=4)


class Cluster(object):

    def __init__(self, name=None, cluster_id=''):
        self.name = name
        self.cluster_id = cluster_id
        self.master_nodes = []
        self.nodes = []
        self.status = ''

    def update_vm_tags(self, vca):
        for node in self.master_nodes+self.nodes:
            tags = {}
            tags['cse.cluster.id'] = self.cluster_id
            tags['cse.node.type'] = node.node_type
            tags['cse.node.name'] = node.name
            tags['cse.cluster.name'] = self.name
            for k, v in tags.items():
                if len(node.href) > 0:
                    result = vca.add_vapp_metadata(node.href,
                                                   'GENERAL', 'READWRITE',
                                                   k, v)
                    if result is None:
                        LOGGER.error('add metadata, result=%s, '
                                     'name=%s, href=%s, '
                                     'key=%s, value=%s',
                                     result, node.name, node.href, k, v)
                        return False
                    else:
                        LOGGER.info('add metadata, result=%s, '
                                    'name=%s, href=%s, '
                                    'key=%s, value=%s',
                                    True, node.name, node.href, k, v)
        return True

    @staticmethod
    def load_from_metadata(vca, cluster_name=None):
        if cluster_name is None:
            query = 'fields=metadata:cse.cluster.id,' + \
                    'metadata:cse.cluster.name,' + \
                    'metadata:cse.node.type,' + \
                    'metadata:cse.node.name&pageSize=%d' \
                    % MAX_VMS
        else:
            query = 'fields=metadata:cse.cluster.id,' + \
                    'metadata:cse.cluster.name,' + \
                    'metadata:cse.node.type,' + \
                    'metadata:cse.node.name&pageSize=%d' + \
                    'filter=metadata:cse.cluster.id==STRING:%s' \
                    % (MAX_VMS, cluster_name)
        print(query)
        result = vca.query_by_metadata(query)
        nodes = dict()
        clusters = dict()
        if result is not None:
            for r in result.Record:
                if r.get_Metadata() is None:
                    continue
                for entry in r.get_Metadata().get_MetadataEntry():
                    if entry.get_Key() == 'cse.node.name':
                        if entry.get_TypedValue().get_Value() not in nodes:
                            node = Node(entry.get_TypedValue().get_Value())
                            nodes[node.name] = node
                    elif entry.get_Key() == 'cse.cluster.name':
                        if entry.get_TypedValue().get_Value() not in nodes:
                            cluster = Cluster(entry.get_TypedValue().
                                              get_Value())
                            clusters[cluster.name] = cluster
            for r in result.Record:
                if r.get_Metadata() is None:
                    continue
                for entry in r.get_Metadata().get_MetadataEntry():
                    if entry.get_Key() == 'cse.node.type':
                        nodes[r.name].node_type = \
                            entry.get_TypedValue().get_Value()
                        nodes[r.name].href = r.href
                    elif entry.get_Key() == 'cse.cluster.id':
                        nodes[r.name].cluster_id = \
                            entry.get_TypedValue().get_Value()
                    elif entry.get_Key() == 'cse.cluster.name':
                        nodes[r.name].cluster_name = \
                            entry.get_TypedValue().get_Value()

        for key, value in nodes.items():
            if value.node_type == TYPE_MASTER:
                clusters[value.cluster_name].cluster_id = node.cluster_id
                clusters[value.cluster_name].master_nodes.append(value)
            elif value.node_type == TYPE_NODE:
                clusters[value.cluster_name].nodes.append(value)

        return clusters.values()

    def __repr__(self):
        return self.toJSON()

    def toJSON(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=4)