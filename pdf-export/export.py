import re
import glob
import logging
import argparse
import numpy as np
from pathlib import Path
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextBoxHorizontal

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

def find_files(fpath):
    globstr = str(Path(fpath).joinpath('*.pdf'))
    return glob.glob(globstr)

def __matrix_util_rebuild_row_delta(row, delta):
    new_map = {}
    vals = sorted(row)
    new_map[vals[0]] = vals[0]
    result = [vals[0]]
    for iid, v in enumerate(vals[:-1]):
        if vals[iid + 1] - v > delta:
            result.append(vals[iid + 1])
        new_map[vals[iid + 1]] = result[-1]
    index_map = {}
    for iid, i in enumerate(result):
        index_map[i] = iid
    return result, new_map, index_map

def process_pages(pages):
    global log
    first_page_items = list(pages[0])
    res = -1
    if pages[0].is_empty():
        res = 1
    elif isinstance(first_page_items[0], LTTextBoxHorizontal) and first_page_items[0].get_text().strip() == 'CONTROLADOR DE SEMAFOROS':
        if first_page_items[1].get_text().strip() == 'MODELO TEK I B':
            stages_page_tag = re.compile('.*Definición de etapas.*', re.IGNORECASE)
            stages = None
            intergrees_page_tag = re.compile('.*Definición de entreverdes.*', re.IGNORECASE)
            intergreens = None
            for pid, layout in enumerate(pages):
                for element in layout:
                    if isinstance(element, LTTextBoxHorizontal):
                        if stages is None and stages_page_tag.match(element.get_text().strip()):
                            first_stages_re = re.compile(r'([A-Z]\n)+')
                            second_stages_re = re.compile(r'(((VEH)|(PEA))\n)+')
                            text_box_elements = [element_ for element_ in pages[pid] if isinstance(element_, LTTextBoxHorizontal)]
                            for tid, text_box in enumerate(text_box_elements):
                                first_match = first_stages_re.match(text_box.get_text())
                                if first_match:
                                    stages_list = first_match.group(0).strip().split()
                                    types = second_stages_re.match(text_box_elements[tid + 1].get_text()).group(0).strip().split()
                                    stages = zip(stages_list, types)
                                    break
                        if intergreens is None and intergrees_page_tag.match(element.get_text().strip()):
                            item_re = re.compile(r'[A-Z]\n|[0-9]{1,2}\n')
                            text_box_elements = [element_ for element_ in pages[pid] if isinstance(element_, LTTextBoxHorizontal)]
                            matrix_items = []
                            for element_ in text_box_elements:
                                letter_match = item_re.match(element_.get_text())
                                if letter_match:
                                    matrix_items.append((int(element_.x0), int(element_.y0), element_.get_text().strip()))
                            new_x, x_map, x_index = __matrix_util_rebuild_row_delta([i[0] for i in matrix_items], 6) # TODO: Get delta from document
                            new_y, y_map, y_index = __matrix_util_rebuild_row_delta([i[1] for i in matrix_items], 6)
                            intergreens = np.zeros((len(new_x), len(new_y))).astype(np.str)
                            for mitem in matrix_items:
                                intergreens[x_index[x_map[mitem[0]]]][y_index[y_map[mitem[1]]]] = mitem[2]
                            intergreens = np.flipud(intergreens.T)
            if stages is None or intergreens is None:
                res = -1
            else:
                print(list(stages))
                print(intergreens)
                res = 0
    log.info('Result => {}'.format(res))
    if res == 0:
        return True
    return False

def parse_files(files, unique=False):
    global log
    done, failed = 0, 0
    if unique:
        lfiles = 1
        log.info('Parsing file {}'.format(files))
        pages = list(extract_pages(files))
        result = process_pages(pages)
        if result:
            done += 1
        else:
            failed += 1
    else:
        lfiles = len(files)
        for idx, pdf in enumerate(files):
            log.info('Parsing file {}/{} => {}'.format(idx + 1, lfiles, pdf))
            pages = list(extract_pages(pdf))
            result = process_pages(pages)
            if result:
                done += 1
            else:
                failed += 1
    log.info('RESULTS => Ok: {} Failed: {} | Progress = {:.2f}%'.format(done, failed, 100 * float(done) / float(lfiles)))

if __name__ == "__main__":
    global log
    parser = argparse.ArgumentParser(description='Extract timings and configuration data from PDF files')
    parser.add_argument('path', type=str, help='path of the input file(s)')
    parser.add_argument('--unique', action='store_true', help='parse only one file in path')
    args = parser.parse_args()
    setup_logging()
    log.info('Started PDF export utility')
    if args.unique:
        parse_files(args.path, unique=True)
    else:
        pdfs = find_files(args.path)
        log.info('Found {} PDF files in {}'.format(len(pdfs), args.path))
        parse_files(pdfs)
