# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
"""
Definition of RethinkDB queries used by the RethinkDB integration.

Useful reference documentation:
- Python ReQL command reference: https://rethinkdb.com/api/python/
- Usage of `eq_join`: https://rethinkdb.com/api/python/eq_join/
"""

from __future__ import absolute_import

from typing import Iterator, Tuple

import rethinkdb
from rethinkdb import r

from ._types import (
    ClusterStats,
    Job,
    JoinRow,
    ReplicaStats,
    Server,
    ServerStats,
    ServerStatus,
    ShardReplica,
    Table,
    TableStats,
    TableStatus,
)


def query_cluster_stats(conn):
    # type: (rethinkdb.net.Connection) -> ClusterStats
    """
    Retrieve statistics about the cluster.
    """
    return r.db('rethinkdb').table('stats').get(['cluster']).run(conn)


def query_servers_with_stats(conn):
    # type: (rethinkdb.net.Connection) -> Iterator[Tuple[Server, ServerStats]]
    """
    Retrieve each server in the cluster along with its statistics.
    """
    # For servers: stats['id'] = ['server', '<SERVER_ID>']
    is_server_stats_row = r.row['id'].nth(0) == 'server'
    server_id = r.row['id'].nth(1)

    stats = r.db('rethinkdb').table('stats')
    server_config = r.db('rethinkdb').table('server_config')

    rows = stats.filter(is_server_stats_row).eq_join(server_id, server_config).run(conn)  # type: Iterator[JoinRow]

    for row in rows:
        server_stats = row['left']  # type: ServerStats
        server = row['right']  # type: Server
        yield server, server_stats


def query_tables_with_stats(conn):
    # type: (rethinkdb.net.Connection) -> Iterator[Tuple[Table, TableStats]]
    """
    Retrieve each table in the cluster along with its statistics.
    """
    # For tables: stats['id'] = ['table', '<TABLE_ID>']
    is_table_stats_row = r.row['id'].nth(0) == 'table'
    table_id = r.row['id'].nth(1)

    stats = r.db('rethinkdb').table('stats')
    table_config = r.db('rethinkdb').table('table_config')

    rows = stats.filter(is_table_stats_row).eq_join(table_id, table_config).run(conn)  # type: Iterator[JoinRow]

    for row in rows:
        table_stats = row['left']  # type: TableStats
        table = row['right']  # type: Table
        yield table, table_stats


def query_replicas_with_stats(conn):
    # type: (rethinkdb.net.Connection) -> Iterator[Tuple[Table, Server, ShardReplica, ReplicaStats]]
    """
    Retrieve each replica (table/server pair) in the cluster along with its statistics.
    """

    # NOTE: To reduce bandwidth usage, we make heavy use of the `.pluck()` operation (i.e. ask RethinkDB for a specific
    # set of fields, instead of sending entire objects, which can be expensive when joining data as we do here.)
    # See: https://rethinkdb.com/api/python/pluck/

    stats = r.db('rethinkdb').table('stats')
    server_config = r.db('rethinkdb').table('server_config')
    table_config = r.db('rethinkdb').table('table_config')
    table_status = r.db('rethinkdb').table(
        'table_status',
        # Required so that 'server' fields in 'replicas' entries refer contain UUIDs instead of names.
        # This way, we can join server information more efficiently, as we don't have to lookup UUIDs from names.
        # See: https://rethinkdb.com/api/python/table/#description
        identifier_format='uuid',
    )

    query = (
        # Start from table statuses, as they contain the list of replicas for each shard of the table.
        # See: https://rethinkdb.com/docs/system-tables/#table_status
        table_status.pluck('id', {'shards': ['replicas']})
        .merge({'table': r.row['id']})
        .without('id')
        # Flatten each table status entry into one entry per shard and replica.
        .concat_map(lambda row: row['shards'].map(lambda shard: row.merge(shard.pluck('replicas'))))
        .without('shards')
        .concat_map(
            lambda row: row['replicas'].map(lambda replica: row.merge({'replica': replica.pluck('server', 'state')}))
        )
        .without('replicas')
        # Grab table information for each replica.
        # See: https://rethinkdb.com/docs/system-tables#table_config
        .merge({'table': table_config.get(r.row['table']).pluck('id', 'db', 'name')})
        # Grab relevant server information for each replica.
        # See: https://rethinkdb.com/docs/system-tables#server_config
        .merge(
            {
                'server': (
                    server_config.get(r.row['replica']['server'])
                    .default({'id': None})  # Disconnected servers aren't present in the 'server_config' table.
                    .pluck('id', 'name', 'tags')
                )
            }
        )
        # Grab statistics for each replica.
        # See: https://rethinkdb.com/docs/system-stats/#replica-tableserver-pair
        .merge(
            {
                'stats': stats.get(['table_server', r.row['table']['id'], r.row['server']['id']])
                .default({})
                .pluck('query_engine', 'storage_engine'),
            }
        )
    )

    rows = query.run(conn)  # type: Iterator[dict]

    for row in rows:
        table = row['table']  # type: Table
        server = row['server']  # type: Server
        replica = row['replica']  # type: ShardReplica
        replica_stats = row['stats']  # type: ReplicaStats
        yield table, server, replica, replica_stats


def query_table_status(conn):
    # type: (rethinkdb.net.Connection) -> Iterator[TableStatus]
    """
    Retrieve the status of each table in the cluster.
    """
    return r.db('rethinkdb').table('table_status').run(conn)


def query_server_status(conn):
    # type: (rethinkdb.net.Connection) -> Iterator[ServerStatus]
    """
    Retrieve the status of each server in the cluster.
    """
    return r.db('rethinkdb').table('server_status').run(conn)


def query_system_jobs(conn):
    # type: (rethinkdb.net.Connection) -> Iterator[Job]
    """
    Retrieve all the currently running system jobs.
    """
    return r.db('rethinkdb').table('jobs').run(conn)
