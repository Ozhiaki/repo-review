"""The retained Colgrep-first compact merge. No answer labels are inputs."""
from . import selection, tokens
from .records import require

def merge(first,second,order):
    require(order in ('one-one','two-one','colgrep-first'),'The merge order is not registered.')
    weights = (2,1) if order=='two-one' else ((max(1,len(first)),max(1,len(second))) if order=='colgrep-first' else (1,1))
    offsets=[0,0];result=[];seen=set()
    while offsets[0]<len(first) or offsets[1]<len(second):
        for index,rows in enumerate((first,second)):
            stop=min(len(rows),offsets[index]+weights[index])
            for row in rows[offsets[index]:stop]:
                key=selection.key(row)
                if key not in seen:result.append(dict(row));seen.add(key)
            offsets[index]=stop
    return result


def assemble(source,candidates,question,stages):
    policy=selection.POLICY
    text=f'Task:\n{question}\n\nRetrieved source evidence:\n'
    require(tokens.tokens(text)<=4000,'The question exceeds the total token limit.')
    spans=[];used={};cache={};trace=[]
    ranks={}
    for n,row in enumerate(candidates,1):ranks.setdefault(selection.key(row),n)
    for stage,phase,rows,total_limit in stages:
        require(phase in ('compact','context') and total_limit in (2400,4000),'The allocation stage is not registered.')
        item_limit=policy['compact_tokens_per_candidate'] if phase=='compact' else policy['context_tokens_per_candidate']
        for stage_rank,row in enumerate(rows,1):
            key=selection.key(row);require(key in ranks,'A stage introduced a new source range.')
            path=row['path']
            if path not in cache:cache[path]=selection.source_lines(source/path)
            lines=cache[path];start=row['start'];end=min(row['end'],len(lines))
            if start>end:continue
            anchor,verified=selection.anchor_line(lines,row,start,end)
            if phase=='compact':begin,finish=anchor,min(end,anchor+policy['compact_lines']-1)
            else:begin,finish=selection.context_window(lines,start,end,question)
            groups=[]
            for n in range(begin,finish+1):
                if n in used.setdefault(path,set()):continue
                if not groups or n!=groups[-1][-1]+1:groups.append([n])
                else:groups[-1].append(n)
            before=tokens.tokens(text);added='';selected=[];stops=[]
            for group in groups:
                chosen=[]
                for n in group:
                    trial=chosen+[n]
                    part=f'{path}:{trial[0]}-{n} [source]\n'+''.join(lines[k-1] for k in trial)+'\n'
                    item_tokens=tokens.tokens(added+part);total_tokens=tokens.tokens(text+added+part)
                    if item_tokens>item_limit or total_tokens>total_limit:
                        stops.append(dict(line=n,candidate_limit=item_tokens>item_limit,total_limit=total_tokens>total_limit))
                        break
                    chosen=trial
                if chosen:
                    added+=f'{path}:{chosen[0]}-{chosen[-1]} [source]\n'+''.join(lines[k-1] for k in chosen)+'\n'
                    span=dict(path=path,start=chosen[0],end=chosen[-1]);selected.append(span);used[path].update(chosen)
            text+=added;spans.extend(selected)
            trace.append(dict(stage=stage,phase=phase,candidate_rank=ranks[key],stage_rank=stage_rank,
                path=path,start=start,end=end,source_anchor=anchor,anchor_verified=verified,
                requested_start=begin,requested_end=finish,tokens_before=before,tokens_after=tokens.tokens(text),
                phase_token_limit=total_limit,spans=selected,stops=stops))
    require(tokens.tokens(text)<=4000,'The source evidence exceeds the total limit.')
    return text,spans,trace



def select(source, colgrep, other, question):
    rows = merge(colgrep, other, 'one-one')
    stages = [('colgrep-compact','compact',colgrep,2400),
              ('other-compact','compact',other,4000),
              ('context','context',rows,4000)]
    return rows, assemble(source, rows, question, stages)
