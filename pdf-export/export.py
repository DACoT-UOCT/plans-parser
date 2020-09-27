import re
import glob
import logging
import argparse
import datetime
import numpy as np
from pathlib import Path
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextBoxHorizontal

global log

RESULT_OK = 0
RESULT_EMPTY = 1
RESULT_UNKNOWN = 2
RESULT_INCOMPLETE_PARSING = 3
RESULT_ONLY_IMAGES = 4

def setup_logging(tofile=True):
    global log
    log_fmt = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%d-%b-%y %H:%M:%S')
    logging.basicConfig(format=log_fmt[0], datefmt=log_fmt[1])
    log = logging.getLogger('pdf-export')
    log.setLevel(logging.INFO)
    if tofile:
        fout = logging.FileHandler('pdf-export.log')
        fout.setFormatter(logging.Formatter(log_fmt[0], datefmt=log_fmt[1]))
        log.addHandler(fout)

def find_files(fpath):
    globstr = str(Path(fpath).joinpath('**/*.pdf'))
    return glob.glob(globstr, recursive=True)

def parse_pdf_tek_i_b_1_singlej(pages):
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
    stages_page_tag = re.compile('.*Definición de etapas.*', re.IGNORECASE)
    intergrees_page_tag = re.compile('.*Definición de entreverdes.*', re.IGNORECASE)
    stages = None
    intergreens = None
    for pid, layout in enumerate(pages):
        for element in layout:
            if isinstance(element, LTTextBoxHorizontal):
                if stages is None and stages_page_tag.match(element.get_text().strip()):
                    first_stages_re = re.compile(r'([A-Z]\s*\n){2,}')
                    second_stages_re = re.compile(r'(((VEH)|(PEA)|(FLE)|(DUM))\s*\n)+')
                    text_box_elements = [element_ for element_ in pages[pid] if isinstance(element_, LTTextBoxHorizontal)]
                    for tid, text_box in enumerate(text_box_elements):
                        first_match = first_stages_re.match(text_box.get_text())
                        if first_match:
                            stages_list = first_match.group(0).strip().split()
                            types_match = second_stages_re.match(text_box_elements[tid + 1].get_text())
                            if not types_match:
                                types_match = second_stages_re.match(text_box_elements[tid - 1].get_text())
                            types = types_match.group(0).strip().split()
                            stages = zip(stages_list, types)
                            break
                if intergreens is None and intergrees_page_tag.match(element.get_text().strip()):
                    item_re = re.compile(r'^([A-Z]\s*\n)$|^([0-9]{1,2}\s*\n)$')
                    text_box_elements = [element_ for element_ in pages[pid] if isinstance(element_, LTTextBoxHorizontal)]
                    matrix_items = []
                    for element_ in text_box_elements:
                        letter_match = item_re.match(element_.get_text())
                        if letter_match:
                            matrix_items.append((int(element_.x0), int(element_.y0), element_.get_text().strip()))
                    # TODO: Get delta from document (how?)
                    _delta = 6
                    new_x, x_map, x_index = __matrix_util_rebuild_row_delta([i[0] for i in matrix_items], _delta)
                    new_y, y_map, y_index = __matrix_util_rebuild_row_delta([i[1] for i in matrix_items], _delta)
                    intergreens = np.zeros((len(new_x), len(new_y))).astype(np.str)
                    for mitem in matrix_items:
                        intergreens[x_index[x_map[mitem[0]]]][y_index[y_map[mitem[1]]]] = mitem[2]
                    intergreens = np.flipud(intergreens.T)
    return list(stages), intergreens

def parse_pdf_tek_i_b_1_multiple(pages, junctions_names):
    junctions_regexs = [re.compile(r'^\s*NODO {}:'.format(j[-1])) for j in junctions_names]
    junction_pages_found = {}
    for idx, j in enumerate(junctions_names):
        junction_pages_found[j] = {}
        junction_pages_found[j]['regex'] = junctions_regexs[idx]
        junction_pages_found[j]['pages'] = []
    for page in pages:
        text_box_elements = [element_ for element_ in page if isinstance(element_, LTTextBoxHorizontal)]
        for element in text_box_elements:
            if 'NODO' in element.get_text():
                for v in junction_pages_found.values():
                    if v['regex'].match(element.get_text().strip()):
                        v['pages'].append(page)
                        break
                break
    results = {}
    for k, v in junction_pages_found.items():
        stages, intergreens = parse_pdf_tek_i_b_1_singlej(v['pages'])
        results[k] = {'stages': stages, 'inters': intergreens}
    return results

def __util_find_text_element(page, element_text):
    text_box_elements = [element_ for element_ in page if isinstance(element_, LTTextBoxHorizontal)]
    for text_elem in text_box_elements:
        if text_elem.get_text().strip() == element_text:
            return True
    return False

def process_pages(pages, pdf_fname):
    global log
    first_page_items = list(pages[0])
    res = (RESULT_UNKNOWN, RESULT_UNKNOWN)
    if pages[0].is_empty():
        res = (RESULT_EMPTY, RESULT_UNKNOWN)
    elif isinstance(first_page_items[0], LTTextBoxHorizontal) and first_page_items[0].get_text().strip() == 'CONTROLADOR DE SEMAFOROS':
        if __util_find_text_element(first_page_items, 'MODELO TEK I B'):
            multiple_junctions = False
            text_box_elements = [element_ for element_ in first_page_items if isinstance(element_, LTTextBoxHorizontal)]
            single_junction_re = re.compile(r'.*(J\d{6}).*')
            multiple_junction_re = re.compile(r'^(J\d{6}\s/\s)+J\d{6}$')
            junction_name = None
            for element in text_box_elements:
                if multiple_junction_re.match(element.get_text().strip()):
                    multiple_junctions = True
                    junction_name = element.get_text().strip().split(' / ')
                    break
            if multiple_junctions:
                multiple_results = parse_pdf_tek_i_b_1_multiple(pages, junction_name)
                res = (RESULT_OK, 'TEK I B', multiple_results) #TODO: Check everything is here
            else:
                junction_name = single_junction_re.match(pdf_fname)
                if junction_name:
                    junction_name = junction_name.group(1)
                stages, intergreens = parse_pdf_tek_i_b_1_singlej(pages)
                if stages is None or intergreens is None or junction_name is None:
                    res = (RESULT_INCOMPLETE_PARSING, RESULT_UNKNOWN)
                else:
                    res = (RESULT_OK, 'TEK I B', {junction_name: {'stages': stages, 'inters': intergreens}})
        elif __util_find_text_element(first_page_items, 'MODELO ST 950'):
            res = (RESULT_ONLY_IMAGES, RESULT_UNKNOWN)
        else:
            print(first_page_items[1])
    log.info('Result => {}'.format(res[:2]))
    return res

def parse_files(files, unique=False, debug_results=False):
    global log
    done, failed = 0, 0
    results = {}
    results_types = {}
    if unique:
        lfiles = 1
        log.info('Parsing file {}'.format(files))
        pages = list(extract_pages(files))
        result = process_pages(pages, files)
        if result[0] == RESULT_OK:
            done += 1
        else:
            failed += 1
        if not result[0] in results:
            results[result[0]] = 0
            results[result[0]] += 1
        results_types[files] = result[1]
    else:
        lfiles = len(files)
        for idx, pdf in enumerate(files):
            log.info('Parsing file {}/{} => {}'.format(idx + 1, lfiles, pdf))
            pages = list(extract_pages(pdf))
            result = process_pages(pages, pdf)
            if result[0] == RESULT_OK:
                done += 1
            else:
                failed += 1
            if not result[0] in results:
                results[result[0]] = 0
            results[result[0]] += 1
            results_types[pdf] = result[1]
            # if len(result) == 3:
            #     print(result[2])
    log.info('RESULTS => Ok: {} Failed: {} | Progress = {:.2f}%'.format(done, failed, 100 * float(done) / float(lfiles)))
    log.info('RESULTS => {}'.format(results))
    if debug_results:
        log.info('PARSED_TYPES =>')
        for k, v in results_types.items():
            if type(v) != int:
                log.info('{} => {}'.format(k, v))

if __name__ == "__main__":
    global log
    start_t = datetime.datetime.now()
    parser = argparse.ArgumentParser(description='Extract timings and configuration data from PDF files')
    parser.add_argument('path', type=str, help='path of the input file(s)')
    parser.add_argument('--unique', action='store_true', help='parse only one file in path')
    parser.add_argument('--debug', action='store_true', help='print results info at the end of execution')
    parser.add_argument('--nologfile', action='store_false', help='disable logging output to file')
    args = parser.parse_args()
    setup_logging(tofile=args.nologfile)
    log.info('Started PDF export utility')
    if args.unique:
        parse_files(args.path, unique=True, debug_results=args.debug)
    else:
        pdfs = find_files(args.path)
        log.info('Found {} PDF files in {}'.format(len(pdfs), args.path))
        parse_files(pdfs, debug_results=args.debug)
    log.info('Done. Script running time: {}'.format(datetime.datetime.now() - start_t))
