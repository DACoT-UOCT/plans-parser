import os
import sys
from gql import gql, Client
from loguru import logger
from gql_query_builder import GqlQuery
from gql.transport.aiohttp import AIOHTTPTransport

class RemoveAllNew:
    def __init__(self):
        env = os.environ
        if not 'BACKEND_URL' in env:
            raise RuntimeError('Missing env values')
        self.__backend = env['BACKEND_URL']
        transport = AIOHTTPTransport(url=self.__backend)
        self.__api = Client(transport=transport, fetch_schema_from_transport=True)
        logger.info('Using {} as API Endpoint'.format(self.__backend))

    def __read_all_new_projects(self):
        qry = GqlQuery().fields(['oid']).query('projects', input={
            'status': '"NEW"'
        }).operation('query').generate()
        result = self.__api.execute(gql(qry))
        return result['projects']

    def __remove_project(self, oid):
        details = GqlQuery().fields([
            'status: "NEW"',
            'oid: "{}"'.format(oid)
        ]).generate()
        qry = GqlQuery().query('deleteProject', input={
            'projectDetails': details
        }).operation('mutation').generate()
        self.__api.execute(gql(qry))

    def run(self):
        logger.info('Reading all projects in NEW status')
        projs = self.__read_all_new_projects()
        count = len(projs)
        logger.debug('We are going to delete {} projects'.format(count))
        for idx, proj in enumerate(projs):
            oid = proj['oid']
            self.__remove_project(oid)
            logger.debug('[{:05.2f}%] Deleting {}'.format(100 * (idx + 1) / count, oid))

if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level='DEBUG')
    try:
        logger.info('Starting')
        remover = RemoveAllNew()
        remover.run()
        logger.info('Done')
    except Exception as excep:
        logger.exception('Global Exception!')
