"""Display summaries without altering stored sets or their identifiers."""

def summarize_sets(records):
    groups = {}
    for row in records:
        key = (row['day'], row['exercise'], row['weight'], row['reps'])
        if key not in groups:
            groups[key] = dict(zip(('day', 'exercise', 'weight', 'reps'), key), sets=0)
        groups[key]['sets'] += 1
    return list(groups.values())
