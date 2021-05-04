import os
import sys

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql_query_builder import GqlQuery
from loguru import logger


class SetEVAll:
    def __init__(self):
        env = os.environ
        if not 'BACKEND_URL' in env:
            raise RuntimeError('Missing env values')
        self.__backend = env['BACKEND_URL']
        transport = RequestsHTTPTransport(url=self.__backend, use_json=True, timeout=120)
        self.__api = Client(transport=transport, fetch_schema_from_transport=True)
        logger.info('Using {} as API Endpoint'.format(self.__backend))

    def __iterate_get_jids(self, data):
        res = []
        for edge in data['projects']['edges']:
            juncs = edge['node']['otu']['junctions']
            for junc in juncs:
                res.append(junc['jid'])
        return res

    def __read_all_new_projects(self):
        final_result = set()
        junc = GqlQuery().fields(['jid']).query('junctions').generate()
        otu = GqlQuery().fields([junc]).query('otu').generate()
        node = GqlQuery().fields([otu]).query('node').generate()
        edges = GqlQuery().fields([node, 'cursor']).query('edges').generate()
        pageInfo = GqlQuery().fields(['endCursor', 'hasNextPage']).query('pageInfo').generate()
        initial_qry = GqlQuery().fields([pageInfo, edges]).query('projects', input={'first': 40, 'metadata_Version': '"latest"', 'metadata_Status': '"NEW"'}).operation('query').generate()
        result = self.__api.execute(gql(initial_qry))
        has_next = result['projects']['pageInfo']['hasNextPage']
        final_result = final_result.union(set(self.__iterate_get_jids(result)))
        while has_next:
            last_token = result['projects']['pageInfo']['endCursor']
            next_qry = GqlQuery().fields([pageInfo, edges]).query('projects', input={
                'first': 40, 'after': '"{}"'.format(last_token), 'metadata_Version': '"latest"', 'metadata_Status': '"NEW"'
            }).operation('query').generate()
            result = self.__api.execute(gql(next_qry))
            final_result = final_result.union(set(self.__iterate_get_jids(result)))
            has_next = result['projects']['pageInfo']['hasNextPage']
            logger.debug('We have {} junctions'.format(len(final_result)))
        logger.debug('Got {} junctions'.format(len(final_result)))
        return final_result

    def __set_ev(self, jid):
        data = GqlQuery().fields([
            'status: "NEW"',
            'jid: "{}"'.format(jid)
        ]).generate()
        qry = GqlQuery().query('setDefaultIntergreen', input={
            'data': data
        }).operation('mutation').generate()
        self.__api.execute(gql(qry))

    def __compute_table(self, jid):
        qry = GqlQuery().query('computeTables', input={
            'jid': '"{}"'.format(jid), 'status': '"NEW"'
        }).operation('query').generate()
        self.__api.execute(gql(qry))

    def run(self):
        logger.info('Reading all projects in NEW status')
        projs = self.__read_all_new_projects()
        count = len(projs)
        logger.debug('We are going to set VI for {} projects'.format(count))
        for idx, jid in enumerate(projs):
            try:
                logger.debug('[{:05.2f}%] Setting IV for {}'.format(100 * (idx + 1) / count, jid))
                self.__set_ev(jid)
                self.__compute_table(jid)
            except Exception as ex:
                logger.error('[{:05.2f}%] Failed to set IV for {}. Cause: {}'.format(100 * (idx + 1) / count, jid, ex))

if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level='DEBUG')
    try:
        logger.info('Starting')
        set_all = SetEVAll()
        set_all.run()
        logger.info('Done')
    except Exception as excep:
        logger.exception('Global Exception!')
