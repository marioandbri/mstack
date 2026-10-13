import json,pathlib,re,sys
r=pathlib.Path(sys.argv[1]); out=r/'review'; out.mkdir(exist_ok=True)
for result in json.loads((r/'results.json').read_text()):
 p=r/result['id']; items=[]; selected=[]
 for line in (p/'events.jsonl').read_text().splitlines():
  event=json.loads(line)
  if event.get('method')!='item/completed': continue
  item=event['params']['item']; typ=item.get('type')
  if typ=='commandExecution':
   cmd=item.get('command',''); output=item.get('aggregatedOutput','')
   selected.extend(re.findall(r'/root/\.agents/skills/([^/\s]+)/SKILL\.md',cmd))
   items.append({'type':typ,'command':cmd,'exitCode':item.get('exitCode'),'output':output})
  elif typ in ['agentMessage','fileChange','mcpToolCall','collabAgentToolCall']:
   items.append(item)
 record={'id':result['id'],'status':result['status'],'selectedSkills':sorted(set(selected)),'items':items}
 (out/(result['id']+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print(result['id'],result['status'],'skills='+','.join(record['selectedSkills']))
