import glob
import logging
import argparse
from pathlib import Path
from PyPDF4 import PdfFileReader

global log

def setup_logging():
    global log
    log_fmt = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%d-%b-%y %H:%M:%S')
    logging.basicConfig(format=log_fmt[0], datefmt=log_fmt[1])
    fout = logging.FileHandler('pdf-export.log')
    fout.setFormatter(logging.Formatter(log_fmt[0], datefmt=log_fmt[1]))
    log = logging.getLogger('pdf-export')
    log.setLevel(logging.INFO)
    log.addHandler(fout)

def find_files(args):
    globstr = str(Path(args.folder).joinpath('*.pdf'))
    return glob.glob(globstr)

def extract_text(pdf_path):
    with open(pdf_path, 'rb') as fp:
        pdf_reader = PdfFileReader(fp)
        text = [page.extractText().replace('\n', ' ') for page in pdf_reader.pages]
    return text

def parse_text(pages_text):
    global log
    if pages_text[0] == '':
        res = 'ONLY IMGS'
    elif pages_text[0][0:24] == 'CONTROLADOR DE SEMAFOROS':
        res = 'OK'
    else:
        res = 'UNKNOWN FORMAT'
    log.info('Result => {}'.format(res))
    if res == 'OK':
        return True
    return False

def parse_files(files):
    global log
    done, failed = 0, 0
    for idx, pdf in enumerate(files):
        log.info('Parsing file {}/{} => {}'.format(idx + 1, 155, pdf))
        text = extract_text(pdf)
        result = parse_text(text)
        if result:
            done += 1
        else:
            failed += 1
    log.info('RESULTS => Ok: {} Failed: {}'.format(done, failed))

if __name__ == "__main__":
    global log
    parser = argparse.ArgumentParser(description='Extract timings and configuration data from PDF files')
    parser.add_argument('folder', type=str, help='directory of input files')
    args = parser.parse_args()
    setup_logging()
    log.info('Started PDF export utility')
    pdfs = find_files(args)
    log.info('Found {} PDF files in {}'.format(len(pdfs), args.folder))
    parse_files(pdfs)

#with open('file.pdf', rb) as fp:
#    pdfp = PdfFileReader(fp)
#    text = [p for pdfp.pages]