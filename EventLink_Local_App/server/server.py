import json, os, sqlite3, secrets, socket, time, csv, mimetypes
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parent.parent; DB=ROOT/'server'/'eventlink.db'; DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
PORT=int(os.environ.get('EVENTLINK_PORT','8765')); USERS={}; MESSAGES=[]; LOGS=[]; ALERTS=[]; NEXT=1
ROOMS=['GENERAL','EC','COUNCIL','HEADS','MEMBERS','LOGISTICS','SECURITY','REGISTRATION','MEDIA','TECHNICAL','EMERGENCY']
EVENT={'id':secrets.token_hex(8),'name':os.environ.get('EVENTLINK_NAME','EVENTLINK LOCAL'),'code':f'{secrets.randbelow(1000000):06d}','host_token':secrets.token_urlsafe(18),'created':int(time.time()),'duration_hours':13}
def db():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,user_id INTEGER,name TEXT,platform TEXT,join_time INTEGER,approval_time INTEGER,leave_time INTEGER,room TEXT,status TEXT,reconnect_count INTEGER)'); c.execute('CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY,ts INTEGER,user TEXT,action TEXT,detail TEXT)'); c.commit(); return c
def log(user,action,detail=''):
 ts=int(time.time()); LOGS.append({'ts':ts,'user':user,'action':action,'detail':detail})
 with db() as c:c.execute('INSERT INTO logs(ts,user,action,detail) VALUES(?,?,?,?)',(ts,user,action,detail));c.commit()
def ip():
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
 try:s.connect(('192.0.2.1',80));x=s.getsockname()[0]
 except:x='127.0.0.1'
 finally:s.close()
 return x
def out(h,o,status=200):
 b=json.dumps(o,ensure_ascii=False).encode();h.send_response(status);h.send_header('Content-Type','application/json');h.send_header('Content-Length',str(len(b)));h.send_header('Cache-Control','no-store');h.end_headers();h.wfile.write(b)
def inp(h):
 n=int(h.headers.get('Content-Length','0'));return json.loads(h.rfile.read(n) or b'{}')
def user(uid):
 try:return USERS.get(int(uid))
 except:return None
def ok(u):return bool(u and u['status']=='approved')
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def file(self,p,typ=None,download=False):
  p=Path(p)
  if not p.exists():return out(self,{'error':'not found'},404)
  b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',typ or mimetypes.guess_type(p.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b))); 
  if download:self.send_header('Content-Disposition',f'attachment; filename="{p.name}"')
  self.end_headers();self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path); path=p.path
  if path=='/':return self.file(ROOT/'client'/'index.html','text/html')
  if path=='/app.js':return self.file(ROOT/'client'/'app.js','application/javascript')
  if path=='/styles.css':return self.file(ROOT/'client'/'styles.css','text/css')
  if path=='/api/health':return out(self,{'ok':True,'internet_required':False})
  if path=='/api/status':
   return out(self,{'event':EVENT,'online':sum(1 for u in USERS.values() if ok(u) and u.get('online')),'pending':[u for u in USERS.values() if u['status']=='pending'],'users':list(USERS.values()),'rooms':ROOMS})
  if path=='/api/messages':
   room=parse_qs(p.query).get('room',['GENERAL'])[0];return out(self,{'messages':[m for m in MESSAGES if m['room']==room][-200:]})
  if path=='/api/logs':
   with db() as c:r=c.execute('SELECT ts,user,action,detail FROM logs ORDER BY id DESC LIMIT 300').fetchall()
   return out(self,{'logs':[dict(ts=a,user=b,action=c,detail=d) for a,b,c,d in r]})
  if path=='/data/attendance.csv':return self.file(DATA/'attendance.csv','text/csv',True)
  return out(self,{'error':'not found'},404)
 def do_POST(self):
  global NEXT
  path=urlparse(self.path).path
  try:d=inp(self)
  except:return out(self,{'ok':False,'error':'invalid json'},400)
  if path=='/api/join':
   if str(d.get('code','')).strip()!=EVENT['code']:return out(self,{'ok':False,'error':'Incorrect event code'},403)
   name=str(d.get('name','')).strip()[:40];platform=str(d.get('platform','Unknown'))[:30]
   if not name:return out(self,{'ok':False,'error':'Name is required'},400)
   u={'id':NEXT,'name':name,'platform':platform,'status':'pending','online':True,'room':'GENERAL','join_time':int(time.time()),'reconnect_count':0};USERS[NEXT]=u;NEXT+=1;log(name,'JOIN_REQUEST',platform);return out(self,{'ok':True,'user_id':u['id']})
  if path in ('/api/approve','/api/deny'):
   if d.get('host_token')!=EVENT['host_token']:return out(self,{'ok':False,'error':'Host token invalid'},403)
   u=user(d.get('user_id'))
   if not u:return out(self,{'ok':False,'error':'User not found'},404)
   if path.endswith('approve'):u['status']='approved';u['approval_time']=int(time.time());u['online']=True;log(u['name'],'APPROVED');
   else:u['status']='denied';u['online']=False;log(u['name'],'DENIED')
   if u['status']=='approved':
    with db() as c:c.execute('INSERT INTO attendance(user_id,name,platform,join_time,approval_time,room,status,reconnect_count) VALUES(?,?,?,?,?,?,?,?)',(u['id'],u['name'],u['platform'],u['join_time'],u.get('approval_time'),u['room'],'Present',0));c.commit()
   return out(self,{'ok':True})
  if path=='/api/message':
   u=user(d.get('user_id'))
   if not ok(u):return out(self,{'ok':False,'error':'Not approved'},403)
   room=str(d.get('room','GENERAL')).upper();room=room if room in ROOMS else 'GENERAL';text=str(d.get('text','')).strip()[:2000]
   if not text:return out(self,{'ok':False,'error':'Empty message'},400)
   m={'id':secrets.token_hex(8),'ts':int(time.time()),'user_id':u['id'],'user':u['name'],'room':room,'text':text};MESSAGES.append(m);return out(self,{'ok':True,'message':m})
  if path=='/api/action':
   u=user(d.get('user_id'));a=str(d.get('action','')).upper()
   if not ok(u):return out(self,{'ok':False,'error':'Not approved'},403)
   if a not in ('POKE','CODE GREEN','CODE RED','CODE BLACK'):return out(self,{'ok':False,'error':'Invalid action'},400)
   log(u['name'],a,u['room']);m={'id':secrets.token_hex(8),'ts':int(time.time()),'user_id':0,'user':'SYSTEM','room':u['room'],'text':f'{a} • {u["name"]}'};MESSAGES.append(m);ALERTS.append({'ts':m['ts'],'action':a,'user':u['name']});return out(self,{'ok':True})
  if path=='/api/room':
   u=user(d.get('user_id'));room=str(d.get('room','GENERAL')).upper()
   if not ok(u) or room not in ROOMS:return out(self,{'ok':False,'error':'Invalid room'},403)
   u['room']=room;log(u['name'],'ROOM_CHANGE',room);return out(self,{'ok':True})
  if path=='/api/heartbeat':
   u=user(d.get('user_id'))
   if u:u['online']=True
   return out(self,{'ok':True})
  if path=='/api/export':
   if d.get('host_token')!=EVENT['host_token']:return out(self,{'ok':False,'error':'Host token invalid'},403)
   p=DATA/'attendance.csv'
   with db() as c,p.open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Name','Platform','Join Time','Approval Time','Leave Time','Room','Status','Reconnect Count']);w.writerows(c.execute('SELECT name,platform,join_time,approval_time,leave_time,room,status,reconnect_count FROM attendance ORDER BY id'))
   return out(self,{'ok':True,'file':'/data/attendance.csv'})
  return out(self,{'ok':False,'error':'not found'},404)
def main():
 db().close();x=ip();print('\n'+'='*60);print('EVENTLINK LOCAL — WINDOWS EVENT SERVER');print('='*60);print('Event code :',EVENT['code']);print('Host token :',EVENT['host_token']);print(f'Local URL  : http://{x}:{PORT}');print(f'PC URL     : http://127.0.0.1:{PORT}');print('Internet   : optional / not required');print('='*60);ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
if __name__=='__main__':main()
