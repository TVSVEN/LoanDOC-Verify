from __future__ import annotations
import hashlib, hmac, json, mimetypes, os, re, secrets, sqlite3, uuid, webbrowser
from datetime import datetime, timedelta, timezone
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT=Path(__file__).parent; DATA=Path(os.environ.get('DATA_DIR',str(ROOT/'data'))); UPLOADS=DATA/'uploads'; DB=DATA/'loandocverify.sqlite3'; PORT=int(os.environ.get('PORT','8000')); HOST=os.environ.get('HOST','127.0.0.1')
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)
try:
 from pypdf import PdfReader
except Exception: PdfReader=None

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def uid(): return str(uuid.uuid4())
def pw_hash(password,salt=None):
 salt=salt or secrets.token_hex(16); return salt+'$'+hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),240000).hex()
def pw_valid(password,stored):
 try:salt,digest=stored.split('$',1); return hmac.compare_digest(pw_hash(password,salt).split('$',1)[1],digest)
 except Exception:return False
def token_hash(token):return hashlib.sha256(token.encode()).hexdigest()
def storage_path(p):
 p=p.resolve()
 try:return str(p.relative_to(ROOT.resolve()))
 except ValueError:return str(p)
def stored_file(value):
 p=Path(value)
 return p if p.is_absolute() else ROOT/p
def connect():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init_db():
 rahul_evidence_added=False
 with connect() as c:
  c.executescript((ROOT/'database/schema.sql').read_text(encoding='utf-8'))
  cols={r['name'] for r in c.execute('pragma table_info(applications)')}
  if 'owner_user_id' not in cols:c.execute("alter table applications add column owner_user_id TEXT NOT NULL DEFAULT 'demo'")
  user_cols={r['name'] for r in c.execute('pragma table_info(users)')}
  if 'role' not in user_cols:c.execute("alter table users add column role TEXT NOT NULL DEFAULT 'applicant'")
  if not c.execute('select 1 from applications limit 1').fetchone(): seed(c)
  if not c.execute("select 1 from documents where application_id='demo-rahul-sharma' and document_type='Employment Proof'").fetchone():
   name='employment_demo.txt'; raw=b'Employment Proof\nEmployee: Rahul Sharma\nEmployer: Northstar Analytics\nEmployment Status: Active'; p=UPLOADS/('demo-rahul-sharma-'+name); p.write_bytes(raw); f=extract(raw,name,'Employment Proof'); c.execute('insert into documents values(?,?,?,?,?,?,?,?,?,?,?)',(uid(),'demo-rahul-sharma',name,'Employment Proof',storage_path(p),hashlib.sha256(raw).hexdigest(),len(raw),'Readable','Processed',json.dumps(f),now()));rahul_evidence_added=True
  for row in DEMO_CASES:
   if not c.execute('select 1 from applications where id=?',(row['id'],)).fetchone(): seed_case(c,row)
 for row in DEMO_CASES:
  if not application(row['id'])['checks']:
   verify(row['id'])
 if rahul_evidence_added:verify('demo-rahul-sharma')
 elif not application('demo-rahul-sharma')['checks']:verify('demo-rahul-sharma')
def seed(c):
 aid='demo-rahul-sharma'; t=now()
 c.execute('insert into applications(id,applicant_name,dob,phone,email,loan_type,requested_amount,declared_income,employer,employment_type,purpose,status,created_at,owner_user_id) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(aid,'Rahul Sharma','1994-06-12','+91 90000 10001','rahul.demo@example.test','Personal Loan',500000,75000,'Northstar Analytics','Salaried','Home renovation','Needs clarification',t,'demo'))
 samples=[('pan_demo.txt','PAN','PAN\nName: Rahul Sharma\nPAN: ABCDE1234F\nDOB: 12/06/1994'),('aadhaar_demo.txt','Aadhaar','Identity Proof\nName: Rahul Sharma\nDOB: 12/06/1994\nAadhaar: XXXX XXXX 1234'),('salary_jan_demo.txt','Salary Slip','Salary Slip\nEmployee: Rahul Sharma\nEmployer: Northstar Analytics\nMonth: January 2026\nGross Salary: 85000\nNet Salary: 75000'),('salary_feb_demo.txt','Salary Slip','Salary Slip\nEmployee: Rahul Sharma\nEmployer: Northstar Analytics\nMonth: February 2026\nGross Salary: 85000\nNet Salary: 75000'),('salary_mar_demo.txt','Salary Slip','Salary Slip\nEmployee: Rahul Sharma\nEmployer: Northstar Analytics\nMonth: March 2026\nGross Salary: 85000\nNet Salary: 75000'),('bank_demo.txt','Bank Statement','Bank Statement\nAccount Holder: Rahul Sharma\nBank: Demo National Bank\nStatement Period: January 2026 to May 2026\nSalary Credit January 2026: 61000\nSalary Credit February 2026: 61000\nSalary Credit April 2026: 61000\nSalary Credit May 2026: 61000'),('employment_demo.txt','Employment Proof','Employment Proof\nEmployee: Rahul Sharma\nEmployer: Northstar Analytics\nEmployment Status: Active')]
 for name,typ,txt in samples:
  p=UPLOADS/(aid+'-'+name); raw=txt.encode(); p.write_bytes(raw); extracted=extract(raw,name,typ)
  c.execute('insert into documents values(?,?,?,?,?,?,?,?,?,?,?)',(uid(),aid,name,typ,storage_path(p),hashlib.sha256(raw).hexdigest(),len(raw),'Readable','Processed',json.dumps(extracted),t))
 log(c,aid,'Orchestrator','Demo case created','Synthetic Rahul Sharma data is ready for the verification walkthrough.','Complete')
DEMO_CASES=[
 {'id':'demo-ananya-rao','name':'Ananya Rao','dob':'2001-02-18','type':'Education Loan','amount':400000,'income':58000,'employer':'Cedar Labs','status':'Verified','purpose':'Tuition fees','docs':[('pan_ananya.txt','PAN','PAN\nName: Ananya Rao\nPAN: QWERT1234Y'),('aadhaar_ananya.txt','Aadhaar','Identity Proof\nName: Ananya Rao\nDOB: 18/02/2001'),('salary_ananya.txt','Salary Slip','Salary Slip\nEmployee: Ananya Rao\nEmployer: Cedar Labs\nNet Salary: 58000'),('bank_ananya.txt','Bank Statement','Bank Statement\nAccount Holder: Ananya Rao\nStatement Period: January 2026 to June 2026\nSalary Credit January 2026: 58000\nSalary Credit February 2026: 58000\nSalary Credit March 2026: 58000\nSalary Credit April 2026: 58000\nSalary Credit May 2026: 58000\nSalary Credit June 2026: 58000'),('employment_ananya.txt','Employment Proof','Employment Proof\nEmployee: Ananya Rao\nEmployer: Cedar Labs')]},
 {'id':'demo-vikram-nair','name':'Vikram Nair','dob':'1990-10-03','type':'Personal Loan','amount':800000,'income':92000,'employer':'Monsoon Retail','status':'Incomplete','purpose':'Vehicle purchase','docs':[('pan_vikram.txt','PAN','PAN\nName: Vikram Nair\nPAN: ZXCVB4321M'),('salary_vikram.txt','Salary Slip','Salary Slip\nEmployee: Vikram Nair\nEmployer: Monsoon Retail\nNet Salary: 92000'),('bank_vikram.txt','Bank Statement','Bank Statement\nAccount Holder: Vikram Nair\nStatement Period: March 2026 to May 2026\nSalary Credit March 2026: 92000\nSalary Credit April 2026: 92000\nSalary Credit May 2026: 92000')]},
 {'id':'demo-meera-iyer','name':'Meera Iyer','dob':'1988-07-29','type':'Home Loan','amount':2500000,'income':135000,'employer':'Blue Orchid Design','status':'Needs clarification','purpose':'Home purchase','docs':[('pan_meera.txt','PAN','PAN\nName: Meera Iyer\nPAN: ASDFG5678H'),('aadhaar_meera.txt','Aadhaar','Identity Proof\nName: Meera Iyer\nDOB: 29/07/1988'),('salary_meera_jan.txt','Salary Slip','Salary Slip\nEmployee: Meera Iyer\nEmployer: Blue Orchid Design\nMonth: January 2026\nNet Salary: 135000'),('salary_meera_feb.txt','Salary Slip','Salary Slip\nEmployee: Meera Iyer\nEmployer: Blue Orchid Design\nMonth: February 2026\nNet Salary: 135000'),('salary_meera_mar.txt','Salary Slip','Salary Slip\nEmployee: Meera Iyer\nEmployer: Blue Orchid Design\nMonth: March 2026\nNet Salary: 135000'),('employment_meera.txt','Employment Proof','Employment Proof\nEmployee: Meera Iyer\nEmployer: Blue Orchid Design'),('bank_meera.txt','Bank Statement','Bank Statement\nAccount Holder: M Iyer\nStatement Period: January 2026 to May 2026\nSalary Credit January 2026: 135000\nSalary Credit February 2026: 135000\nSalary Credit March 2026: 135000\nSalary Credit April 2026: 135000\nSalary Credit May 2026: 135000')]}
]
def seed_case(c,row):
 t=now(); c.execute('insert into applications(id,applicant_name,dob,phone,email,loan_type,requested_amount,declared_income,employer,employment_type,purpose,status,created_at,owner_user_id) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(row['id'],row['name'],row['dob'],None,None,row['type'],row['amount'],row['income'],row['employer'],'Salaried',row['purpose'],row['status'],t,'demo'))
 for name,typ,txt in row['docs']:
  p=UPLOADS/(row['id']+'-'+name); raw=txt.encode(); p.write_bytes(raw); f=extract(raw,name,typ)
  c.execute('insert into documents values(?,?,?,?,?,?,?,?,?,?,?)',(uid(),row['id'],name,typ,storage_path(p),hashlib.sha256(raw).hexdigest(),len(raw),'Readable','Processed',json.dumps(f),t))
 if row['status'] in ('Incomplete','Needs clarification'):
  reason='Bank statement coverage is shorter than requested.' if row['status']=='Incomplete' else 'Applicant and bank account holder names need reviewer confirmation.'
  c.execute('insert into review_cases values(?,?,?,?,?,?,?)',(uid(),row['id'],reason,'Medium','Open',None,t))
  c.execute('insert into requests values(?,?,?,?,?,?)',(uid(),row['id'],'Complete bank statement coverage' if row['status']=='Incomplete' else 'Name clarification',reason,'Open',t))
 log(c,row['id'],'Orchestrator','Synthetic demo case created',f"{row['name']} · {row['status']}",'Complete')
def log(c,aid,agent,action,detail,status='Complete'): c.execute('insert into events values(?,?,?,?,?,?,?)',(uid(),aid,agent,action,detail,status,now()))
def norm(s): return re.sub(r'[^a-z0-9]','',str(s or '').lower())
def norm_date(value):
 if not value:return None
 for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y','%d/%m/%y'):
  try:return datetime.strptime(str(value).strip(),fmt).date().isoformat()
  except ValueError:pass
 return None
def classify(name,text=''):
 s=(name+' '+text[:1000]).lower()
 for key,typ in [('pan','PAN'),('aadhaar','Aadhaar'),('aadhar','Aadhaar'),('salary','Salary Slip'),('payslip','Salary Slip'),('pay slip','Salary Slip'),('bank','Bank Statement'),('statement','Bank Statement'),('employment','Employment Proof'),('offer letter','Employment Proof')]:
  if key in s:return typ
 return 'Other'
def extract(raw,name,typ=None):
 typ=typ or classify(name); text=''
 if name.lower().endswith('.pdf') and PdfReader:
  try:
   from io import BytesIO
   text='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(raw)).pages)
  except Exception: text=''
 elif name.lower().endswith(('.txt','.csv')): text=raw.decode('utf-8','ignore')
 def get(pattern):
  m=re.search(pattern,text,re.I|re.M); return m.group(1).strip() if m else None
 f={'document_type':typ,'text_available':bool(text),'source':'PDF text' if name.lower().endswith('.pdf') else ('text file' if text else 'OCR unavailable for images')}
 f['name']=get(r'(?:name|employee|account holder)\s*[:\-]\s*([^\n]+)')
 f['dob']=get(r'(?:dob|date of birth)\s*[:\-]\s*([^\n]+)')
 f['pan']=get(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b')
 f['employer']=get(r'(?:employer|company)\s*[:\-]\s*([^\n]+)')
 f['net_salary']=number(get(r'(?:net salary|take.?home|net pay)\s*[:₹ ]+([\d,]+(?:\.\d+)?)'))
 f['gross_salary']=number(get(r'(?:gross salary|gross pay)\s*[:₹ ]+([\d,]+(?:\.\d+)?)'))
 f['account_holder']=get(r'account holder\s*[:\-]\s*([^\n]+)')
 credits=re.findall(r'(?:salary credit|salary)\s+([A-Za-z]+\s+20\d\d)\s*[:₹ ]+([\d,]+(?:\.\d+)?)',text,re.I)
 f['salary_credits']=[{'month':m,'amount':number(v)} for m,v in credits]
 period=get(r'(?:statement period|period)\s*[:\-]\s*([^\n]+)'); f['statement_period']=period
 f['pan_format_valid']=bool(f['pan'] and re.fullmatch(r'[A-Z]{5}[0-9]{4}[A-Z]',f['pan'])) if typ=='PAN' else None
 return f
def number(x):
 try:return float(str(x).replace(',','')) if x is not None else None
 except:return None
def verify(aid):
 with connect() as c:
  app=c.execute('select * from applications where id=?',(aid,)).fetchone()
  if not app: return None
  docs=c.execute('select * from documents where application_id=?',(aid,)).fetchall(); fields=[(d,json.loads(d['extracted_json'])) for d in docs]
  c.execute('delete from checks where application_id=?',(aid,))
  checks=[]
  def add(kind,result,explanation,evidence,confidence):
   row={'check_type':kind,'result':result,'explanation':explanation,'evidence':evidence,'confidence':confidence}; checks.append(row)
   c.execute('insert into checks values(?,?,?,?,?,?,?,?)',(uid(),aid,kind,result,explanation,json.dumps(evidence),confidence,now()))
   log(c,aid,'Verification tools',kind,explanation,result)
  log(c,aid,'Orchestrator','Verification started','Planning document, identity, income, coverage and anomaly checks.')
  counts={}
  for d,f in fields: counts[d['document_type']]=counts.get(d['document_type'],0)+1
  required=({'PAN':1,'Aadhaar':1,'Salary Slip':1,'Bank Statement':1,'Employment Proof':1} if app['loan_type']=='Education Loan' else {'PAN':1,'Aadhaar':1,'Salary Slip':3,'Bank Statement':1,'Employment Proof':1})
  missing=[]
  for typ,n in required.items():
   if counts.get(typ,0)<n: missing.append(typ)
  add('Required documents','Needs attention' if missing else 'Pass',('Missing or short: '+', '.join(missing)+'.' if missing else 'All configured personal-loan document categories are present.'),{'required':required,'uploaded':counts,'sources':[{'document_id':d['id'],'file_name':d['file_name'],'document_type':d['document_type']} for d,f in fields]},.99)
  pan=[f for d,f in fields if d['document_type']=='PAN' and f.get('pan')]
  if pan:
   good=pan[0]['pan_format_valid']; dpan=next(d for d,f in fields if f is pan[0]); add('PAN format','Pass' if good else 'Needs attention','Extracted PAN matches the expected 10-character structure.' if good else 'Extracted PAN does not match expected structure.',{'document_id':dpan['id'],'document':dpan['file_name'],'field':'PAN','value':pan[0]['pan']},.98)
  names=[{'document_id':d['id'],'document':d['file_name'],'field':'name','value':f['name']} for d,f in fields if f.get('name')]
  mismatches=[x for x in names if norm(x['value']) not in norm(app['applicant_name']) and norm(app['applicant_name']) not in norm(x['value'])]
  add('Identity name match','Needs attention' if mismatches else ('Pass' if names else 'Unable to verify'),'Names were compared across the application and readable documents.' if names else 'No readable name fields were extracted.',{'application':{'field':'applicant_name','value':app['applicant_name']},'sources':names,'mismatches':mismatches},.88 if names else .2)
  dobs=[{'document_id':d['id'],'document':d['file_name'],'field':'dob','value':f['dob']} for d,f in fields if f.get('dob')]
  dob_mismatches=[x for x in dobs if norm_date(x['value']) and norm_date(app['dob']) and norm_date(x['value'])!=norm_date(app['dob'])]
  add('Date of birth match','Needs attention' if dob_mismatches else ('Pass' if dobs and norm_date(app['dob']) else 'Unable to verify'),'Readable dates of birth were normalized and compared to the application.' if dobs and norm_date(app['dob']) else 'A readable date of birth was not available from both sources.',{'application':{'field':'dob','value':app['dob']},'sources':dobs,'mismatches':dob_mismatches},.9 if dobs and norm_date(app['dob']) else .2)
  employers=[{'document_id':d['id'],'document':d['file_name'],'field':'employer','value':f['employer']} for d,f in fields if f.get('employer')]
  employer_mismatches=[x for x in employers if app['employer'] and norm(x['value']) not in norm(app['employer']) and norm(app['employer']) not in norm(x['value'])]
  add('Employer consistency','Needs attention' if employer_mismatches else ('Pass' if employers and app['employer'] else 'Unable to verify'),'Employer names were compared with the application where both were readable.' if employers and app['employer'] else 'An employer name was not available from both sources.',{'application':{'field':'employer','value':app['employer']},'sources':employers,'mismatches':employer_mismatches},.84 if employers and app['employer'] else .2)
  salaries=[(d,f) for d,f in fields if d['document_type']=='Salary Slip' and f.get('net_salary') is not None]
  avg=sum(f['net_salary'] for d,f in salaries)/len(salaries) if salaries else None
  delta=abs(avg-app['declared_income'])/app['declared_income'] if avg and app['declared_income'] else None
  add('Declared vs payslip income','Needs attention' if delta is not None and delta>.1 else ('Pass' if avg else 'Unable to verify'),(f"Payslip net average is ₹{avg:,.0f} vs declared ₹{app['declared_income']:,.0f} ({delta:.0%} difference)." if avg and delta is not None else 'No readable net salary values were extracted.'),{'payslips':[{'document_id':d['id'],'document':d['file_name'],'field':'net_salary','value':f['net_salary']} for d,f in salaries],'average_net_salary':avg,'declared_income':app['declared_income'],'threshold':.1},.9 if avg else .2)
  credits=[(d,x) for d,f in fields for x in f.get('salary_credits',[])]
  avgcredit=sum(x['amount'] for d,x in credits)/len(credits) if credits else None
  gap=abs(avgcredit-avg)/avg if avg and avgcredit else None
  add('Payslip vs bank credits','Needs attention' if gap is not None and gap>.1 else ('Pass' if avgcredit else 'Unable to verify'),(f"Average identified bank salary credit is ₹{avgcredit:,.0f} compared with payslip net average ₹{avg:,.0f}. Possible explanations include deductions, split pay or incomplete coverage." if avgcredit and avg else 'Salary credits could not be compared from extracted evidence.'),{'credits':[{'document_id':d['id'],'document':d['file_name'],'field':'salary_credit','month':x['month'],'value':x['amount']} for d,x in credits],'payslip_sources':[{'document_id':d['id'],'document':d['file_name'],'field':'net_salary','value':f['net_salary']} for d,f in salaries],'average_credit':avgcredit,'average_net_salary':avg},.82 if credits else .2)
  periods=[{'document_id':d['id'],'document':d['file_name'],'period':f.get('statement_period')} for d,f in fields if f.get('statement_period')]
  observed=sorted(set(x['month'] for d,x in credits)); coverage_issue=bool(periods and len(observed)<6)
  add('Bank statement coverage','Needs attention' if coverage_issue else ('Pass' if periods else 'Unable to verify'),('Statement evidence shows '+str(len(observed))+' salary-credit months; six months are expected for this demo.' if coverage_issue else ('Statement period was extracted; month-level coverage could not be fully verified.' if periods else 'No statement period could be extracted.')),{'periods':periods,'observed_salary_credit_months':observed,'expected_months':6},.68 if periods else .2)
  duplicates=[{'document_id':d['id'],'file_name':d['file_name'],'sha256_prefix':d['file_hash'][:12]} for d in docs if c.execute('select count(*) from documents where file_hash=?',(d['file_hash'],)).fetchone()[0]>1]
  add('Duplicate file check','Needs attention' if duplicates else 'Pass','Matching SHA-256 file hashes indicate duplicate uploads.' if duplicates else 'No duplicate file hashes found in this application.',{'duplicates':duplicates},.99)
  unreadable=[{'document_id':d['id'],'file_name':d['file_name'],'quality_status':d['quality_status']} for d,f in fields if d['quality_status']!='Readable']
  add('Document readability','Needs attention' if unreadable else 'Pass','Some files need a clearer upload or OCR before their fields can be relied upon.' if unreadable else 'All submitted files supplied readable text for this run.',{'sources':unreadable or [{'document_id':d['id'],'file_name':d['file_name'],'quality_status':d['quality_status']} for d,f in fields]},.7 if unreadable else .86)
  findings=[x for x in checks if x['result']=='Needs attention']; requests=set(missing)
  if any(x['check_type']=='Payslip vs bank credits' and x['result']=='Needs attention' for x in findings): requests.add('Income clarification')
  if coverage_issue: requests.add('Complete bank statement coverage')
  requests.update('Re-upload clearer document: '+x['file_name'] for x in unreadable)
  for r in requests:
   if not c.execute("select 1 from requests where application_id=? and requested_document=? and status='Open'",(aid,r)).fetchone():c.execute('insert into requests values(?,?,?,?,?,?)',(uid(),aid,r,'Required evidence is missing or a cross-document difference needs clarification.', 'Open',now()))
  if missing or findings:
   reason='; '.join(x['check_type'] for x in findings) or 'Missing documents'
   if not c.execute("select 1 from review_cases where application_id=? and status='Open'",(aid,)).fetchone():c.execute('insert into review_cases values(?,?,?,?,?,?,?)',(uid(),aid,reason,'Medium','Open',None,now()))
  status='Incomplete' if missing else ('Needs clarification' if findings or c.execute("select 1 from review_cases where application_id=? and status='Open'",(aid,)).fetchone() else 'Verified')
  c.execute('update applications set status=? where id=?',(status,aid))
  log(c,aid,'Orchestrator','Next action selected',('Applicant clarification and human review are required.' if findings or missing else 'Checks complete; case is ready for human review.'),status)
  log(c,aid,'Report agent','Evidence report generated','Findings include source fields, confidence and suggested next action.')
  return {'application_id':aid,'status':status,'checks':checks,'requests':[dict(x) for x in c.execute('select * from requests where application_id=?',(aid,))],'events':[dict(x) for x in c.execute('select * from events where application_id=? order by created_at',(aid,))]}

def mask_sensitive(value,field=''):
 if isinstance(value,dict):
  return {k:mask_sensitive(v,('pan' if k=='value' and 'pan' in str(value.get('field','')).lower() else k)) for k,v in value.items()}
 if isinstance(value,list):return [mask_sensitive(x,field) for x in value]
 if isinstance(value,str) and field.lower() in {'pan','aadhaar','aadhaar_number','account_number','account'}:
  clean=re.sub(r'\W','',value)
  return (clean[:4]+'*'*(max(1,len(clean)-5))+clean[-1:]) if field.lower()=='pan' and len(clean)>5 else ('*'*(max(0,len(clean)-4))+clean[-4:] if len(clean)>4 else value)
 return value
def application_scope(user,alias='a'):
 if user['role']=='officer':return f"{alias}.id IN (SELECT application_id FROM application_access WHERE officer_user_id=?)",(user['id'],)
 return f'{alias}.owner_user_id=?',(user['id'],)
def owns_application(aid,user_id):
 with connect() as c:return bool(c.execute('select 1 from applications where id=? and owner_user_id=?',(aid,user_id)).fetchone())
def visible_applications(user):
 scope,params=application_scope(user)
 with connect() as c:return [dict(row) for row in c.execute(f'select a.* from applications a where {scope} order by a.created_at desc',params)]
def visible_review_cases(user):
 scope,params=application_scope(user)
 with connect() as c:return [dict(row) for row in c.execute(f"select r.*,a.applicant_name,a.loan_type from review_cases r join applications a on r.application_id=a.id where r.status='Open' and {scope} order by r.created_at desc",params)]
def visible_reports(user):
 scope,params=application_scope(user)
 with connect() as c:return [dict(row) for row in c.execute(f'select a.id as application_id,a.applicant_name,a.loan_type,a.status,max(k.created_at) as generated_at,count(k.id) as check_count from applications a left join checks k on k.application_id=a.id where {scope} group by a.id order by coalesce(max(k.created_at),a.created_at) desc',params)]
def application(aid,user_id=None):
 with connect() as c:
  a=c.execute('select * from applications where id=?'+(' and (owner_user_id=? or exists(select 1 from application_access x where x.application_id=applications.id and x.officer_user_id=?))' if user_id else ''),(aid,user_id,user_id) if user_id else (aid,)).fetchone()
  if not a:return None
  x=dict(a); x['documents']=[{**dict(d),'extracted':mask_sensitive(json.loads(d['extracted_json']))} for d in c.execute('select * from documents where application_id=? order by uploaded_at',(aid,))]; x['checks']=[{**dict(d),'evidence':mask_sensitive(json.loads(d['evidence_json']))} for d in c.execute('select * from checks where application_id=? order by created_at',(aid,))]; x['events']=[dict(d) for d in c.execute('select * from events where application_id=? order by created_at',(aid,))]; x['requests']=[dict(d) for d in c.execute('select * from requests where application_id=?',(aid,))]; x['reviews']=[dict(d) for d in c.execute('select * from review_cases where application_id=?',(aid,))]; return x
def make_report_pdf(app):
 from io import BytesIO
 from xml.sax.saxutils import escape
 from reportlab.lib import colors
 from reportlab.lib.pagesizes import letter
 from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
 from reportlab.lib.units import inch
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
 pdfsafe=lambda value:escape(str(value).replace('₹','INR '))
 out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=letter,rightMargin=.65*inch,leftMargin=.65*inch,topMargin=.65*inch,bottomMargin=.65*inch)
 styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='SmallMuted',parent=styles['BodyText'],fontSize=8,textColor=colors.HexColor('#64748b'),leading=11))
 story=[Paragraph('LoanDocVerify | Evidence report',styles['Title']),Paragraph('Synthetic demonstration data · For human review only',styles['SmallMuted']),Spacer(1,14)]
 info=[[Paragraph('<b>Applicant</b>',styles['BodyText']),escape(app['applicant_name']),Paragraph('<b>Application</b>',styles['BodyText']),escape(app['id'])],[Paragraph('<b>Loan type</b>',styles['BodyText']),escape(app['loan_type']),Paragraph('<b>Status</b>',styles['BodyText']),escape(app['status'])],[Paragraph('<b>Requested amount</b>',styles['BodyText']),f"INR {app['requested_amount']:,.0f}",Paragraph('<b>Monthly income declared</b>',styles['BodyText']),f"INR {app['declared_income']:,.0f}"]]
 table=Table(info,colWidths=[1.1*inch,2.05*inch,1.3*inch,2.1*inch]); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f3f6fa')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#dce4ef')),('INNERGRID',(0,0),(-1,-1),.3,colors.HexColor('#dce4ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)])); story += [table,Spacer(1,16),Paragraph('Documents reviewed',styles['Heading2'])]
 for d in app['documents']: story.append(Paragraph(f"• {escape(d['file_name'])} · {escape(d['document_type'])} · {escape(d['quality_status'])}",styles['BodyText']))
 story += [Spacer(1,10),Paragraph('Verification checks and evidence',styles['Heading2'])]
 for check in app['checks']:
  ev=pdfsafe(json.dumps(check['evidence'],ensure_ascii=False)); group=[Paragraph(f"<b>{pdfsafe(check['check_type'])}</b> - {pdfsafe(check['result'])} ({check['confidence']:.0%} confidence)",styles['BodyText']),Paragraph(pdfsafe(check['explanation']),styles['BodyText']),Paragraph('Evidence: '+ev,styles['SmallMuted']),Spacer(1,8)]; story.append(KeepTogether(group))
 story += [Spacer(1,8),Paragraph('Agent actions',styles['Heading2'])]
 for event in app['events']: story.append(Paragraph(f"{pdfsafe(event['agent'])} - {pdfsafe(event['action'])}: {pdfsafe(event['detail'])}",styles['SmallMuted']))
 story += [Spacer(1,12),Paragraph('Limitations',styles['Heading2']),Paragraph('Automated findings assist document review. They are not determinations of fraud or loan eligibility. A human loan officer must review the evidence and make every lending decision. This demo uses synthetic data.',styles['BodyText'])]
 doc.build(story);return out.getvalue()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def send(self,body,status=200,ctype='application/json; charset=utf-8',headers=None):
  raw=body if isinstance(body,bytes) else (json.dumps(body,ensure_ascii=False).encode() if ctype.startswith('application/json') else str(body).encode())
  self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(raw))); self.send_header('X-Content-Type-Options','nosniff')
  for k,v in (headers or {}).items():self.send_header(k,v)
  self.end_headers(); self.wfile.write(raw)
 def body(self):
  n=min(int(self.headers.get('Content-Length',0)),25_000_000); return self.rfile.read(n)
 def jsonbody(self): return json.loads(self.body() or b'{}')
 def auth_user(self):
  raw=self.headers.get('Cookie','')
  token=next((p.strip().split('=',1)[1] for p in raw.split(';') if p.strip().startswith('ldv_session=')),None)
  if not token:return None
  with connect() as c:return c.execute('select u.id,u.email,u.name,u.role from sessions s join users u on u.id=s.user_id where s.token_hash=? and s.expires_at>?',(token_hash(token),now())).fetchone()
 def do_GET(self):
  path=unquote(urlparse(self.path).path)
  if path=='/healthz':
   try:
    with connect() as c:c.execute('select 1').fetchone()
    self.send({'status':'ok'})
   except sqlite3.Error:self.send({'status':'error'},503)
   return
  if path=='/api/auth/me':
   u=self.auth_user(); self.send(dict(u) if u else {'error':'Sign in required'},200 if u else 401);return
  if path.startswith('/api/') or path.startswith('/files/'):
   self.user=self.auth_user()
   if not self.user:self.send({'error':'Please sign in to continue.'},401);return
  if path=='/api/applications':
   self.send(visible_applications(self.user)); return
  if path=='/api/dashboard':
   rows=visible_applications(self.user); rev=visible_review_cases(self.user)
   self.send({'applications':rows,'review_cases':rev,'metrics':{'total':len(rows),'processing':sum(x['status']=='Processing' for x in rows),'verified':sum(x['status']=='Verified' for x in rows),'review':len(rev),'incomplete':sum(x['status']=='Incomplete' for x in rows)}}); return
  if path=='/api/admin/review-cases':
   if self.user['role']!='officer':self.send({'error':'Loan officer access is required.'},403);return
   with connect() as c:
    scope,params=application_scope(self.user)
    rows=[dict(x) for x in c.execute(f"select r.*,a.applicant_name,a.loan_type from review_cases r join applications a on r.application_id=a.id where {scope} order by r.created_at desc",params)]
   self.send(rows);return
  if path=='/api/admin/reports':
   if self.user['role']!='officer':self.send({'error':'Loan officer access is required.'},403);return
   self.send(visible_reports(self.user));return
  if path.startswith('/api/applications/'):
   tail=path[len('/api/applications/'):].split('/'); aid=tail[0]
   if len(tail)>2 and tail[1:]==['verification','report.pdf']:
    a=application(aid,self.user['id'])
    if not a:self.send({'error':'Not found'},404);return
    self.send(make_report_pdf(a),200,'application/pdf',{'Content-Disposition':f'inline; filename="LoanDocVerify-{aid}.pdf"'});return
   if len(tail)>1 and tail[1]=='documents':
    a=application(aid,self.user['id'])
    if not a:self.send({'error':'Not found'},404)
    else:self.send(a['documents'])
    return
   if len(tail)>1 and tail[1]=='requests':
    a=application(aid,self.user['id'])
    if not a:self.send({'error':'Not found'},404)
    else:self.send(a['requests'])
    return
   if len(tail)>1 and tail[1]=='verification' and len(tail)>2 and tail[2]=='status':
    a=application(aid,self.user['id'])
    if not a:self.send({'error':'Not found'},404)
    else:self.send({'application_id':aid,'status':a['status'],'checks_completed':len(a['checks'])})
    return
   if len(tail)>1 and tail[1]=='verification' and len(tail)>2 and tail[2]=='report':
    a=application(aid,self.user['id'])
    if not a:self.send({'error':'Not found'},404);return
    self.send({'application':a,'human_decision_required':True});return
   a=application(aid,self.user['id'])
   if not a:self.send({'error':'Not found'},404)
   else:self.send(a)
   return
  if path.startswith('/files/'):
   name=Path(path).name
   with connect() as c:allowed=c.execute('select 1 from documents d join applications a on a.id=d.application_id where (a.owner_user_id=? or exists(select 1 from application_access x where x.application_id=a.id and x.officer_user_id=?)) and d.storage_path like ?',(self.user['id'],self.user['id'],'%'+name)).fetchone()
   if not allowed:self.send('Not found',404,'text/plain');return
   p=UPLOADS/name
   if not p.exists():self.send('Not found',404,'text/plain');return
   self.send(p.read_bytes(),200,mimetypes.guess_type(name)[0] or 'application/octet-stream');return
  if path=='/' or path=='/index.html':self.send((ROOT/'frontend/index.html').read_bytes(),200,'text/html; charset=utf-8');return
  if path.startswith('/assets/'):
   p=(ROOT/'frontend'/path.removeprefix('/assets/')).resolve()
   if p.is_relative_to((ROOT/'frontend').resolve()) and p.exists():self.send(p.read_bytes(),200,mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
   else:self.send('Not found',404,'text/plain')
   return
  self.send({'error':'Not found'},404)
 def do_POST(self):
  path=unquote(urlparse(self.path).path)
  if path in ('/api/auth/signup','/api/auth/login'):
   data=self.jsonbody(); email=str(data.get('email','')).strip().lower(); password=str(data.get('password','')); name=str(data.get('name','')).strip(); role=str(data.get('role','applicant')).lower()
   if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):self.send({'error':'Enter a valid email address.'},400);return
   if not password:self.send({'error':'Enter your password.'},400);return
   if path.endswith('signup') and len(password)<10:self.send({'error':'Use a password with at least 10 characters.'},400);return
   if path.endswith('signup') and role not in {'applicant','officer'}:self.send({'error':'Choose Applicant or Loan officer for this account.'},400);return
   with connect() as c:
    user=c.execute('select * from users where email=?',(email,)).fetchone()
    if path.endswith('signup'):
     if not name:self.send({'error':'Enter your name.'},400);return
     if user:self.send({'error':'An account with this email already exists.'},409);return
     user_id=uid(); c.execute('insert into users(id,email,name,password_hash,role,created_at) values(?,?,?,?,?,?)',(user_id,email,name,pw_hash(password),role,now())); user={'id':user_id,'email':email,'name':name,'role':role}
    elif not user or not pw_valid(password,user['password_hash']):self.send({'error':'Email or password is incorrect.'},401);return
    token=secrets.token_urlsafe(32); remember=path.endswith('signup') or bool(data.get('remember')); max_age=2592000 if remember else 28800; c.execute('insert into sessions values(?,?,?)',(token_hash(token),user['id'],(datetime.now(timezone.utc)+timedelta(seconds=max_age)).isoformat(timespec='seconds')))
   secure='; Secure' if self.headers.get('X-Forwarded-Proto','').lower()=='https' else ''
   self.send({'user':{'id':user['id'],'email':user['email'],'name':user['name'],'role':user['role']}},200,headers={'Set-Cookie':f'ldv_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={max_age}{secure}'});return
  if path=='/api/auth/logout':
   u=self.auth_user()
   if u:
    token=next((p.strip().split('=',1)[1] for p in self.headers.get('Cookie','').split(';') if p.strip().startswith('ldv_session=')),None)
    with connect() as c:c.execute('delete from sessions where token_hash=?',(token_hash(token),))
   self.send({'signed_out':True},200,headers={'Set-Cookie':'ldv_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'});return
  if path.startswith('/api/'):
   self.user=self.auth_user()
   if not self.user:self.send({'error':'Please sign in to continue.'},401);return
   share_match=re.fullmatch(r'/api/applications/([^/]+)/share-invite',path)
   if share_match:
    if self.user['role']!='applicant':self.send({'error':'Only the applicant can invite a loan officer.'},403);return
    aid=share_match.group(1)
    if not owns_application(aid,self.user['id']):self.send({'error':'Application not found.'},404);return
    code=secrets.token_hex(8).upper(); created=datetime.now(timezone.utc); expires=(created+timedelta(hours=24)).isoformat(timespec='seconds'); stamp=created.isoformat(timespec='seconds')
    with connect() as c:
     c.execute('insert into application_invites(code_hash,application_id,applicant_user_id,expires_at,accepted_by,accepted_at,created_at) values(?,?,?,?,?,?,?)',(token_hash(code),aid,self.user['id'],expires,None,None,stamp))
    self.send({'code':code,'expires_at':expires},201);return
   if path=='/api/application-invites/accept':
    if self.user['role']!='officer':self.send({'error':'Sign in with a loan officer account to accept an invitation.'},403);return
    code=re.sub(r'[\s-]','',str(self.jsonbody().get('code',''))).upper()
    if not re.fullmatch(r'[A-F0-9]{16}',code):self.send({'error':'Enter the 16-character invitation code.'},400);return
    with connect() as c:
     invite=c.execute('select * from application_invites where code_hash=? and accepted_at is null and expires_at>?',(token_hash(code),now())).fetchone()
     if not invite:self.send({'error':'That invitation code is invalid, expired or already used.'},404);return
     c.execute('insert or ignore into application_access(application_id,officer_user_id,created_at) values(?,?,?)',(invite['application_id'],self.user['id'],now()))
     c.execute('update application_invites set accepted_by=?,accepted_at=? where code_hash=?',(self.user['id'],now(),invite['code_hash']))
     c.execute('update application_invites set expires_at=? where application_id=? and accepted_at is null',(now(),invite['application_id']))
     log(c,invite['application_id'],'Access control','Loan officer connected',f"{self.user['name']} accepted the applicant's invitation.")
    self.send({'application_id':invite['application_id'],'connected':True},200);return
  if path=='/api/applications':
   if self.user['role']!='applicant':self.send({'error':'Only applicant accounts can create loan applications.'},403);return
   data=self.jsonbody(); aid=uid()
   with connect() as c:
    c.execute('insert into applications(id,applicant_name,dob,phone,email,loan_type,requested_amount,declared_income,employer,employment_type,purpose,status,created_at,owner_user_id) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(aid,data.get('applicant_name','').strip(),data.get('dob'),data.get('phone'),data.get('email'),data.get('loan_type','Personal Loan'),number(data.get('requested_amount')),number(data.get('declared_income')),data.get('employer'),data.get('employment_type'),data.get('purpose'),'Submitted',now(),self.user['id'])); log(c,aid,'Application service','Application created','Applicant submitted a new application.')
   self.send(application(aid,self.user['id']),201);return
  m=re.fullmatch(r'/api/applications/([^/]+)/documents',path)
  if m:
   aid=m.group(1)
   if not application(aid,self.user['id']):self.send({'error':'Not found'},404);return
   msg=BytesParser(policy=default).parsebytes(b'Content-Type: '+self.headers.get('Content-Type','').encode()+b'\r\nMIME-Version: 1.0\r\n\r\n'+self.body()); saved=[]
   for part in msg.iter_parts():
    if part.get_content_disposition()!='form-data' or not part.get_filename():continue
    name=Path(part.get_filename()).name; raw=part.get_payload(decode=True) or b''
    if len(raw)>10_000_000:self.send({'error':'Each file must be under 10 MB'},413);return
    ext=Path(name).suffix.lower()
    if ext not in {'.pdf','.png','.jpg','.jpeg','.txt','.csv'}:continue
    digest=hashlib.sha256(raw).hexdigest(); typ=classify(name); f=extract(raw,name,typ); newname=uid()+ext; p=UPLOADS/newname; p.write_bytes(raw)
    quality='Readable' if f['text_available'] else 'OCR needed'
    with connect() as c:
     duplicate=c.execute('select 1 from documents where application_id=? and file_hash=?',(aid,digest)).fetchone()
     if duplicate: quality='Duplicate'
     c.execute('insert into documents values(?,?,?,?,?,?,?,?,?,?,?)',(uid(),aid,name,typ,storage_path(p),digest,len(raw),quality,'Processed' if f['text_available'] else 'Needs OCR',json.dumps(f),now())); c.execute("update applications set status='Submitted' where id=?",(aid,)); c.execute('delete from checks where application_id=?',(aid,)); log(c,aid,'Document agent','Document received',f'{name}: classified as {typ}; {quality.lower()}.')
    saved.append({'name':name,'type':typ,'quality':quality})
   self.send({'uploaded':saved,'application':application(aid,self.user['id'])},201);return
  m=re.fullmatch(r'/api/applications/([^/]+)/verification/start',path)
  if m:
   if self.user['role']!='officer':self.send({'error':'Only a loan officer can start verification.'},403);return
   if not application(m.group(1),self.user['id']):self.send({'error':'Not found'},404);return
   result=verify(m.group(1)); self.send(result or {'error':'Not found'},200 if result else 404);return
  m=re.fullmatch(r'/api/admin/review-cases/([^/]+)/resolve',path)
  if m:
   if self.user['role']!='officer':self.send({'error':'Loan officer access is required.'},403);return
   data=self.jsonbody()
   with connect() as c:
    row=c.execute('select r.* from review_cases r join applications a on a.id=r.application_id where r.id=? and (a.owner_user_id=? or exists(select 1 from application_access x where x.application_id=a.id and x.officer_user_id=?))',(m.group(1),self.user['id'],self.user['id'])).fetchone()
    if row:c.execute("update review_cases set status='Resolved',resolution_notes=? where id=?",(data.get('notes','Reviewed by officer'),m.group(1)));row=c.execute('select * from review_cases where id=?',(m.group(1),)).fetchone()
    if row:log(c,row['application_id'],'Reviewer','Review case resolved',data.get('notes','Reviewed by officer.'),'Resolved')
   self.send(dict(row) if row else {'error':'Not found'},200 if row else 404);return
  m=re.fullmatch(r'/api/applications/([^/]+)/requests/([^/]+)/respond',path)
  if m:
   if self.user['role']!='applicant' or not owns_application(m.group(1),self.user['id']):self.send({'error':'Only the applicant who owns this application can respond.'},403);return
   data=self.jsonbody()
   if not application(m.group(1),self.user['id']):self.send({'error':'Not found'},404);return
   with connect() as c:
    c.execute("update requests set status='Submitted' where application_id=? and id=?",(m.group(1),m.group(2))); row=c.execute('select * from requests where application_id=? and id=?',(m.group(1),m.group(2))).fetchone()
    if row:log(c,m.group(1),'Applicant','Request response submitted',data.get('message','Applicant submitted a response and supporting information.'),'Submitted')
   self.send(dict(row) if row else {'error':'Not found'},200 if row else 404);return
  m=re.fullmatch(r'/api/applications/([^/]+)/requests',path)
  if m:
   if self.user['role']!='officer':self.send({'error':'Only a loan officer can request clarification.'},403);return
   data=self.jsonbody(); rid=uid()
   with connect() as c:
    if not application(m.group(1),self.user['id']):self.send({'error':'Not found'},404);return
    c.execute('insert into requests values(?,?,?,?,?,?)',(rid,m.group(1),data.get('document_type','Additional document'),data.get('reason','Please provide the requested evidence.'),'Open',now())); c.execute("update applications set status='Needs clarification' where id=?",(m.group(1),)); log(c,m.group(1),'Reviewer','Applicant request created',data.get('reason','Additional evidence requested.'))
   self.send({'id':rid,'application_id':m.group(1),'status':'Open'},201);return
  m=re.fullmatch(r'/api/applications/([^/]+)/review/(note|assign)',path)
  if m:
   if self.user['role']!='officer':self.send({'error':'Only a loan officer can record reviewer actions.'},403);return
   data=self.jsonbody(); action='Reviewer note added' if m.group(2)=='note' else 'Reviewer assigned'; detail=data.get('note','').strip() if m.group(2)=='note' else f"Assigned to {data.get('reviewer','Loan Officer')}"
   if not detail:self.send({'error':'A note is required.' if m.group(2)=='note' else 'A reviewer is required.'},400);return
   with connect() as c:
    if not application(m.group(1),self.user['id']):self.send({'error':'Not found'},404);return
    log(c,m.group(1),'Reviewer',action,detail)
   self.send({'saved':True,'action':action,'detail':detail},201);return
  m=re.fullmatch(r'/api/applications/([^/]+)/review/finding',path)
  if m:
   if self.user['role']!='officer':self.send({'error':'Only a loan officer can assess findings.'},403);return
   data=self.jsonbody(); finding_id=data.get('finding_id','').strip(); decision=data.get('decision','').strip(); note=data.get('note','').strip()
   allowed={'Reviewed','Confirmed issue','Needs applicant clarification','Not applicable'}
   if not finding_id or decision not in allowed or (decision in {'Confirmed issue','Not applicable'} and not note):self.send({'error':'Choose a valid assessment and add a note when required.'},400);return
   with connect() as c:
    row=c.execute('select k.check_type from checks k join applications a on a.id=k.application_id where k.id=? and k.application_id=? and (a.owner_user_id=? or exists(select 1 from application_access x where x.application_id=a.id and x.officer_user_id=?))',(finding_id,m.group(1),self.user['id'],self.user['id'])).fetchone()
    if not row:self.send({'error':'Finding not found for this application.'},404);return
    log(c,m.group(1),'Reviewer',f"Finding marked: {decision}",f"{row['check_type']} · {note or 'Reviewed by officer.'} · finding_id={finding_id}")
   self.send({'saved':True,'finding_id':finding_id,'decision':decision},201);return
  self.send({'error':'Not found'},404)
 def do_PUT(self):
  self.user=self.auth_user()
  if not self.user:self.send({'error':'Please sign in to continue.'},401);return
  m=re.fullmatch(r'/api/documents/([^/]+)',unquote(urlparse(self.path).path))
  if m:
   data=self.jsonbody(); typ=data.get('document_type','Other')
   if typ not in {'PAN','Aadhaar','Salary Slip','Bank Statement','Employment Proof'}:self.send({'error':'Choose a document type from the personal-loan checklist.'},400);return
   with connect() as c:
    row=c.execute('select d.* from documents d join applications a on a.id=d.application_id where d.id=? and (a.owner_user_id=? or exists(select 1 from application_access x where x.application_id=a.id and x.officer_user_id=?))',(m.group(1),self.user['id'],self.user['id'])).fetchone()
    if row:
     raw=stored_file(row['storage_path']).read_bytes(); extracted=extract(raw,row['file_name'],typ); c.execute('update documents set document_type=?,extracted_json=? where id=?',(typ,json.dumps(extracted),m.group(1))); c.execute('delete from checks where application_id=?',(row['application_id'],)); c.execute("update applications set status='Submitted' where id=?",(row['application_id'],)); log(c,row['application_id'],'Document agent','Document type corrected',f"{row['file_name']} was updated to {typ}; previous checks were marked stale.")
   self.send({'document_id':m.group(1),'document_type':typ},200 if row else 404);return
  m=re.fullmatch(r'/api/applications/([^/]+)',unquote(urlparse(self.path).path))
  if not m:self.send({'error':'Not found'},404);return
  if self.user['role']!='applicant' or not owns_application(m.group(1),self.user['id']):self.send({'error':'Only the applicant who owns this application can edit it.'},403);return
  d=self.jsonbody(); fields=['applicant_name','dob','phone','email','loan_type','requested_amount','declared_income','employer','employment_type','purpose']
  if not application(m.group(1),self.user['id']):self.send({'error':'Not found'},404);return
  with connect() as c:
   sets=','.join(k+'=?' for k in fields); c.execute('update applications set '+sets+",status='Submitted' where id=? and owner_user_id=?",[number(d.get(k)) if k in ('requested_amount','declared_income') else d.get(k) for k in fields]+[m.group(1),self.user['id']]); c.execute('delete from checks where application_id=?',(m.group(1),)); log(c,m.group(1),'Applicant','Application details updated','Existing verification checks are stale and should be rerun.')
  self.send(application(m.group(1),self.user['id']) or {'error':'Not found'})
 def do_DELETE(self):
  self.user=self.auth_user()
  if not self.user:self.send({'error':'Please sign in to continue.'},401);return
  m=re.fullmatch(r'/api/documents/([^/]+)',unquote(urlparse(self.path).path))
  if m:
   with connect() as c:
    row=c.execute('select d.storage_path,d.application_id from documents d join applications a on a.id=d.application_id where d.id=? and (a.owner_user_id=? or exists(select 1 from application_access x where x.application_id=a.id and x.officer_user_id=?))',(m.group(1),self.user['id'],self.user['id'])).fetchone()
    if row:
     c.execute('delete from documents where id=?',(m.group(1),)); c.execute('delete from checks where application_id=?',(row['application_id'],)); c.execute("update applications set status='Submitted' where id=?",(row['application_id'],)); log(c,row['application_id'],'Document agent','Document removed','Previous verification checks are stale and need to be rerun.')
   if row:
    p=stored_file(row['storage_path']).resolve()
    if p.is_relative_to(UPLOADS.resolve()) and p.exists():p.unlink()
   self.send({'deleted':bool(row)},200 if row else 404);return
  m=re.fullmatch(r'/api/applications/([^/]+)',unquote(urlparse(self.path).path))
  if m:
   if self.user['role']!='applicant' or not owns_application(m.group(1),self.user['id']):self.send({'error':'Only the applicant who owns this application can delete it.'},403);return
   with connect() as c: paths=[x['storage_path'] for x in c.execute('select d.storage_path from documents d join applications a on a.id=d.application_id where d.application_id=? and a.owner_user_id=?',(m.group(1),self.user['id']))]; c.execute('delete from applications where id=? and owner_user_id=?',(m.group(1),self.user['id'])); deleted=c.total_changes>0
   for path in paths:
    p=stored_file(path).resolve()
    if p.is_relative_to(UPLOADS.resolve()) and p.exists():p.unlink()
   self.send({'deleted':deleted},200 if deleted else 404);return
  self.send({'error':'Not found'},404)

if __name__=='__main__':
 init_db()
 server=ThreadingHTTPServer((HOST,PORT),Handler)
 url=f'http://127.0.0.1:{PORT}'
 print(f'LoanDocVerify listening on {HOST}:{PORT}.',flush=True)
 if HOST in ('127.0.0.1','localhost') and os.environ.get('LDV_NO_BROWSER')!='1':
  print(f'Keep this window open; press Ctrl+C to stop. Opening {url}',flush=True)
  webbrowser.open(url,new=2)
 try: server.serve_forever()
 except KeyboardInterrupt: print('\nLoanDocVerify stopped.',flush=True)
 finally: server.server_close()
