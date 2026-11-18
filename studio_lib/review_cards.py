"""Read all retained review pages before deciding a delivery card is absent."""

def find_by_marker(api,label,marker):
    for page in range(1,11):
        rows=api('GET','issues?state=all&labels='+label+'&per_page=100&page='+str(page))
        if not isinstance(rows,list):raise ValueError('Review card lookup unavailable; refuse duplicate creation')
        found=next((x for x in rows if marker in (x.get('body') or '')),None)
        if found:return found
        if len(rows)<100:return None
    raise ValueError('Review history exceeds lookup bound; refuse duplicate creation')
