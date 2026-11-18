"""Compact full topic memory for model requests; never truncates saved history."""

def prompt_history(rows):
    result=[];seen=set()
    for row in rows:
        for key in ('topic','title'):
            value=row.get(key)
            if isinstance(value,str) and value.strip():
                value=' '.join(value.split())
                if value not in seen:seen.add(value);result.append(value)
    return result
