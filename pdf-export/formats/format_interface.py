import camelot
from abc import ABC, abstractmethod

class FormatInterface(ABC):
    def __init__(self, input_file):
        self._input = input_file

    def _read_table(self, table_area, flavor='stream'):
        table = camelot.read_pdf(self._input, flavor=flavor, table_areas=[table_area])
        if table.n != 1:
            raise RuntimeError('No table found')
        return table[0].df

    @abstractmethod
    def identity(self):
        """Test if the supplied file is parseable by this interface implementation"""
        raise NotImplementedError

#    @abstractmethod
    def parse(self):
        """Parse the needed data"""
        raise NotImplementedError
