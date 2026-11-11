import os, unittest
from unittest.mock import patch
from reddit_service import collect_posts, run_research, RedditBlocked
class RedditServiceTests(unittest.TestCase):
 def test_fake_success_preserves_source(self):
  posts=[{'title':'Pain','subreddit':'r/test','permalink':'https://reddit.com/x','created':1,'text':'slow workflow'}]; out=run_research('x',['test'],1,lambda q,s,l:posts,lambda p:{'score':7,'pain_points':['slow']}); self.assertEqual(out['sources'][0]['permalink'],'https://reddit.com/x'); self.assertEqual(out['analysis']['sources'],['https://reddit.com/x'])
 def test_no_config_does_not_call_adapter(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(RedditBlocked): collect_posts('x',['test'],1)
if __name__=='__main__': unittest.main()
