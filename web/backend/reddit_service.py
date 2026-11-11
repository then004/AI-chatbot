import os
class RedditBlocked(Exception): pass
def reddit_configured(): return all(os.getenv(x) for x in ('REDDIT_CLIENT_ID','REDDIT_CLIENT_SECRET','REDDIT_USER_AGENT'))
def collect_posts(query, subreddits, limit=10, adapter=None):
    if not reddit_configured() and adapter is None: raise RedditBlocked('Reddit is not configured; no request was sent.')
    if adapter: return adapter(query,subreddits,limit)
    import praw
    reddit=praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],client_secret=os.environ['REDDIT_CLIENT_SECRET'],user_agent=os.environ['REDDIT_USER_AGENT'],check_for_async=False)
    return [{'title':x.title,'subreddit':str(x.subreddit),'permalink':f'https://reddit.com{x.permalink}','created':x.created_utc,'text':x.selftext[:5000]} for x in reddit.subreddit('+'.join(subreddits)).search(query,limit=limit)]
def analyze_local(posts, ollama):
    prompt='Return JSON only with keys score,pain_points,alternatives,opportunities,limitations,sources. Use only these posts: '+str([{'title':p['title'],'text':p['text'],'permalink':p['permalink']} for p in posts])
    result=ollama(prompt)
    if not isinstance(result,dict): raise ValueError('Ollama analysis was not a JSON object')
    result['sources']=[p['permalink'] for p in posts]; return result
def run_research(query, subreddits, limit, reddit_adapter, ollama_adapter):
    posts=collect_posts(query,subreddits,limit,adapter=reddit_adapter)
    if not posts: raise ValueError('no Reddit posts collected')
    return {'sources':posts,'analysis':analyze_local(posts,ollama_adapter)}
def praw_adapter(query, subreddits, limit, profile='fast'):
    if not reddit_configured(): raise RedditBlocked('Reddit credentials are not configured')
    import praw
    reddit=praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],client_secret=os.environ['REDDIT_CLIENT_SECRET'],user_agent=os.environ['REDDIT_USER_AGENT'],check_for_async=False)
    per_profile={'fast':min(limit,10),'standard':min(limit,30),'deep':min(limit,60)}; out=[]
    for sub in subreddits:
        for x in reddit.subreddit(sub).search(query,limit=per_profile.get(profile,10),sort='relevance'):
            comments=[]
            try:
                x.comments.replace_more(limit=0)
                comments=[getattr(c,'body','')[:1000] for c in list(x.comments)[:3]]
            except Exception: pass
            out.append({'title':x.title,'subreddit':str(x.subreddit),'permalink':f'https://reddit.com{x.permalink}','created':x.created_utc,'text':(x.selftext or '')[:5000],'comments':comments})
    return out
