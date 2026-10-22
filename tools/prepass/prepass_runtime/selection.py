"""The retained compact source policy and native match decoder."""
from __future__ import annotations
import math
from pathlib import Path
import re
from .records import PrepassError as TrialError

POLICY = dict(version=1, global_matches=30, compact_lines=8, compact_tokens_per_candidate=120,
              compact_total_tokens=2400, context_lines=20, context_tokens_per_candidate=320,
              total_tokens=4000, candidate_order='Native file order; three matches per file in stable score order; 30 ranges total.',
              anchor='First source declaration with the native match name inside the match range; otherwise match start.',
              context='Twenty-line window with most whole-word question-term matches; earliest window breaks ties.',
              source_languages='Python and Go declaration recognition. Other source ranges start at the match start.')


def key(row):
    return row['path'], row['start'], row['end']


def source_lines(path):
    # Native coordinates count LF bytes. Keep CRLF and Unicode separators intact.
    parts = Path(path).read_bytes().decode('utf-8').split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def native_pool(raw, native_source, source, paths):
    """Retain every returned native match, its score, name, and provenance."""
    if not isinstance(raw, list): raise TrialError('The native JSON must contain a list.')
    pool, cache = [], {}
    for file_rank, row in enumerate(raw, 1):
        unit = row['unit']; path = Path(unit['file'])
        if path.is_absolute():
            try: path = path.relative_to(native_source)
            except ValueError as exc: raise TrialError('A native match is outside its registered source.') from exc
        name = str(path)
        if name not in paths: raise TrialError(f'A native match is outside the tracked inventory: {name}')
        if name not in cache: cache[name] = len((source / name).read_bytes().split(b'\n'))
        matches = row.get('matches') or [dict(line=unit['line'], end_line=unit['end_line'],
                                             score=row['score'], name=unit.get('name', ''))]
        for match_rank, match in enumerate(matches, 1):
            start, end, score = match['line'], match['end_line'], match.get('score', 0)
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= cache[name]:
                raise TrialError('A native match has an invalid source range.')
            if type(score) not in (int, float) or not math.isfinite(score):
                raise TrialError('A native match has an invalid score.')
            match_name = match.get('name') or ''
            if not isinstance(match_name, str): raise TrialError('A native match name is invalid.')
            pool.append(dict(path=name, start=start, end=end, score=score, name=match_name,
                             file_rank=file_rank, match_rank=match_rank))
    return pool


def anchor_line(lines, row, start, end):
    """Use a name from the native response, then verify the declaration in source."""
    name = row.get('name')
    if name and Path(row['path']).suffix == '.py':
        pattern = r'^\s*(?:async\s+)?(?:def|class)\s+' + re.escape(name) + r'\b'
    elif name and Path(row['path']).suffix == '.go':
        pattern = r'^\s*(?:func\s+(?:\([^)]*\)\s*)?|type\s+|var\s+|const\s+)' + re.escape(name) + r'\b'
    else:
        return start, False
    matches = [n for n in range(start, end + 1) if re.match(pattern, lines[n - 1])]
    return (matches[0], True) if matches else (start, False)


def context_window(lines, start, end, question):
    length = POLICY['context_lines']
    if end - start + 1 <= length: return start, end
    terms = set(re.findall(r'[a-zA-Z_]{3,}', question.lower())) - set('the where does which are from and'.split())
    weights = [len(terms.intersection(re.findall(r'[a-zA-Z_]{3,}', line.lower()))) for line in lines[start - 1:end]]
    offset = max(range(len(weights) - length + 1), key=lambda i: sum(weights[i:i + length]))
    return start + offset, start + offset + length - 1
