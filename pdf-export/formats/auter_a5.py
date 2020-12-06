from .format_interface import FormatInterface

class AuterA5(FormatInterface):
    
    def identity(self):
        ftype = self._read_table('47.90660225442834,636.9533778047853,555.7165861513688,594.7942592225917')
        print(ftype)
