from formats import *

formats = [AuterA5]
inputf = '/home/cponce/pdf-ocr-test-dacot/test.pdf'

for f in formats:
    finst = f(inputf)
    finst.identity()
    print(finst)
