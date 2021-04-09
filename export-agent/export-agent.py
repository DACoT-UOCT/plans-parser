import os
import sys
from loguru import logger
from datetime import datetime
from telnet_command_executor import TelnetCommandExecutor as TCE

class ExportAgent:
    def __init__(self):
        env = os.environ
        if not ('UTC_HOST' in env and 'UTC_USER' in env and 'UTC_PASS' in env):
            raise RuntimeError('Missing variables')
        self.__utc_host = env['UTC_HOST']
        self.__utc_user = env['UTC_USER']
        self.__utc_passwd = env['UTC_PASS']
        self.__read_plans_sleep = 120

    def run_full_session(self):
        logger.info('Starting FULL SESSION!')
        executor = TCE(host=self.__utc_host, logger=logger)
        logger.debug('Using TCE={}'.format(executor))
        self.__login_sys(executor)
        self.__get_plans(executor)
        self.__logout_sys(executor)
        logger.debug('Using the following full-session execution plan: {}'.format(executor.history()))
        logger.info('=== STARTING SESSION EXECUTION ===')
        executor.run(debug=True)
        self.__write_results(executor, 'utc_sys_exports/dacot-export-agent')
        logger.info('Full session done')

    def __write_results(self, executor, output_prefix):
        now = datetime.now()
        outfile = './{}_{}.sys_txt'.format(output_prefix, now.isoformat())
        logger.info('Saving TCE execution result to {}'.format(outfile))
        with open(outfile, 'w') as out:
            res = executor.get_results()
            for k, v in res:
                out.write('{}\n'.format('=' * 30))
                out.write('{}\n'.format(k))
                out.write('{}\n'.format('=' * 30))
        logger.info('Saving done in {}'.format(outfile))

    def __get_plans(self, executor):
        logger.info('Building get-plans procedure')
        executor.command('get-plans-wildcard', 'LIPT A000000 TIMINGS')
        logger.warning('Using a {} (s) sleep call to wait for buffers from remote'.format(self.__read_plans_sleep))
        executor.sleep(self.__read_plans_sleep)
        executor.read_lines(encoding="iso-8859-1", line_ending=b"\x1b8\x1b7")
        logger.debug('Get-Plans built')

    def __login_sys(self, executor):
        logger.info('Building login procedure')
        executor.read_until('Username:', 15)
        executor.command('login-user', self.__utc_user)
        executor.read_until('Password:', 15)
        executor.command('login-pass', self.__utc_passwd)
        executor.read_lines(encoding='iso-8859-1')
        logger.debug('Login built')

    def __logout_sys(self, executor):
        logger.info('Building logout procedure')
        executor.command("end-session", "ENDS")
        logger.debug('Logout built')

if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level='DEBUG')
    try:
        logger.info('Starting')
        agent = ExportAgent()
        agent.run_full_session()
        logger.info('Done')
    except Exception as excep:
        logger.exception('Global Exception!')
