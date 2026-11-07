"""Task187: offline invented examples, NOT recovered plan186 or owner VM data."""
import copy,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ci/terraform'))
import state_only_policy as policy
import drift_projection as projection
from automation_policy import ReviewError
from test_terraform_policy import fixture,CANARY
import test_terraform_automation as previous

CONTROL='yandex_compute_instance.k8s["k8s-control-1"]'
WORKER='yandex_compute_instance.k8s["k8s-worker-2"]'


def empty():return {'version':'state-only-v1','drift':[],'outputs':[]}


def observed(plan,address,key,before,after):
    for section in ('before','after'):
        next(x for x in plan['resource_changes'] if x['address']==address)['change'][section][key]=copy.deepcopy(after)
    for state in (plan['prior_state']['values'],plan['planned_values']):
        next(x for x in state['root_module']['resources'] if x['address']==address)['values'][key]=copy.deepcopy(after)
    drift=next((x for x in plan.setdefault('resource_drift',[]) if x['address']==address),None)
    if drift is None:
        drift=copy.deepcopy(next(x for x in plan['resource_changes'] if x['address']==address))
        drift['change']['actions']=['update'];plan['resource_drift'].append(drift)
    drift['change']['before'][key]=copy.deepcopy(before)
    drift['change']['after'][key]=copy.deepcopy(after)
    return drift


def labels_fixture(before=None,after=None,address=CONTROL):
    after={} if after is None else after
    plan=fixture();observed(plan,address,'labels',before,after)
    manifest=empty();manifest['drift']=[{'address':address,'path':['labels'],'before':copy.deepcopy(before),'after':copy.deepcopy(after)}]
    return plan,manifest


class PathTests(unittest.TestCase):
    def test_known_node_map_keys_are_parsed_in_exact_output_context(self):
        for node in sorted(policy.NODE_KEYS):
            for leaf in ('external_ip','internal_ip'):
                policy.validate_path('outputs','k8s_nodes',[node,leaf])

    def test_unsafe_node_keys_contexts_and_traversal(self):
        for target,path in [('synthetic',['k8s-worker-2','external_ip']),
                            ('k8s_nodes',['k8s-worker-9','external_ip']),
                            ('k8s_nodes',[CANARY,'external_ip']),
                            ('k8s_nodes',['../k8s-worker-2','external_ip']),
                            ('k8s_nodes',['k8s-worker-2','metadata']),
                            ('k8s_nodes',['k8s-worker-2','external_ip','nested']),
                            ('k8s_nodes',['*','external_ip']),('k8s_nodes',[])]:
            with self.assertRaises(ReviewError):policy.validate_path('outputs',target,path)
        for path in [['__class__'],['..'],['*'],[True],[0],[-1],[10000],['labels',CANARY],['nested','k8s-worker-2'],['a']*13]:
            with self.assertRaises(ReviewError):policy.validate_path('drift',CONTROL,path)

    def test_valid_network_path_does_not_authorize_output_reconciliation(self):
        for node in sorted(policy.NODE_KEYS):
            manifest=empty();manifest['outputs']=[{'name':'k8s_nodes','path':[node,'external_ip'],
                'before':'SYNTHETIC_OLD','after':None}]
            with self.assertRaisesRegex(ReviewError,'PROTECTED_PATH'):policy.manifest_gate(manifest)


class StructuralTests(unittest.TestCase):
    def test_explicit_null_empty_map_exact_rules_in_both_directions(self):
        for address in sorted(policy.LABEL_TARGETS):
            for before,after in [(None,{}),({},None)]:
                plan,manifest=labels_fixture(before,{},address)
                # Use observed() explicitly for the nullable reverse direction.
                observed(plan,address,'labels',before,after)
                manifest['drift'][0].update(before=before,after=after)
                decision=policy.approve(plan,manifest)
                self.assertTrue(decision['state_changes'])
                self.assertNotIn(CANARY,json.dumps(decision))

    def test_capability_does_not_grant_empty_production_manifest(self):
        plan,_=labels_fixture()
        with self.assertRaises(ReviewError):policy.approve(plan,empty())
        self.assertEqual(json.loads((ROOT/'ci/terraform/apply-policy.json').read_text()),empty())

    def test_container_type_contents_unknown_and_wrong_locations_fail(self):
        for after in ([],[1],{'team':'x'},{'private':CANARY},'',False,0):
            plan,manifest=labels_fixture(after=after)
            with self.assertRaises(ReviewError):policy.approve(plan,manifest)
        for address in ('yandex_vpc_network.diplom','yandex_alb_virtual_host.diplom'):
            plan,manifest=labels_fixture(address=address)
            with self.assertRaises(ReviewError):policy.approve(plan,manifest)
        for key in ('before_sensitive','after_sensitive','after_unknown'):
            plan,manifest=labels_fixture();plan['resource_drift'][0]['change'][key]={'labels':True}
            with self.assertRaises(ReviewError):policy.approve(plan,manifest)

    def test_structural_approval_cannot_cover_nonempty_or_insert_delete(self):
        for before,after in [(None,{'x':1}),({}, {'x':1}),({'x':1},{}),([],['x'])]:
            plan,manifest=labels_fixture()
            observed(plan,CONTROL,'labels',before,after)
            # Leave manifest exactly null->{} to prove value/shape binding.
            with self.assertRaises(ReviewError):policy.approve(plan,manifest)
        plan,manifest=labels_fixture();manifest['outputs']=[{'name':'synthetic','path':[], 'before':None,'after':{}}]
        with self.assertRaises(ReviewError):policy.approve(plan,manifest)

    def test_exact_address_path_direction_rules_and_native_action_required(self):
        for mutation in ('target','path','before','after','action','unused'):
            plan,manifest=labels_fixture()
            if mutation=='target':manifest['drift'][0]['address']='yandex_alb_http_router.diplom'
            if mutation=='path':manifest['drift'][0]['path']=['authority']
            if mutation=='before':manifest['drift'][0]['before']={};manifest['drift'][0]['after']=None
            if mutation=='after':manifest['drift'][0]['after']={'x':1}
            if mutation=='action':plan['resource_changes'][0]['change']['actions']=['update']
            if mutation=='unused':plan.pop('resource_drift')
            with self.assertRaises(ReviewError):policy.approve(plan,manifest)


class LifecycleTests(unittest.TestCase):
    def test_preemptible_marker_owner_stopped_never_implies_permission(self):
        # These are INVENTED transitions, not the withheld values from186.
        plan=fixture()
        observed(plan,WORKER,'scheduling_policy',[{'preemptible':True}],[{'preemptible':True}])
        observed(plan,WORKER,'status','running','stopped')
        observed(plan,WORKER,'network_interface',[{'nat_ip_address':'SYNTHETIC_OLD'}],[{'nat_ip_address':None}])
        plan['output_changes']={'k8s_nodes':{'actions':['update'],'before':{'k8s-worker-2':{'external_ip':'SYNTHETIC_OLD'}},
            'after':{'k8s-worker-2':{'external_ip':None}},'after_unknown':False}}
        with self.assertRaises(ReviewError):policy.approve(plan,empty())
        for path in (['status'],['scheduling_policy',0,'preemptible'],['network_interface',0,'nat_ip_address'],['id']):
            manifest=empty();manifest['drift']=[{'address':WORKER,'path':path,'before':'SYNTHETIC_OLD','after':None}]
            with self.assertRaisesRegex(ReviewError,'PROTECTED_PATH'):policy.manifest_gate(manifest)

    def test_state_only_noop_actions_still_required_for_structural_rule(self):
        for actions in (['create'],['update'],['delete'],['delete','create'],['create','delete']):
            plan,manifest=labels_fixture();plan['resource_changes'][0]['change']['actions']=actions
            with self.assertRaises(ReviewError):policy.approve(plan,manifest)


class ProjectionTests(unittest.TestCase):
    def project(self,plan):
        result=projection.project(plan);text=json.dumps(result)
        for value in (CANARY,'192.0.2.1','192.0.2.2','SYNTHETIC_OLD','SSH_PRIVATE_DATA'):
            self.assertNotIn(value,text)
        self.assertFalse(result['policy_approval'])
        return result

    def test_shapes_disambiguate_null_empty_and_nonempty_without_contents(self):
        for after,expected in [({},'EMPTY_MAP'),({'team':CANARY},'NONEMPTY_MAP'),([],'EMPTY_ARRAY'),([CANARY],'NONEMPTY_ARRAY')]:
            plan,_=labels_fixture(after=after)
            row=self.project(plan)['rows'][0]
            self.assertEqual(row['before_shape'],'NULL');self.assertEqual(row['after_shape'],expected)
            self.assertEqual(row['values'],'WITHHELD')

    def test_pinned_schema_paths_and_hyphen_output_projection(self):
        path=('http_backend',0,'healthcheck',0,'http_healthcheck',0,'expected_statuses')
        tokens,vetted=projection.path_projection(path,projection.BACKEND)
        self.assertTrue(vetted);self.assertEqual(tokens,list(path))
        path=('route',0,'http_route',0,'http_route_action',0,'upgrade_types')
        self.assertTrue(projection.path_projection(path,projection.VIRTUAL_HOST)[1])
        self.assertTrue(projection.path_projection(('subnet_ids',),projection.NETWORK)[1])
        plan=fixture();plan['output_changes']={'k8s_nodes':{'actions':['update'],
            'before':{'k8s-worker-2':{'external_ip':'192.0.2.1'}},'after':{'k8s-worker-2':{'external_ip':'192.0.2.2'}}}}
        row=self.project(plan)['rows'][0]
        self.assertEqual(row['path'],['k8s-worker-2','external_ip'])
        self.assertEqual(row['category'],'PROTECTED_IDENTITY_OR_NETWORK')

    def test_status_categories_are_not_permission_or_raw_values(self):
        plan=fixture();observed(plan,WORKER,'status','running','stopped')
        row=self.project(plan)['rows'][0]
        self.assertEqual((row['before_status_category'],row['after_status_category']),('KNOWN_RUNNING','KNOWN_STOPPED'))
        self.assertEqual(row['category'],'UNKNOWN');self.assertFalse(row['policy_approval'])
        observed(plan,WORKER,'status',CANARY,'SSH_PRIVATE_DATA')
        row=self.project(plan)['rows'][0]
        self.assertEqual(row['before_status_category'],'UNRECOGNIZED_WITHHELD')

    def test_sensitive_unknown_maps_ssh_and_status_do_not_leak_shapes(self):
        for key in ('before_sensitive','after_sensitive','after_unknown'):
            plan,_=labels_fixture();plan['resource_drift'][0]['change'][key]=True
            row=self.project(plan)['rows'][0]
            self.assertEqual(row['before_shape'],'WITHHELD');self.assertEqual(row['after_shape'],'WITHHELD')
        plan=fixture();observed(plan,WORKER,'metadata',{CANARY:'SSH_PRIVATE_DATA'},{CANARY:'SSH_PRIVATE_DATA_CHANGED'})
        result=self.project(plan);self.assertNotIn('SSH_PRIVATE_DATA_CHANGED',json.dumps(result))
        self.assertEqual(result['rows'][0]['category'],'SENSITIVE_WITHHELD')
        self.assertIn('<unvetted-key>',result['rows'][0]['path'])
        plan=fixture();d=observed(plan,WORKER,'status','running','stopped');d['change']['after_sensitive']=True
        self.assertEqual(self.project(plan)['rows'][0]['before_status_category'],'WITHHELD')

    def test_untrusted_schema_and_output_names_masked(self):
        plan=fixture();observed(plan,WORKER,CANARY,None,{'status':CANARY})
        row=self.project(plan)['rows'][0];self.assertEqual(row['path'],['<unvetted-key>'])
        self.assertEqual(row['after_shape'],'WITHHELD')
        plan=fixture();plan['output_changes']={CANARY:{'actions':['update'],'before':None,'after':CANARY}}
        self.assertEqual(self.project(plan)['rows'][0]['alias'],'<unreviewed-output>')

    def test_noop_resource_changes_and_nonempty_drift_remain_separate(self):
        plan,_=labels_fixture();result=self.project(plan)
        self.assertEqual(result['actions'],{'no-op':14});self.assertEqual(result['drift_count'],1)
        self.assertEqual(result['output_change_count'],0)
        self.assertEqual(len(result['rows']),1)

    def test_projection_survives_policy_denial_without_second_native_call(self):
        testcase=previous.AutomationTests()
        plan,_=labels_fixture()
        error,_,progress,calls,_=testcase.simulate(mode='apply',plan=plan,exitcode=2)
        self.assertIsNotNone(error);self.assertNotIn('apply',calls)
        self.assertEqual(calls.count('plan'),1)
        self.assertEqual(progress['drift_review']['rows'][0]['after_shape'],'EMPTY_MAP')
        self.assertNotIn(CANARY,json.dumps(progress))

    def test_nested_dynamic_keys_and_false_vs_zero(self):
        self.assertEqual(list(projection.diffs([False],[0]))[0][0],(0,))
        tokens,vetted=projection.path_projection(('labels',CANARY,'status'),projection.COMPUTE)
        self.assertFalse(vetted);self.assertNotIn(CANARY,json.dumps(tokens))

if __name__=='__main__':unittest.main()
