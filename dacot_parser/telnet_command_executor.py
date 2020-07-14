import queue
import telnetlib

class TelnetCommandExecutor():
    def __init__(self, host, port=23, connection_timeout=7):
        self.__commands = queue.Queue()
        self.__target_host = host
        self.__target_port = port
        self.__conn_timeout = connection_timeout
        self.__reads_outputs = {}
        self.__command_history = []
        self.__current_command = 'init'

    def command(self, identifier, command):
        self.__command_history.append(identifier)
        item = (identifier, lambda **kwargs: self.__command_impl(command, **kwargs))
        self.__commands.put(item)

    def read_lines(self, encoding='ascii', line_ending=b'\n'):
        item = ('read_lines', lambda **kwargs: self.__read_lines_impl(encoding, line_ending, **kwargs))
        self.__commands.put(item)

    def read_until(self, text, timeout=None, encoding='ascii'):
        item = ('read_until', lambda **kwargs: self.__read_until_impl(text, timeout, encoding, **kwargs))
        self.__commands.put(item)

    def get_results(self):
        return self.__reads_outputs

    def history(self):
        return self.__command_history

    def __read_lines_impl(self, encoding, line_ending, **kwargs):
        telnet = kwargs['telnet']
        lines = []
        while True:
            l = telnet.read_until(line_ending, 1)
            if l == b'':
                break
            lines.append(l.decode(encoding).rstrip())
        return lines

    def __command_impl(self, command, **kwargs):
        telnet = kwargs['telnet']
        comm = bytes(command + '\r\n', encoding='ascii')
        telnet.write(comm)

    def __read_until_impl(self, text, timeout, encoding, **kwargs):
        telnet = kwargs['telnet']
        out = telnet.read_until(bytes(text, encoding=encoding), timeout)
        return out.decode(encoding)

    def reset(self):
        self.__reads_outputs.clear()
        self.__command_history.clear()
        self.__commands.queue.clear()

    def run(self):
        # TODO: Add debug messages, method try/catch and return status code
        with telnetlib.Telnet(self.__target_host, self.__target_port, self.__conn_timeout) as tn_client:
            while not self.__commands.empty():
                cmd = self.__commands.get()
                if 'read' in cmd[0]:
                    if not self.__current_command in self.__reads_outputs:
                        self.__reads_outputs[self.__current_command] = []
                    output = cmd[1](telnet=tn_client)
                    self.__reads_outputs[self.__current_command].append(output)
                else:
                    self.__current_command = cmd[0]
                    cmd[1](telnet=tn_client)
