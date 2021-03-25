def build_project_meta(csv_index):
    r = {}
    comp = get_companies_dict()
    u = User.objects(email="seed@dacot.uoct.cl").first()
    for k, v in csv_index.items():
        rk = k.split(".")[0]
        m = ProjectMeta(version="base", status="PRODUCTION", status_user=u)
        m.commune = v.get("commune")
        m.maintainer = comp.get(v.get("maintainer"))
        r[rk] = m
    return r

def build_otu(project_metas):
    global is_diff
    l = []
    d = {}
    for k in project_metas:
        o = OTU(oid=k)
        if is_diff:
            o.version = "latest"
        l.append(o)
    # saved_ids = fast_validate_and_insert(l, OTU)
    for s in l:
        d[s.oid] = s
    return d

def build_projects(csv_index):
    global is_diff
    metas = build_project_meta(csv_index)
    otus = build_otu(metas)
    comps = get_companies_dict()
    lp = []
    cmodels = {}
    otu_cmodels = {}
    for v in csv_index.values():
        otus.get(v.get("oid")).metadata = OTUMeta()
        otus.get(v.get("oid")).metadata.ip_address = v.get("ip_address")
        cmk = (v.get("otu_company"), v.get("otu_model"))
        if cmk[0] and cmk[1]:
            if not cmk[0] in comps:
                comps[cmk[0]] = ExternalCompany(name=cmk[0]).save().reload()
            if not cmk in cmodels:
                cmodels[cmk] = (
                    ControllerModel(company=comps[cmk[0]], model=cmk[1]).save().reload()
                )
            otu_cmodels[v.get("oid")] = cmodels[cmk]
    for s in otus.values():
        otus[s.oid] = s
    for oid in otus:
        p = Project(metadata=metas.get(oid), otu=otus.get(oid), oid=oid)
        if is_diff:
            p.metadata.version = "latest"
        p.controller = Controller()
        if oid in otu_cmodels:
            p.controller.model = otu_cmodels[oid]
        lp.append(p)
    return otus, lp


def build_junctions(csv_index, otus):
    global is_diff
    lj = []
    jd = {}
    od = {}
    for k, v in csv_index.items():
        jid = k.split(".")[1]
        j = Junction(jid=jid, metadata=JunctionMeta())
        j.metadata.location = (v.get("latitude", 0.0), v.get("longitude", 0.0))
        j.metadata.address_reference = v.get("address_reference")
        j.metadata.sales_id = v.get("sales_id")
        if is_diff:
            j.version = "latest"
        lj.append(j)
    for saved in lj:
        jd[saved.jid] = saved
    for k, v in csv_index.items():
        oid, jid = k.split(".")
        otus[oid].junctions.append(jd[jid])
    for saved in otus.values():
        od[saved.oid] = saved
    return jd, od

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
