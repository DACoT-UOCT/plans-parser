import queue
import telnetlib

class TelnetCommandExecutor():
    def __init__(self, host, port=23, connection_timeout=7):
        self.__commands = queue.Queue()
        self.__target_host = host
        self.__target_port = port
        self.__conn_timeout = connection_timeout
        self.__reads_outputs = []
        self.__command_history = []

    def command(self, command):
        self.__command_history.append(command)
        self.__commands.put(lambda **kwargs: self.__command_impl(command, **kwargs))

    def read_lines(self):
        self.__commands.put(lambda **kwargs: self.__read_lines_impl(**kwargs))

    def read_until(self, text, timeout=None):
        self.__commands.put(lambda **kwargs: self.__read_until_impl(text, timeout, **kwargs))

    def get_results(self):
        return self.__reads_outputs

    def history(self):
        return self.__command_history

    def __read_lines_impl(self, **kwargs):
        telnet = kwargs['telnet']
        lines = []
        while True:
            l = telnet.read_until(b'\n', 1)
            if l == b'':
                break
            lines.append(l.decode('ascii').rstrip())
        self.__reads_outputs.append(lines)

    def __command_impl(self, command, **kwargs):
        telnet = kwargs['telnet']
        comm = bytes(command + '\r\n', encoding='ascii')
        telnet.write(comm)

    def __read_until_impl(self, text, timeout, **kwargs):
        telnet = kwargs['telnet']
        out = telnet.read_until(bytes(text, encoding='ascii'), timeout)
        self.__reads_outputs.append(out.decode('ascii'))

    def reset(self):
        self.__reads_outputs.clear()
        self.__command_history.clear()
        self.__commands.queue.clear()

    def run(self):
        # TODO: Add debug messages, method try/catch and return status code
        with telnetlib.Telnet(self.__target_host, self.__target_port, self.__conn_timeout) as tn_client:
            while not self.__commands.empty():
                self.__commands.get()(telnet=tn_client)
