"""Validate native Zoekt bytes and select retained enclosing source ranges."""
import base64
from collections import defaultdict
import math
from pathlib import Path
from . import selection
from .records import require, PrepassError

def checked_path(value, source, paths):
    path = Path(value)
    if path.is_absolute():
        try: path = path.relative_to(source)
        except ValueError as exc: raise PrepassError('A result path is outside its source.') from exc
    name = str(path)
    require(name in paths and '..' not in path.parts, f'A result path is outside the file list: {value}')
    return name


def no_truncation(raw):
    require(all(raw.get(k,0) == 0 for k in ('Crashes','FilesSkipped','FilesSkippedDueToCancellation','ShardsSkipped')),
            'Zoekt reported a crash, cancellation, or skipped search work.')
    require(raw.get('MatchCount',0) < 100000, 'A query reached the native per-shard match limit.')


def source_lines(content):
    parts = content.split(b'\n')
    return [part+b'\n' for part in parts[:-1]]+([parts[-1]] if parts[-1] else [])


def zoekt_hits(raw, source, paths, eligible=None):
    no_truncation(raw)
    files, all_hits = [], set()
    for file in raw.get('Files') or []:
        path = checked_path(file['FileName'],source,paths)
        if eligible is not None and path not in eligible: continue
        content = (source/path).read_bytes(); lines = source_lines(content)
        offsets, offset = [], 0
        for line in lines: offsets.append(offset); offset += len(line)
        matches = file.get('LineMatches') or []
        require(len(matches) > 0, 'A content search returned a file with no line matches.')
        hits = []
        for match in matches:
            n = match['LineNumber']; score = match['Score']
            require(type(n) is int and 1 <= n <= len(lines), 'A native match line is invalid.')
            require(not match['FileName'] and type(score) in (int,float) and math.isfinite(score), 'A native match is invalid.')
            line = base64.b64decode(match['Line'],validate=True)
            require(line == lines[n-1] and match['LineStart'] == offsets[n-1]
                and match['LineEnd'] == offsets[n-1]+len(line), 'A native match does not match its source bytes.')
            hits.append(dict(line=n,score=score)); all_hits.add((path,n))
        files.append((path,sorted(hits,key=lambda r:-r['score'])))
    require(len({p for p,_ in files}) == len(files), 'A native result repeats a file.')
    return files, all_hits


def candidates(files, outlines, source):
    by_path = defaultdict(list)
    for row in outlines: by_path[row['path']].append(row)
    result = []
    for path,hits in files:
        seen = set(); count = len(source_lines((source/path).read_bytes()))
        for hit in hits:
            n = hit['line']; enclosing = [r for r in by_path[path] if r['start'] <= n <= r['end']]
            if enclosing:
                row = dict(min(enclosing,key=lambda r:(r['end']-r['start'],-r['start'],r['name'])))
            else: row = dict(path=path,start=max(1,n-3),end=min(count,n+37),name='')
            key = selection.key(row)
            if key in seen: continue
            seen.add(key); result.append(dict(row,hit_line=n,score=hit['score']))
            if len(result) == 30: return result
            if len(seen) == 3: break
    return result
