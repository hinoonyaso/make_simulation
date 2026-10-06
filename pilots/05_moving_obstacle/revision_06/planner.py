"""Local educational A* and closed-loop path tracker. No Nav2 implementation."""
import heapq,math
GRID=.05
ROBOT_RADIUS=.25
MARGIN=.22
DRUM_RADIUS=.3
WALL_Y=1.45
GOAL=(1.3,0.)

def clearance(x,y,known):
    return min(WALL_Y-abs(y),2.5-abs(x),math.hypot(x,y)-DRUM_RADIUS if known else float('inf'))

def plan(start,known):
    def cell(p):return tuple(round(x/GRID) for x in p)
    def point(p):return (p[0]*GRID,p[1]*GRID)
    s=cell(start);g=cell(GOAL);q=[(0,0,s)];cost={s:0.};parents={};closed=set();serial=0
    def valid(p):return clearance(*point(p),known)>ROBOT_RADIUS+MARGIN
    while q:
        _,_,p=heapq.heappop(q)
        if p in closed:continue
        closed.add(p)
        if p==g:
            route=[p]
            while p!=s:p=parents[p];route.append(p)
            return [list(point(c)) for c in reversed(route)]
        for dx,dy in [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            n=(p[0]+dx,p[1]+dy)
            if not valid(n) or (dx and dy and (not valid((p[0]+dx,p[1])) or not valid((p[0],p[1]+dy)))):continue
            candidate=cost[p]+math.hypot(dx,dy)*GRID
            if candidate<cost.get(n,float('inf')):
                cost[n]=candidate;parents[n]=p;serial+=1
                heapq.heappush(q,(candidate+math.dist(point(n),GOAL),serial,n))
    return []

def command(pose,path):
    x,y,yaw=pose
    if math.dist((x,y),GOAL)<.055:return 0.,0.,list(GOAL),'goal_reached'
    if not path:return 0.,0.,None,'no_path_stop'
    i=min(range(len(path)),key=lambda k:math.dist((x,y),path[k]));j=i;length=0
    while j<len(path)-1 and length<.30:length+=math.dist(path[j],path[j+1]);j+=1
    target=path[j];angle=math.atan2(target[1]-y,target[0]-x)-yaw;angle=(angle+math.pi)%(2*math.pi)-math.pi
    w=max(-1.,min(1.,2.2*angle))
    v=min(.20,.65*math.dist((x,y),GOAL))*max(0.,math.cos(angle))
    if abs(angle)>.8:v=0.
    return v,w,target,'tracking'
