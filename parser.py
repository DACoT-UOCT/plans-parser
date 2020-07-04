import re
import json
import argparse

# [python:S4784]: There is no risk for a ReDoS since the input text to evaluate is not provided by users
re_plan = re.compile(r'^Plan\s+(?P<id>\d+)\s(?P<junction>J\d{6}).*(?P<cycle>CY\d{3})\s(?P<phases>[A-Z0-9\s,!]+)$')
re_phases = re.compile(r'[A-Z]{1,2}\s\d{1,3}')

def build_phases(re_phases_match):
    initial_format = [{i.split()[0]: int(i.split()[1])} for i in re_phases_match]
    phases_dict = {}
    for phase in initial_format:
        phases_dict.update(phase)
    # Map letter to numbers in  phases ids
    result = {}
    for k in phases_dict.keys():
        if len(k) > 1:
            kn = int(''.join([str(ord(i) - 64) for i in list(k)]))
            result[kn] = phases_dict[k]
        else:
            kn = ord(k) - 64
            result[kn] = phases_dict[k]
    return result

def parse_plan(text):
    plan = re_plan.match(text)
    if not plan:
        return False, None
    phases = re_phases.findall(plan.group('phases'))
    if not phases:
        return False, None
    formatted_phases = build_phases(phases)
    plan_timings = {
        'cycle': int(plan.group('cycle').split('Y')[1]),
        'system_start': formatted_phases
    }
    return True, (plan.group('junction'), plan.group('id'), plan_timings)

def parse_plans_file(fpath, encoding='iso-8859-1'):
    plans = {}
    with open(fpath, encoding=encoding) as fplans:
        for line in fplans.readlines():
            line = line.strip()
            ok, plan = parse_plan(line)
            if ok:
                junct, plan_id, plan_timings = plan
                if not junct in plans:
                    plans[junct] = {}
                plans[junct][plan_id] = plan_timings
    return plans

if __name__ == "__main__":
    args_parser = argparse.ArgumentParser(description='Initial plans parser script')
    args_parser.add_argument('input', type=str, help='Input file')
    args_parser.add_argument('output', type=str, help='Output file')
    args_parser.add_argument('--junc', type=str, help='Junction to verify')
    args = args_parser.parse_args()
    # Parse
    plans = parse_plans_file(args.input)
    print('{} junctions parsed'.format(len(plans.keys())))
    if args.junc:
        print('\nExtracted data for {}:'.format(args.junc))
        print(json.dumps(plans[args.junc], indent='\t'))
    json.dump(plans, open(args.output, 'w'))
    print('Done. Results saved to [{}]'.format(args.output))
