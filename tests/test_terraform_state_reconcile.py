"""Task188 active policy. Synthetic examples, all native/API calls mocked."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ci/terraform'))
import state_reconcile_policy as active
import state_only_policy as historical
import run_automation as runner
from automation_policy import ReviewError
from test_terraform_policy import fixture,CANARY
from test_terraform_state_paths import observed
import test_terraform_automation as previous


def refresh_fixture():
    """Invented9/1 shape, NOT a recreation of deleted plan186 values."""
    plan=fixture()
    labels={*(f'yandex_compute_instance.k8s["{n}"]' for n in ('k8s-control-1','k8s-worker-1','k8s-worker-2')),
        'yandex_alb_backend_group.k8s_ingress','yandex_alb_http_router.diplom',
        'yandex_alb_load_balancer.diplom','yandex_alb_target_group.k8s_workers'}
    for address in sorted(labels):observed(plan,address,'labels',None,{'synthetic-label':CANARY})
    observed(plan,'yandex_alb_backend_group.k8s_ingress','http_backend',None,[{'healthcheck':[{'http_healthcheck':[{'expected_statuses':[200]}]}]}])
    observed(plan,'yandex_alb_virtual_host.diplom','authority',None,[])
    observed(plan,'yandex_vpc_network.diplom','subnet_ids',[],['SYNTHETIC_SUBNET'])
    worker='yandex_compute_instance.k8s["k8s-worker-2"]'
    observed(plan,worker,'status','running','stopped')
    observed(plan,worker,'network_interface',[{'nat_ip_address':'192.0.2.1'}],[{'nat_ip_address':None}])
    plan['output_changes']={'k8s_nodes':{'actions':['update'], 'before':{'k8s-worker-2':{'external_ip':'192.0.2.1'}},
        'after':{'k8s-worker-2':{'external_ip':None}}, 'after_unknown':False}}
    return plan


class ActivePolicyTests(unittest.TestCase):
    def test_noop_resources_nonzero_drift_outputs_allowed_without_manifest(self):
        plan=refresh_fixture();summary=active.review(plan)
        self.assertEqual((summary['actions'],summary['drift_count'],summary['output_change_count']),({'no-op':14},9,1))
        decision=active.approve(plan)
        self.assertTrue(decision['state_changes'])
        self.assertEqual(decision['policy_version'],'managed-noop-state-refresh-v1')
        self.assertNotIn(CANARY,json.dumps(decision))
        self.assertNotIn('192.0.2.1',json.dumps(decision))

    def test_output_only_create_update_delete_noop(self):
        for actions,before,after in [(['create'],None,{'x':1}),(['update'],{'x':1},{'x':2}),(['delete'],{'x':1},None),(['no-op'],{'x':1},{'x':1})]:
            plan=fixture();plan['output_changes']={'synthetic':{'actions':actions,'before':before,'after':after}}
            self.assertEqual(active.approve(plan)['state_changes'],actions!=['no-op'])

    def test_managed_actions_writes_deny_even_with_historic_manifest_rules(self):
        for actions in (['create'],['update'],['delete'],['create','delete'],['delete','create'],['forget'],['read']):
            plan=refresh_fixture();plan['resource_changes'][0]['change']['actions']=actions
            with self.assertRaises(ReviewError):active.approve(plan)

    def test_unknown_sensitive_each_change_channel_denied(self):
        for section in ('resource_changes','resource_drift','output_changes'):
            for marker in ('before_sensitive','after_sensitive','after_unknown'):
                plan=refresh_fixture();change=(plan[section][0]['change'] if section!='output_changes' else next(iter(plan[section].values())))
                change[marker]={'nested':[False,True]}
                with self.assertRaises(ReviewError):active.approve(plan)
        for section in ('prior_state','planned_values'):
            plan=fixture();values=plan[section]['values'] if section=='prior_state' else plan[section]
            values['root_module']['resources'][0]['sensitive_values']={'metadata':True}
            with self.assertRaises(ReviewError):active.approve(plan)
            plan=fixture();values=plan[section]['values'] if section=='prior_state' else plan[section]
            values['outputs']={'synthetic':{'value':CANARY,'sensitive':True}}
            with self.assertRaises(ReviewError):active.approve(plan)

    def test_malformed_scope_identity_moves_import_unknowns_checks(self):
        for kind in ('schema','complete','version','provider','address','duplicate','id','move','import','missing','checks','deferred','drift_action','unknown_field'):
            plan=refresh_fixture()
            if kind=='schema':plan['format_version']='999'
            if kind=='complete':plan['complete']=False
            if kind=='version':plan['terraform_version']='1.0'
            if kind=='provider':plan['resource_drift'][0]['provider_name']='untrusted'
            if kind=='address':plan['resource_drift'][0]['address']='unknown.resource'
            if kind=='duplicate':plan['resource_drift'].append(copy.deepcopy(plan['resource_drift'][0]))
            if kind=='id':plan['resource_drift'][0]['change']['before']['id']='different'
            if kind=='move':plan['resource_changes'][0]['previous_address']='old.resource'
            if kind=='import':plan['resource_changes'][0]['change']['importing']={'id':'synthetic'}
            if kind=='missing':del plan['resource_changes'][0]['change']['after']
            if kind=='checks':plan['checks']=[{'status':'unknown'}]
            if kind=='deferred':plan['deferred_changes']=[{}]
            if kind=='drift_action':plan['resource_drift'][0]['change']['actions']=['delete']
            if kind=='unknown_field':plan['unexpected_top_field']=True
            with self.assertRaises(ReviewError):active.approve(plan)

    def test_false_noop_values_and_inconsistent_output_actions_deny(self):
        plan=fixture();plan['resource_changes'][0]['change']['after']['private']='different'
        with self.assertRaises(ReviewError):active.approve(plan)
        for actions,before,after in [(['no-op'],1,2),(['create'],1,2),(['delete'],1,2),(['delete','create'],None,2)]:
            plan=fixture();plan['output_changes']={'synthetic':{'actions':actions,'before':before,'after':after}}
            with self.assertRaises(ReviewError):active.approve(plan)

    def test_not_applyable_unknown_missing_flag_denied(self):
        for flag in (False, None, 'unknown'):
            plan=refresh_fixture();plan['applyable']=flag
            with self.assertRaises(ReviewError):active.approve(plan)
        plan=refresh_fixture();del plan['applyable']
        with self.assertRaises(ReviewError):active.approve(plan)


class RuntimeTests(unittest.TestCase):
    simulate=previous.AutomationTests.simulate
    def test_full_refresh_applies_one_same_saved_plan_no_historic_gate(self):
        with patch.object(historical,'approve',side_effect=AssertionError('Historical gate must be inactive')),patch.object(runner,'command',wraps=runner.command) as commands:
            error,result,progress,calls,heads=self.simulate('apply',refresh_fixture(),2)
        self.assertIsNone(error);self.assertEqual(calls,['version','init','validate','plan','show','apply'])
        paths={stage:str(call.args[1]) for call in commands.call_args_list if (stage:=call.args[0]) in ('plan','show','apply')}
        self.assertEqual(len(set(paths.values())),1)
        self.assertEqual(result['status'],'SAVED_PLAN_APPLY_EXIT_0')
        self.assertEqual(result['cleanup'],'COMPLETED');self.assertEqual(heads,4)
        self.assertEqual(progress['commands'][3]['returncode'],2)
        self.assertNotIn(CANARY,json.dumps(progress));self.assertNotIn('192.0.2.1',json.dumps(progress))

    def test_drift_only_refresh_even_when_native_plan_reports_zero(self):
        plan=refresh_fixture();plan['output_changes']={}
        error,result,_,calls,_=self.simulate('apply',plan,0)
        self.assertIsNone(error);self.assertEqual(result['status'],'SAVED_PLAN_APPLY_EXIT_0')
        self.assertEqual(calls.count('apply'),1)

    def test_true_empty_noop_skips_fake_apply(self):
        error,result,_,calls,_=self.simulate('apply',fixture(),0)
        self.assertIsNone(error);self.assertEqual(result['status'],'NO_CHANGES_APPLY_SKIPPED')
        self.assertNotIn('apply',calls)

    def test_writes_stop_before_apply_and_keep_redacted_evidence(self):
        for actions in (['create'],['update'],['delete'],['delete','create']):
            plan=refresh_fixture();plan['resource_changes'][0]['change']['actions']=actions
            error,_,progress,calls,_=self.simulate('apply',plan,2)
            self.assertEqual(error,'RESOURCE_ACTION');self.assertNotIn('apply',calls)
            self.assertEqual(calls.count('plan'),1);self.assertEqual(progress['cleanup'],'COMPLETED')

    def test_sensitive_unknown_failed_apply_or_lock_no_retry(self):
        for problem in ('sensitive','unknown','lock','error','timeout'):
            plan=refresh_fixture();options={}
            if problem=='sensitive':next(iter(plan['output_changes'].values()))['after_sensitive']=True
            if problem=='unknown':plan['resource_drift'][0]['change']['after_unknown']=True
            if problem=='lock':options['heads']=[200,404,403,404]
            if problem=='error':options['fail']='apply'
            if problem=='timeout':options['timeout']='apply'
            error,_,progress,calls,_=self.simulate('apply',plan,2,**options)
            self.assertIsNotNone(error);self.assertEqual(calls.count('plan'),1)
            self.assertEqual(calls.count('apply'),1 if problem in ('error','timeout') else 0)
            self.assertEqual(progress['cleanup'],'COMPLETED')

if __name__=='__main__':unittest.main()
