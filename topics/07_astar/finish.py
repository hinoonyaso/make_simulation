import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'output';A=json.loads((R/'assets/audio/manifest.json').read_text());S=json.loads((R/'storyboard.json').read_text());D=json.loads((O/'trace.json').read_text())
chapters=[dict(seconds=next(a['start'] for a in A if a['chapter']==i),title=ch['title']) for i,ch in enumerate(S['chapters'])];ends=[next(a['end'] for a in reversed(A) if a['chapter']==i) for i in range(8)];total=A[-1]['end']
meta=';FFMETADATA1\n'
for ch,end in zip(chapters,ends):meta+=f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(ch["seconds"]*1000)}\nEND={round(end*1000)}\ntitle={ch["title"]}\n'
(O/'chapters.ffmeta').write_text(meta)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(O/'manim/videos/lesson/1080p30/AStarLesson.mp4'),'-i',str(O/'narration.wav'),'-f','ffmetadata','-i',str(O/'chapters.ffmeta'),'-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-t',str(total),'-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(O/'astar_education_ko.mp4')],check=True)
im=Image.new('RGB',(1280,720),'#F7F9FC');draw=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
def text(x,y,t,size,color='#26364A'):draw.text((x,y),t,font=ImageFont.truetype(font,size),fill=color)
text(60,40,'A*',135,'#147DAD');text(65,220,'최단 경로는',67);text(65,310,'어떻게 찾을까?',66);text(65,555,'f = g + h',63,'#198868')
size=39;ox=760;oy=160
for y in range(D['height']):
 for x in range(D['width']):
  rect=(ox+x*size,oy+y*size,ox+(x+1)*size-3,oy+(y+1)*size-3)
  fill='#586B80' if [x,y] in D['blocked'] else '#FFFFFF';draw.rectangle(rect,fill=fill,outline='#D1DBE6')
points=[(ox+(x+.5)*size-1.5,oy+(y+.5)*size-1.5) for x,y in D['astar']['path']];draw.line(points,fill='#198868',width=8)
for node,label,color in [(D['start'],'S','#198868'),(D['goal'],'G','#B75057')]:
 x=ox+node[0]*size;y=oy+node[1]*size;draw.rectangle((x,y,x+size-3,y+size-3),fill=color);text(x+7,y+1,label,27,'#FFFFFF')
text(845,560,'START  →  GOAL',29,'#147DAD');im.save(O/'thumbnail.png')
desc='SLAM으로 지도를 만들고 AMCL로 위치를 찾았다면, 이제 경로를 계획할 차례입니다. A*가 g+h로 후보를 선택하고 Open/Closed를 갱신하며, 부모 노드를 역추적해 최단 경로를 얻는 과정을 실제 계산 기록으로 보여줍니다.\n\n'
for ch in chapters:
 t=int(ch['seconds']);desc+=f'{t//60:02d}:{t%60:02d} {ch["title"]}\n'
desc+='\n직접 구현한 교육용 12×9 정적 격자 탐색입니다. 상하좌우 4방향, 모든 이동 비용 1, 통과 불가능한 장애물, Manhattan 휴리스틱을 사용합니다. g는 현재 발견한 최선 경로 비용, h는 남은 비용의 하한 추정, f=g+h입니다. 이 휴리스틱은 일관적이므로 Closed를 다시 열지 않는 구현에서도 최적성을 유지합니다. 목표를 처음 발견할 때가 아니라 최소 f로 Open에서 꺼낼 때 종료합니다.\n\n같은 지도: A*와 Dijkstra 모두 최단 비용 16. 유효하게 꺼낸 칸 수(시작·목적지 포함)는 A* 41 / Dijkstra 89입니다. 시간 성능 벤치마크가 아닙니다. 지도, 휴리스틱, 동점 처리에 따라 수가 달라집니다. A* 동점은 작은 h, 그 다음 삽입 순서로 처리하며, 이웃 순서는 오른쪽·위·아래·왼쪽입니다. 예시 칸 (5,5)의 g=5, h=7, f=12도 같은 실행에서 나온 값입니다.\n\n빈 격자 비용 10, 장애물 격자 비용 16, 도달 불가능한 목표를 별도로 검증했고 독립 BFS 결과와 최단 비용을 비교했습니다. 영상은 지도 위 탐색 계산이며 실제 로봇 주행이 아닙니다. 로봇 크기·회전 반경·동적 장애물·costmap inflation·controller는 이 격자 모형에 구현하지 않았습니다.\n\nNav2에서는 점유 지도와 센서 등을 바탕으로 구성한 global costmap을 선택된 플래너가 사용합니다. NavFn의 use_astar 같은 설정을 통해 A*를 선택할 수 있습니다. 본 영상은 Nav2/NavFn 구현 재현이 아닙니다. Global Path와 실제 속도 명령을 구분하며 다음 Nav2 편으로 연결합니다.\n\n이전 편\nSLAM: https://www.youtube.com/watch?v=VGIooUDrPbM\nAMCL: https://www.youtube.com/watch?v=ZrRFR6ma-QY\n\n참고 자료\nhttps://www.redblobgames.com/pathfinding/a-star/introduction.html\nhttps://docs.nav2.org/rolling/configuration_and_development/configuration_guide/planners_plugins/configuring_navfn/\n\n한국어 합성 내레이션, Whisper 자막 정렬, Manim 원본 애니메이션을 사용했습니다.\n#AStar #경로탐색 #로봇 #Nav2 #ROS2 #알고리즘\n'
package=dict(video='../output/astar_education_ko.mp4',title='A*는 어떻게 최단 경로를 찾을까? | 로봇 경로 계획',description=desc,privacy='public',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../output/subtitles.ko.srt',caption_language='ko',thumbnail='../output/thumbnail.png',made_for_kids=False,contains_synthetic_media=False,tags=['A*','AStar','경로 탐색','로봇','Nav2','ROS2','Manim'],chapters=chapters)
(R/'publish/package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2));(O/'youtube_description.txt').write_text(desc);(O/'timeline.json').write_text(json.dumps(dict(chapters=chapters,ends=ends,duration=total,playback='Narration-paced recorded algorithm events, not real-time robot motion'),ensure_ascii=False,indent=2));print('Finished',total)
