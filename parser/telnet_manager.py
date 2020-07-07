import logging
import telnetlib

class TelnetManager():
    def __init__(self):
        self.__telnet = None

    def start(self, host, port=23, creds=None):
        try:
            logging.debug('Starting telnet session to {}:{}'.format(host, port))
            self.__telnet = telnetlib.Telnet(host, port)
            logging.debug('Connected to {}:{}'.format(host, port))
        except Exception as error:
            logging.fatal(error)
            return False
        return True

    def command(self, text):
        try:
            self.__telnet.write(bytes(text + '\r\n', encoding='ascii'))
        except Exception as error:
            logging.fatal(error)
            return False
        return True

    def read_until(self, text):
        try:
            return self.__telnet.read_until(bytes(text, encoding='ascii'))
        except Exception as error:
            logging.fatal(error)
            return False

    def read_lines(self):
        lines = []
        try:
            while True:
                line = self.__telnet.read_until(b'\n', 1)
                if line == b'':
                    break
                lines.append(line)
            return lines
        except Exception as error:
            logging.fatal(error)
            return False

    def terminate_command(self, command):
        if self.command(command):
            try:
                self.__telnet.read_all()
            except ConnectionResetError as err:
                logging.debug('Read all caused a ConnectionResetError while closing the connection, this is OK. {}'.format(err))
            self.__telnet.close()
            return True
        else:
            return False
        
