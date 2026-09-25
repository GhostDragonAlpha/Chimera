"""Ten model-agent registrations and reports; not task/worktree/resource authority."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time

from integrity import unique_object, reject_constant

DEFAULT_ROOT = Path('E:/ChimeraWork/monkey-coordination')
PHASES = {'claim','derive','implement','numerical','runtime','visual','review','integrate','resource_wait','blocked','finished'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def local_time(stamp):
    return datetime.fromtimestamp(stamp,timezone.utc).astimezone().isoformat()


def text(value, name):
    require(isinstance(value,str) and 0 < len(value.strip()) <= 2000, 'invalid_'+name)
    return value


def check_instruction_revision(arguments, current):
    require(arguments.get('instruction_revision')==current['revision_id'] and
            arguments.get('instruction_bundle_sha256')==current['bundle_sha256'],
            'LEAD_UPDATE_REQUIRED: Read E:/PythonChimera/docs/MONKEY_RUN.md and its current bundle; '
            'apply the instructions and record your own acknowledgement, then retry this same assignment '
            'with instruction_revision='+current['revision_id']+' and instruction_bundle_sha256='+current['bundle_sha256']+
            '. Existing claims remain intact; do not ask the operator for a new task.')


class Registry:
    def __init__(self, root, clock=time.time):
        self.root = Path(root)
        self.path = self.root/'agent_slots.sqlite3'
        self.clock = clock

    def expire(self, state):
        stamp = self.clock()
        for slot in state['slots']:
            if slot['agent_id'] is not None and slot.get('lease_state') == 'ACTIVE' and stamp >= slot['deadline_unix']:
                slot['lease_state'] = 'EXPIRED_RECOVERY_REQUIRED'
                slot['expired_at_utc'] = datetime.fromtimestamp(stamp,timezone.utc).isoformat()
                self.event(state,'hour_boundary_expired',{'slot':slot['slot'],'generation':slot['generation'],
                    'next_action':'Confirm worker cessation and preserve work before release; do not infer process exit'})

    @contextmanager
    def transaction(self):
        require(self.path.is_file(), 'registry_not_initialized')
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.execute('BEGIN IMMEDIATE')
            state = json.loads(connection.execute('SELECT payload FROM state WHERE id=1').fetchone()[0])
            self.expire(state)
            yield state
            connection.execute('UPDATE state SET payload=? WHERE id=1',(json.dumps(state),))
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        self.root.mkdir(parents=True,exist_ok=True)
        connection = sqlite3.connect(self.path,timeout=10)
        try:
            connection.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
            state = {'schema':'chimera.agent_slot_registry.v1','mode':'AWAITING_RECONCILIATION',
                     'capacity':10,'revision':0,'coordinator_report':None,'instruction_ack':None,
                     'heartbeat_policy':'NEXT_TOP_OF_HOUR; no renewal by reporting; mid-hour registration gets the remainder',
                     'display_clock':'Windows system local time; operator specifies Central Time; UTC retained for unambiguous identity',
                     'slots':[{'slot':i,'generation':0,'agent_id':None,'phase':'unregistered'} for i in range(1,11)],
                     'recent_events':[]}
            connection.execute('INSERT OR IGNORE INTO state VALUES (1,?)',(json.dumps(state),))
            connection.commit()
        finally:
            connection.close()
        return self.snapshot()

    @staticmethod
    def event(state, action, detail):
        state['revision'] += 1
        state['recent_events'].append({'revision':state['revision'],'at_utc':now(),'action':action,'detail':detail})
        state['recent_events'] = state['recent_events'][-100:]

    def register(self, a):
        # Enforce at the shared deployment, not merely in prose. Isolated test/recovery
        # stores are not the production instruction authority.
        if self.root.absolute()==DEFAULT_ROOT.absolute() and not a.get('adopt_existing'):
            from instruction_state import inspect
            check_instruction_revision(a,inspect(Path(__file__).resolve().parents[2]))
        for key in ('agent_id','task_id','ownership_reference','workspace','checkpoint','next_action','instruction_revision','instruction_bundle_sha256'):
            text(a.get(key),key)
        require(a.get('phase') in PHASES, 'invalid_phase')
        require(isinstance(a.get('memory',{}),dict) and len(json.dumps(a.get('memory',{}))) <= 16000,
                'invalid_slot_memory')
        with self.transaction() as state:
            require(state['mode']=='ACTIVE' or a.get('adopt_existing') is True,
                    'reconcile_existing_agents_before_new_dispatch')
            require(not any(s['agent_id']==a['agent_id'] for s in state['slots']), 'agent_already_registered')
            free = [s for s in state['slots'] if s['agent_id'] is None]
            require(free, 'all_ten_agent_slots_occupied')
            slot = free[0]
            generation = slot['generation']+1
            stamp = self.clock()
            window_start = int(stamp // 3600) * 3600
            deadline = window_start + 3600
            slot.update({k:a[k] for k in ('agent_id','task_id','ownership_reference','workspace','checkpoint','next_action','instruction_revision','instruction_bundle_sha256','phase')})
            slot.update(generation=generation,last_report_utc=now(),last_action=a.get('last_action','registered'),
                        evidence_reference=a.get('evidence_reference'),lease_state='ACTIVE',
                        heartbeat_window_start_unix=window_start,deadline_unix=deadline,
                        deadline_utc=datetime.fromtimestamp(deadline,timezone.utc).isoformat(),
                        deadline_local=local_time(deadline),
                        heartbeat_window_utc=datetime.fromtimestamp(window_start,timezone.utc).isoformat(),
                        heartbeat_window_local=local_time(window_start),
                        memory=a.get('memory',{}))
            self.event(state,'register',{'slot':slot['slot'],'generation':generation,'agent_id':a['agent_id']})
            result = dict(slot)
        self.snapshot()
        return result

    @staticmethod
    def owned(state,a):
        require(type(a.get('slot')) is int and 1 <= a['slot'] <= 10, 'invalid_slot')
        slot = state['slots'][a['slot']-1]
        require(slot['agent_id'] is not None and slot['agent_id']==a.get('agent_id')
                and type(a.get('generation')) is int and slot['generation']==a['generation'],
                'stale_or_wrong_agent_registration')
        return slot

    def report(self,a):
        require(a.get('phase') in PHASES, 'invalid_phase')
        for key in ('checkpoint','last_action','next_action','instruction_revision','instruction_bundle_sha256'):
            text(a.get(key),key)
        with self.transaction() as state:
            slot = self.owned(state,a)
            require(slot.get('lease_state')=='ACTIVE','assignment_expired_checkpoint_in_recovery')
            for key in ('phase','checkpoint','last_action','next_action','instruction_revision','instruction_bundle_sha256'):
                slot[key]=a[key]
            slot.update(last_report_utc=now(),evidence_reference=a.get('evidence_reference'))
            if 'memory' in a:
                require(isinstance(a['memory'],dict) and len(json.dumps(a['memory'])) <= 16000,'invalid_slot_memory')
                slot['memory']=a['memory']
            self.event(state,'report',{'slot':slot['slot'],'phase':slot['phase']})
        return self.snapshot()

    def release(self,a):
        text(a.get('preservation_reference'),'preservation_reference')
        with self.transaction() as state:
            slot = self.owned(state,a)
            require((slot['phase']=='finished' or slot.get('lease_state')=='EXPIRED_RECOVERY_REQUIRED')
                    and a.get('worker_finished_confirmed') is True,
                    'worker_completion_confirmation_required')
            self.event(state,'release',{'slot':slot['slot'],'agent_id':slot['agent_id'],
                                      'preservation_reference':a['preservation_reference']})
            number,generation=slot['slot'],slot['generation']
            handoff={k:slot.get(k) for k in ('agent_id','task_id','workspace','ownership_reference','checkpoint',
                      'last_action','next_action','evidence_reference','memory','instruction_revision','lease_state')}
            handoff['preservation_reference']=a['preservation_reference']
            slot.clear();slot.update(slot=number,generation=generation,agent_id=None,phase='unregistered',last_handoff=handoff)
        return self.snapshot()

    def reconcile(self,a):
        require(type(a.get('expected_registered_agents')) is int and 0 <= a['expected_registered_agents'] <= 10,
                'invalid_expected_count')
        text(a.get('live_inventory_reference'),'live_inventory_reference')
        with self.transaction() as state:
            actual=sum(s['agent_id'] is not None for s in state['slots'])
            require(actual==a['expected_registered_agents'],'reconciliation_count_mismatch')
            state['mode']='ACTIVE'
            state['reconciliation']={'at_utc':now(),'reported_agent_count':actual,
                                     'live_inventory_reference':a['live_inventory_reference']}
            self.event(state,'reconcile',state['reconciliation'])
        return self.snapshot()

    def coordinator(self,a):
        for key in ('coordinator_id','checkpoint','last_action','next_action','evidence_reference'):
            text(a.get(key),key)
        with self.transaction() as state:
            state['coordinator_report']={k:a[k] for k in ('coordinator_id','checkpoint','last_action','next_action','evidence_reference')}
            state['coordinator_report']['at_utc']=now()
            self.event(state,'coordinator_report',{'coordinator_id':a['coordinator_id']})
        return self.snapshot()

    def acknowledge(self,a):
        from instruction_state import inspect
        # Caller supplies its own acknowledgement. Never write one for a different agent.
        result=inspect(Path(__file__).resolve().parents[2],a)
        require(result['state']=='ACK_RECORD_MATCHES','acknowledgement_not_current')
        with self.transaction() as state:
            state['instruction_ack']=a
            self.event(state,'instruction_ack',{'coordinator_id':a['coordinator_id'],'revision_id':a['revision_id']})
        return self.snapshot()

    def snapshot(self):
        # Hold the same transaction lock while publishing the derived view. Never expose
        # a stale older writer's projection after a newer writer's projection.
        with self.transaction() as state:
            result={**state,'snapshot_at_utc':now(),
                    'snapshot_at_local':local_time(self.clock()),
                    'current_heartbeat_window_utc':datetime.fromtimestamp(int(self.clock()//3600)*3600,timezone.utc).isoformat(),
                    'current_heartbeat_window_local':local_time(int(self.clock()//3600)*3600),
                    'registered_agents':sum(s['agent_id'] is not None for s in state['slots']),
                    'limits':'Self-reported positions. Deadline checks run when this helper is invoked, not by a background timer. Expiry is not proof of process exit or revocation of native task/filesystem authority. Never reclaim a silent worker automatically.'}
            target=self.root/'STATUS.json'
            temporary=self.root/'STATUS.pending.json'
            temporary.write_text(json.dumps(result,indent=2),encoding='utf-8')
            temporary.replace(target)
        return result

    def instruction_notice(self):
        if self.root.absolute()!=DEFAULT_ROOT.absolute():return None
        from instruction_state import inspect
        try:
            current=inspect(Path(__file__).resolve().parents[2])
            return {'revision_id':current['revision_id'],'bundle_sha256':current['bundle_sha256'],
                    'entry':'E:/PythonChimera/docs/MONKEY_RUN.md',
                    'required_action':'Read this revision before new dispatch. Preserve/report/release existing work normally; acknowledge only your own actual read.'}
        except (OSError,ValueError,KeyError) as exc:
            return {'state':'POLICY_READ_FAILED','reason':str(exc),
                    'required_action':'Preserve existing work. Resolve policy integrity before new dispatch.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('action',choices=['init','status','register','report','release','reconcile','coordinator','acknowledge'])
    p.add_argument('--arguments',type=Path)
    a=p.parse_args(argv)
    try:
        registry=Registry(a.root)
        if a.action=='init':result=registry.initialize()
        elif a.action=='status':result=registry.snapshot()
        else:
            require(a.arguments is not None,'arguments_file_required')
            with a.arguments.open('rb') as stream:raw=stream.read(65537)
            require(len(raw)<=65536,'arguments_size_limit')
            data=json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)
            require(isinstance(data,dict),'arguments_must_be_object')
            result=getattr(registry,a.action)(data)
        notice=registry.instruction_notice()
        if notice is not None:result['lead_instruction_notice']=notice
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error) as exc:
        print(json.dumps({'refused':str(exc)}),file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
