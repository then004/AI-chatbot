import unittest
from core.agent import run_agent

class AgentTests(unittest.TestCase):
    def test_scenarios(self):
        ev=type('R',(),{'search':lambda s,q:[{'source':'x','page':1,'text':'evidence'}]})()
        self.assertEqual(run_agent(lambda c:{'action':'ask_user','params':{}},'x').status,'waiting_input')
        empty=type('R',(),{'search':lambda s,q:[]})()
        self.assertEqual(run_agent(lambda c:{'action':'search_knowledge','params':{'query':'x'}},'x',empty).stop_reason,'no_evidence')
        self.assertEqual(run_agent(lambda c:{'action':'calculate_budget','params':{'price':1,'units':1,'variable_cost':2,'fixed_cost':1}},'x').stop_reason,'invalid_budget')
        self.assertEqual(run_agent(lambda c:{'action':'evil'},'x').stop_reason,'invalid_action')
        seq2=iter([{'action':'search_knowledge','params':{'query':'x'}},{'action':'search_knowledge','params':{'query':'x'}}]); self.assertEqual(run_agent(lambda c:next(seq2),'x',ev).stop_reason,'repeated_action')
        self.assertEqual(run_agent(lambda c:{'action':'search_knowledge','params':{'query':'x'}},'x',ev,max_steps=1).stop_reason,'step_limit')
        seq=iter([{'action':'search_knowledge','params':{'query':'x'}},{'action':'calculate_budget','params':{'price':10,'units':2,'variable_cost':2,'fixed_cost':1}},{'action':'finish_report','params':{}}])
        r=run_agent(lambda c:next(seq),'x',ev); self.assertEqual(r.status,'succeeded'); self.assertFalse(r.fallback)
        self.assertEqual(run_agent(lambda c:{'action':'search_knowledge','params':{'extra':1}},'x',ev).stop_reason,'invalid_params')
        self.assertEqual(run_agent(lambda c:{'action':'finish_report','params':{}},'x',ev).stop_reason,'missing_prerequisites')
        calls=iter(['not-json', {'action':'ask_user','params':{}}]); fixed=run_agent(lambda c:next(calls),'x'); self.assertEqual(fixed.status,'waiting_input'); self.assertTrue(any(x['action']=='format_repair' for x in fixed.trace))

if __name__=='__main__': unittest.main()
