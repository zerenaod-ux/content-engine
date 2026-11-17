import ast,unittest
from pathlib import Path
source=ast.parse(Path('ce_publisher.py').read_text())
function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='newest_waiting')
ns={};exec(compile(ast.Module(body=[function],type_ignores=[]),'ce_publisher.py','exec'),ns)
class PriorityTests(unittest.TestCase):
    def test_latest_unscheduled_approval_first_without_moving_existing_posts(self):
        items=[{'tag':'old','reviewed_at':'2026-11-16T10:00:00+00:00'},{'tag':'new','reviewed_at':'2026-11-17T10:00:00+00:00'},{'tag':'fixed','reviewed_at':'2026-11-18T10:00:00+00:00'}]
        state={'done':{'fixed/youtube':{'remote':'already-scheduled'}}}
        result=ns['newest_waiting'](items,state,'youtube')
        self.assertEqual([x['tag'] for x in result],['new','old'])
        self.assertEqual(state['done']['fixed/youtube']['remote'],'already-scheduled')
        self.assertEqual([x['tag'] for x in ns['newest_waiting'](items,state,'instagram')],['fixed','new','old'])
