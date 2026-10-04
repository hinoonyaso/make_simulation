"""A* and Dijkstra over one deterministic unit-cost four-connected grid."""
from pathlib import Path
import heapq,itertools,json
from collections import deque
R=Path(__file__).resolve().parent
W,H=12,9;START=(1,4);GOAL=(10,3)
BLOCKED={(6,y) for y in range(1,8)}|{(3,y) for y in range(5,8)}|{(9,6),(10,6)}
def neighbors(n,blocked=BLOCKED):
 for dx,dy in [(1,0),(0,-1),(0,1),(-1,0)]:
  v=n[0]+dx,n[1]+dy
  if 0<=v[0]<W and 0<=v[1]<H and v not in blocked:yield v

def heuristic(n,goal=GOAL):return abs(n[0]-goal[0])+abs(n[1]-goal[1])
def search(use_h=True,blocked=BLOCKED,start=START,goal=GOAL):
 tick=itertools.count();g={start:0};parents={};closed=set();opened={start};h=lambda n:heuristic(n,goal) if use_h else 0
 heap=[(h(start),h(start),next(tick),0,start)];rows=[]
 while heap:
  _,_,_,queued,n=heapq.heappop(heap)
  if n in closed or queued!=g[n]:continue
  candidates=[dict(node=list(v),g=g[v],h=h(v),f=g[v]+h(v)) for v in sorted(opened,key=lambda v:(g[v]+h(v),h(v),v))]
  opened.remove(n);closed.add(n);changes=[]
  if n!=goal:
   for v in neighbors(n,blocked):
    if v in closed:continue # Manhattan is consistent for unit-cost cardinal edges.
    tentative=g[n]+1
    if tentative<g.get(v,float('inf')):
     old=g.get(v);g[v]=tentative;parents[v]=n;opened.add(v);changes.append(dict(node=list(v),old_g=old,new_g=tentative,parent=list(n)))
     heapq.heappush(heap,(tentative+h(v),h(v),next(tick),tentative,v))
  rows.append(dict(step=len(rows),current=list(n),g=g[n],h=h(n),f=g[n]+h(n),candidates=candidates,open=[list(v) for v in sorted(opened)],closed=[list(v) for v in sorted(closed)],updates=changes,parents=[dict(node=list(k),parent=list(v)) for k,v in sorted(parents.items())]))
  if n==goal:
   path=[goal]
   while path[-1]!=start:path.append(parents[path[-1]])
   return dict(rows=rows,path=[list(v) for v in path[::-1]],cost=g[goal],selected_nodes=len(rows),expanded_before_goal=len(rows)-1)
 return dict(rows=rows,path=[],cost=None,selected_nodes=len(rows),expanded_before_goal=len(rows))

def reference_distance(blocked=BLOCKED,start=START,goal=GOAL):
 q=deque([(start,0)]);seen={start}
 while q:
  u,d=q.popleft()
  if u==goal:return d
  for v in neighbors(u,blocked):
   if v not in seen:seen.add(v);q.append((v,d+1))
 return None
if __name__=='__main__':
 a=search();d=search(False);clear=search(blocked=set());unreachable=search(blocked=BLOCKED|set(neighbors(GOAL)))
 assert a['cost']==d['cost']==reference_distance()
 assert clear['cost']==heuristic(START)
 assert unreachable['cost'] is None and not unreachable['path']
 for row in a['rows']:
  assert row['f']==row['g']+row['h']
  assert row['f']==min(c['f'] for c in row['candidates'])
  assert not set(map(tuple,row['open']))&set(map(tuple,row['closed']))
 for u,v in zip(a['path'],a['path'][1:]):assert tuple(v) in neighbors(tuple(u))
 for x in range(W):
  for y in range(H):
   for v in neighbors((x,y)):assert heuristic((x,y))<=1+heuristic(v)
 chosen=next((r for r in a['rows'] if r['g']==5 and r['h']==7),a['rows'][5])
 metrics=dict(path_cost=a['cost'],astar_selected=a['selected_nodes'],dijkstra_selected=d['selected_nodes'],unobstructed_cost=clear['cost'],unreachable_check='passed',cell_example={k:chosen[k] for k in ['step','current','g','h','f']})
 doc=dict(width=W,height=H,start=START,goal=GOAL,blocked=sorted(BLOCKED),move_cost=1,connectivity=4,tie_break='lowest f, then lowest h, then insertion order; neighbors right, up, down, left',astar=a,dijkstra=d,clear=clear,metrics=metrics)
 (R/'output/trace.json').write_text(json.dumps(doc));(R/'output/model_validation.json').write_text(json.dumps(metrics,indent=2));print(metrics)
