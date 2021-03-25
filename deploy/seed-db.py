def build_junction_plans(junctions, json_data):
    for k, v in json_data.items():
        j = junctions.get(k)
        if j:
            for pid, pval in v["plans"].items():
                s_start = []
                for phid, phvalue in pval["system_start"].items():
                    s_start.append(JunctionPlanPhaseValue(phid=phid, value=phvalue))
                plan = JunctionPlan(plid=pid, cycle=pval["cycle"], system_start=s_start)
                j.plans.append(plan)
    jd = {}
    for j in junctions.values():
        jd[j.jid] = j
    return jd

def build_otu_programs(otus, json_data, projects):
    done = set()
    programs = {}
    for k, v in json_data.items():
        oid = "X{}0".format(k[1:-1])
        if not oid in done:
            programs[oid] = v.get("program")
            done.add(oid)
    for k, v in otus.items():
        otu_program = []
        if k in programs:
            for table, items in programs[k].items():
                for item in items:
                    otu_program.append(
                        OTUProgramItem(day=table, time=item[0][:5], plan=item[1])
                    )
        v.program = otu_program
    od = {}
    for o in otus.values():
        od[o.oid] = o
    projects = fast_validate_and_insert_with_errors(projects, Project)
    return projects
