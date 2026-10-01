import unittest
from test_operational_lead import Tests as Base
import continuous_cycle as cycle
import kanban as k

class ResumeTests(Base):
    def test_working_candidate_requires_honest_checkpoint_then_takeover(self):
        with self.r.transaction() as s:
            s['kanban']['cards']['T0']['attempts']['attempt']['state']='WORKING'
        packet=cycle.join(self.r,'author')
        self.assertEqual(packet['state'],'CHECKPOINT_FOR_COORDINATION')
        self.assertIsNone(self.r.readonly()['kanban'].get('operational_lead'))
        k.park(self.r,dict(packet['park_template'],checkpoint='No writes; preserved existing files'))
        self.assertEqual(cycle.join(self.r,'author')['state'],'OPERATIONAL_LEAD_ASSIGNED')

if __name__=='__main__':unittest.main()
