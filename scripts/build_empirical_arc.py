#!/usr/bin/env python3
"""Replay the real-data walkthrough from frozen extracts; no models, source writes or refits.

The inputs in data/empirical/ are hash-verified projections of the study's research
records, not the synthetic fixture. Interpretive case cards are supplied evidence,
never inferred from counts.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import html
import io
import itertools
import json
import math
from pathlib import Path
import statistics

TROPES=('boom_and_bust','structural_risk','shaky_foundations','smart_vs_dumb_money',
        'stock_hype','bumbling_fools','hidden_skeletons','hustler_story','impossible_challenge')
def sha(data):return hashlib.sha256(data).hexdigest()
def unique(rows,key):
    result={}
    for row in rows:
        k=key(row)
        if k in result:raise ValueError('Duplicate key: '+str(k))
        result[k]=row
    return result
def number(x):
    if x is None or str(x).strip()=='':raise ValueError('Missing numeric value')
    n=float(x)
    if not math.isfinite(n):raise ValueError('Nonfinite numeric value')
    return n
def binary(x):
    n=integer(x)
    if n not in (0,1):raise ValueError('Expected binary label')
    return n
def integer(x):
    n=number(x)
    if not n.is_integer():raise ValueError('Expected integer')
    return int(n)
def load_inputs(root):
    manifest=json.loads((root/'manifest.json').read_text());result={}
    for name,h in manifest['files'].items():
        p=root/name
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('Input path escape')
        data=p.read_bytes()
        if sha(data)!=h:raise ValueError('Input hash mismatch: '+name)
        if p.suffix=='.csv':result[name]=list(csv.DictReader(io.StringIO(data.decode())))
        elif p.suffix=='.json':result[name]=json.loads(data)
        else:raise ValueError('Unsupported input')
    return manifest,result
def analyze(data):
    profiles=unique(data['campaign_trope_profiles.csv'],lambda x:integer(x['campaign_id']))
    narrative=unique(data['campaign_narrative_measure.csv'],lambda x:integer(x['campaign_id']))
    clusters=unique(data['cluster_assignments.csv'],lambda x:integer(x['campaign_id']))
    if not profiles.keys()==narrative.keys()==clusters.keys():raise ValueError('Campaign universe mismatch')
    decisions=data['selected_original_adjudicated_and_model_labels.json']
    unique(decisions,lambda x:integer(x['item_id']))
    unique(decisions,lambda x:(integer(x['campaign_id']),integer(x['segment_id']),x['task']))
    matrices=data['comparison_matrix_rows.csv']
    unique(matrices,lambda x:(x['version'],integer(x['campaign_id'])))
    for row in matrices:
        if integer(row['campaign_id']) not in profiles:raise ValueError('Matrix campaign missing profile')
    breadth={};counts={};by_cluster=defaultdict(list)
    for cid,p in profiles.items():
        n=narrative[cid];den=integer(n['segments']);yes=integer(n['majority_narrative'])
        if den<=0 or not 0<=yes<=den or abs(number(n['stored_share'])-yes/den)>1e-10:raise ValueError('Narrative share mismatch')
        counts[cid]={t:integer(p[t+'_count_api_majority']) for t in TROPES}
        present={t:integer(p[t+'_present_api_majority']) for t in TROPES}
        routed=integer(p['trope_vote_segment_count'])
        if not 0<=routed<=den or any(v<0 or v>routed for v in counts[cid].values()):raise ValueError('Impossible trope count')
        if any(present[t]!=int(counts[cid][t]>0) or present[t]!=integer(clusters[cid][t+'_present']) for t in TROPES):raise ValueError('Cluster feature/profile mismatch')
        breadth[cid]=sum(present.values());by_cluster[clusters[cid]['cluster_kmeans']].append(cid)
    if len(by_cluster)!=2:raise ValueError('Expected two stored content clusters')
    means={k:statistics.mean(breadth[c] for c in ids) for k,ids in by_cluster.items()}
    if len(set(means.values()))!=2:raise ValueError('Ambiguous breadth naming')
    broad=max(means,key=means.get)
    cluster_name={k:('broad' if k==broad else 'focused') for k in by_cluster}
    groups=[{'stored_cluster':k,'descriptive_name':cluster_name[k],'campaigns':len(ids),
        'mean_trope_breadth':means[k],'mean_campaign_narrative_share':statistics.mean(number(narrative[c]['stored_share']) for c in ids)} for k,ids in sorted(by_cluster.items())]
    pairs=[{'trope_a':a,'trope_b':b,'campaigns':sum(counts[c][a]>0 and counts[c][b]>0 for c in profiles),'denominator':len(profiles)} for a,b in itertools.combinations(TROPES,2)]
    trace=[];after={c:counts[c].copy() for c in profiles};after_n={c:integer(n['majority_narrative']) for c,n in narrative.items()}
    for d in decisions:
        cid=integer(d['campaign_id'])
        if cid not in profiles:raise ValueError('Decision campaign missing profile')
        m=d['current_cached_model_values'];final=d['adjudicated_codes']
        if not d.get('canonical_passage_sha256'):raise ValueError('Missing canonical passage identity')
        if d['task']=='narrative_structure':
            if final.get('narrative_structure') not in ('is_narrative','is_argument'):raise ValueError('Unknown adjudicated narrative state')
            after_n[cid]+=int(final['narrative_structure']=='is_narrative')-binary(m['api_narrative_majority'])
        elif d['task']=='tropes':
            for t in TROPES:after[cid][t]+=binary(final[t])-binary(m['api_tropes_'+t+'_majority'])
        else:raise ValueError('Unsupported decision task')
        trace.append({'item_id':d['item_id'],'campaign_id':cid,'segment_id':d['segment_id'],'task':d['task'],
            'original_readings':d['original_readings'],'adjudicated_codes':final,'current_cached_model_values':m,
            'original_status':'stored originals available' if d['original_readings'] else 'missing originals; not a paired before/after',
            'passage_sha256':d['canonical_passage_sha256'],'current_campaign_breadth':breadth[cid],
            'current_narrative_share':number(narrative[cid]['stored_share'])})
    overlay=[]
    expected={integer(x['campaign_id']):x for x in data['bounded_correction_overlay.json']['campaigns']}
    for cid in sorted({integer(d['campaign_id']) for d in decisions}):
        den=integer(narrative[cid]['segments'])
        if any(v<0 or v>den for v in after[cid].values()) or not 0<=after_n[cid]<=den:raise ValueError('Invalid overlay')
        row={'campaign_id':cid,'segments':den,'narrative_before':integer(narrative[cid]['majority_narrative']),
             'narrative_after':after_n[cid],'share_before':number(narrative[cid]['stored_share']),'share_after':after_n[cid]/den,
             'trope_counts_before':counts[cid],'trope_counts_after':after[cid],
             'presence_changes':[t for t in TROPES if (counts[cid][t]>0)!=(after[cid][t]>0)]}
        prior=expected.get(cid)
        if prior is None or any(row[k]!=prior[k] for k in ('narrative_before','narrative_after','trope_counts_before','trope_counts_after')):raise ValueError('Frozen overlay mismatch')
        overlay.append(row)
    cards=data['case_cards.json'];unique(cards,lambda c:integer(c['campaign_id']));cases=[]
    for card in cards:
        cid=integer(card['campaign_id'])
        if cid not in profiles:raise ValueError('Case missing profile')
        for key in ('interpretation','textual_relations','sources','limits'):
            if not card.get(key):raise ValueError('Missing documentary case field: '+key)
        cases.append({**card,'evidence_kind':'documentary interpretation; not an algorithmically assigned strategy',
            'computed':{'segments':integer(narrative[cid]['segments']),'narrative_positive':integer(narrative[cid]['majority_narrative']),
                'narrative_share':number(narrative[cid]['stored_share']),'trope_breadth':breadth[cid],
                'trope_counts':counts[cid],'stored_content_cluster':cluster_name[clusters[cid]['cluster_kmeans']]},
            'matrix_witnesses':[r for r in matrices if integer(r['campaign_id'])==cid]})
    pools=data['ground_truth_campaign_lengths.csv'];unique(pools,lambda r:integer(r['campaign_id']))
    summary={'campaigns':len(profiles),'segments':sum(integer(r['segments']) for r in narrative.values()),
        'positive_narrative_segments':sum(integer(r['majority_narrative']) for r in narrative.values()),
        'zero_valid_rows':sum(integer(r['zero_valid_rows']) for r in narrative.values()),
        'unweighted_mean_narrative_share':statistics.mean(number(r['stored_share']) for r in narrative.values()),
        'clusters':groups,'trope_prevalence':{t:sum(counts[c][t]>0 for c in profiles) for t in TROPES},
        'matrix_campaign_counts':dict(Counter(r['version'] for r in matrices)),
        'pool_campaigns':len(pools),'pool_segments':sum(integer(r['segments']) for r in pools),
        'early_median_words':statistics.median(integer(r['words']) for r in pools if integer(r['pool_order'])<2),
        'later_median_words':statistics.median(integer(r['words']) for r in pools if integer(r['pool_order'])>=2),
        'selected_decisions':len(trace),'case_comparisons':len(cases),
        'limits':'Recomputed from frozen extracted artifacts. Existing cluster assignments retained; no model calls, cluster refits, corpus recoding or causal-effect estimates. Documentary relations are explicitly supplied readings.'}
    return {'summary':summary,'cooccurrence':pairs,'decisions':trace,'overlay':overlay,'cases':cases}
def render(result):
    s=result['summary'];lines=['# An empirical walkthrough from coding to strategies','',
      'Computed joins and summaries are distinguished from documentary interpretations. The inputs are real extracted research artifacts, frozen in data/empirical/. This walkthrough does not computationally recreate discovery or classify strategies from counts.','',
      '## 1 Original readings and adjudication','', '| Item | Campaign and segment | Original state | Adjudicated state |','|---|---|---|---|']
    for d in result['decisions']:
        if d['item_id'] not in (115,121,166,215):continue
        def labels(c):return ', '.join(k for k,v in c.items() if v==1) if 'narrative_structure' not in c else c['narrative_structure']
        lines.append(f"| {d['item_id']} | {d['campaign_id']} / {d['segment_id']} | "+(' ; '.join(labels(x['codes']) for x in d['original_readings']) or 'Missing originals')+' | '+labels(d['adjudicated_codes'])+' |')
    lines+=['','The original/adjudicated comparison is historical evidence. The current model/profile comparison is a separate diagnostic; their timing must not be collapsed. Item 115’s proposed background-event rule was rejected in correspondence. See the substantive account and source register for the textual warrants and adopted definitions.','',
      '## 2 Corpus description','',f"Computed universe: {s['campaigns']} campaigns, {s['segments']} segments, {s['positive_narrative_segments']} positive narrative majorities. The all-segment denominator includes {s['zero_valid_rows']} zero-valid rows. Unweighted mean campaign narrative share: {s['unweighted_mean_narrative_share']:.4%}.",'',
      '| Stored descriptive group | Campaigns | Mean trope breadth | Mean campaign narrative share |','|---|---:|---:|---:|']
    for g in s['clusters']:lines.append(f"| {g['descriptive_name']} | {g['campaigns']} | {g['mean_trope_breadth']:.3f} | {g['mean_campaign_narrative_share']:.2%} |")
    lines+=['','These are two retained content clusters, not three rhetorical strategies. Presence measures repertoire; neither frequency nor cooccurrence establishes centrality or integration.','',
      '### Recurring combinations','', '| Pair of resources | Campaigns containing both | Denominator |','|---|---:|---:|']
    for p in sorted(result['cooccurrence'],key=lambda x:-x['campaigns'])[:6]:lines.append(f"| {p['trope_a']} + {p['trope_b']} | {p['campaigns']} | {p['denominator']} |")
    lines+=['','## 3 Versioned selection and comparative reading','',f"The preserved matrices contain {s['matrix_campaign_counts']}. Their narrative measures are retained by version. Case cards below join those rows to current majority profiles; the strategy readings are documentary and require their source passages.",'']
    for c in result['cases']:
        x=c['computed'];lines += [f"### {c['name']} — campaign {c['campaign_id']}",'',f"Computed: {x['stored_content_cluster']} content cluster; {x['trope_breadth']} tropes; {x['narrative_positive']}/{x['segments']} = {x['narrative_share']:.2%} majority narrative share.",'',c['interpretation'],'',c['textual_relations'],'',
        '| Matrix | Row | Narrative share | EUS tier | Volatility tier |','|---|---:|---:|---|---|']
        for m in c['matrix_witnesses']:lines.append(f"| {m['version']} | {m['excel_row']} | {number(m['narrative_share']):.2%} | {m['eus_tier']} | {m['vol_tier']} |")
        lines+=['','Sources: '+'; '.join(c['sources']),'','Limit or missing link: '+c['limits'],'']
    lines+=['## 4 Feedback without rewriting the corpus','',
      'The following bounded overlay is recomputed from current saved model values and selected adjudications, then checked against the earlier frozen overlay. It is not a historical estimate of codebook-change effects. Gates, denominators and cluster assignments stay fixed.','',
      '| Campaign | Narrative before | Narrative after | Trope-presence changes |','|---|---:|---:|---|']
    for r in result['overlay']:lines.append(f"| {r['campaign_id']} | {r['narrative_before']}/{r['segments']} | {r['narrative_after']}/{r['segments']} | {', '.join(r['presence_changes']) or 'None'} |")
    lines+=['','Campaign 165’s documentary objection is not a stored recoding instruction and therefore is not applied to these numbers. Missing original states remain missing. Impact analysis is supplementary and is not rerun.','',
      '## Inspect the evidence','', '[Computed summaries](summary.json) · [All pair counts](cooccurrence.json) · [Decision states](decisions.json) · [Case joins and documentary readings](cases.json) · [Bounded overlay](overlay.json) · [Input and output hashes](manifest.json).','']
    return '\n'.join(lines)
def html_report(markdown):
    out=[];lines=markdown.splitlines();i=0
    def inline(s):
        import re
        s=html.escape(s);s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
        return s
    while i<len(lines):
        x=lines[i]
        if not x:i+=1;continue
        if x.startswith('#'):
            n=len(x)-len(x.lstrip('#'));out.append(f'<h{n}>'+inline(x[n:].strip())+f'</h{n}>');i+=1
        elif x.startswith('|'):
            table=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=lines[i].strip('|').split('|');i+=1
                if all(set(c.strip())<=set('-:') for c in row):continue
                tag='th' if not table else 'td';table.append('<tr>'+''.join(f'<{tag}>'+inline(c.strip())+f'</{tag}>' for c in row)+'</tr>')
            out.append('<div class="table"><table>'+''.join(table)+'</table></div>')
        else:out.append('<p>'+inline(x)+'</p>');i+=1
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Empirical walkthrough</title><style>body{font:17px/1.6 system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;color:#17242c}h1,h2,h3{line-height:1.25;color:#000}h2{margin-top:2.4em}h3{margin-top:2em;border-left:4px solid #437789;padding-left:14px}a{color:#155a83}table{border-collapse:collapse;font-size:14px;width:100%}td,th{border:1px solid #d3dce1;padding:9px;text-align:left;vertical-align:top}th{background:#e8eef3}.table{overflow:auto}p{max-width:940px}</style>'+''.join(out)+'</html>'
def build(inputs,output):
    inputs=inputs.resolve();output=output.resolve();repo=Path(__file__).resolve().parents[1]
    if output.exists():raise FileExistsError('Output must be new')
    if output.is_relative_to(inputs):raise ValueError('Output must be outside the input directory')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'outputs'):raise ValueError("Output inside the repository must be under outputs/")
    manifest,data=load_inputs(inputs);result=analyze(data)
    # Fail before writing if evidence is incomplete or inconsistent.
    output.mkdir(parents=True,mode=0o700)
    for name,value in result.items():(output/(name+'.json')).write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    md=render(result);(output/'WALKTHROUGH.md').write_text(md);(output/'index.html').write_text(html_report(md))
    hashes={p.name:sha(p.read_bytes()) for p in sorted(output.iterdir())}
    for name,h in manifest['files'].items():
        if sha((inputs/name).read_bytes())!=h:raise ValueError('Input changed during build')
    (output/'manifest.json').write_text(json.dumps({'inputs':manifest['files'],'builder_sha256':sha(Path(__file__).read_bytes()),'outputs':hashes,'source_preserved':True,'interpretation_status':'Case readings supplied by documentary review, not inferred from computed counts.'},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','campaigns':result['summary']['campaigns'],'decisions':len(result['decisions']),'cases':len(result['cases'])}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,default=Path(__file__).resolve().parents[1]/'data'/'empirical');p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.inputs,a.output)
