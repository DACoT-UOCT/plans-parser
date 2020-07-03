import re
import json
import argparse

first_re = re.compile(r'^Plan\s+(?P<id>\d+)\s(?P<junction>J\d{6}).*(?P<cycle>CY\d{3})\s(?P<phases>[A-Z0-9\s,]+)$')
second_re = re.compile(r'[A-Z]{1,2}\s\d{1,3}')

def read_plans(file):
    plans = {}
    with open(file, encoding='iso-8859-1') as fplans:
        for idx, line in enumerate(fplans.readlines()):
            line = line.strip()
            if not 'Plan' in line[0:5]:
                continue
            match_junction = first_re.match(line)
            if not match_junction:
                print("WARN: Line [ {} ] didn't match first regex".format(line))
                continue
            match_phases = second_re.findall(match_junction.group('phases'))
            if not match_phases:
                print("WARN: Phases string [ {} ] didn't match regex".format(match_junction.group('phases')))
                continue
            join_phases = {}
            match_phases = [{i.split()[0]: int(i.split()[1])} for i in match_phases]
            phases_dict = {}
            for m in match_phases:
                join_phases.update(m)
            for k in join_phases.keys():
                if len(k) > 1:
                    nk = int(''.join([str(ord(i) - 64) for i in list(k)]))
                    phases_dict[nk] = join_phases[k]
                else:
                    nk = ord(k) - 64
                    phases_dict[nk] = join_phases[k]
            if not match_junction.group('junction') in plans:
                plans[match_junction.group('junction')] = {}
                plans[match_junction.group('junction')][match_junction.group('id')] = {
                    'cycle': int(match_junction.group('cycle').split('Y')[1]),
                    'system_start': phases_dict
                }
            else:
                plans[match_junction.group('junction')][match_junction.group('id')] = {
                    'cycle': int(match_junction.group('cycle').split('Y')[1]),
                    'system_start': phases_dict
                }
    return plans

if __name__ == "__main__":
    args_parser = argparse.ArgumentParser(description='Initial plans parser script')
    args_parser.add_argument('input', type=str, help='Input file')
    args_parser.add_argument('junc', type=str, help='Junction to verify')
    args = args_parser.parse_args()
    # Parse
    plans = read_plans(args.input)
    print('\n\n{} junctions parsed'.format(len(plans.keys())))
    print('\nExtracted data for {}:'.format(args.junc))
    print(json.dumps(plans[args.junc], indent='\t'))
    #json.dump(plans, open('plans.json', 'w'))
