"""Loopback-only roadshow. Recorded verdicts + live LOCAL retrieval; no cloud endpoint."""
import argparse,json,threading,webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from bioguard import core as guard
ROOT=Path(__file__).resolve().parent
WEB=ROOT/'demo'

def make_handler(retriever,policy,port):
    lock=threading.Lock();cards={c['id']:c for c in policy['cards']};sources={s['id']:s for s in policy['sources']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass # Do not write user inputs to access logs.
        def respond(self,status,payload,kind='application/json; charset=utf-8'):
            body=json.dumps(payload,ensure_ascii=False).encode() if isinstance(payload,dict) else payload
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers();self.wfile.write(body)
        def host_ok(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def do_GET(self):
            if not self.host_ok():self.respond(403,dict(error='只接受本机地址'));return
            if self.path=='/api/health':self.respond(200,dict(mode='offline_retrieval_and_recorded_verdicts',cloud_enabled=False));return
            files={'/':('index.html','text/html; charset=utf-8'),'/data.js':('data.js','application/javascript; charset=utf-8'),'/report.html':('report.html','text/html; charset=utf-8')}
            # Only the public evidence linked from the report is served from the project.
            report_files = {
                '/results/summary.csv': 'text/csv',
                '/results/evidence/paired_comparisons.json': 'application/json',
                '/results/evidence/retrieval.json': 'application/json',
                '/results/evidence/citations.json': 'application/json',
                '/results/evidence/model_only_errors.json': 'application/json',
                '/results/records.md': 'text/plain',
                '/data/requests.jsonl': 'text/plain',
                '/data/review_template.json': 'application/json',
                '/policy/knowledge.json': 'application/json',
            }
            if self.path in report_files:
                payload = (ROOT / self.path.lstrip('/')).read_bytes()
                self.respond(200, payload, report_files[self.path] + '; charset=utf-8')
                return
            if self.path not in files:self.respond(404,dict(error='Not found'));return
            name,kind=files[self.path];self.respond(200,(WEB/name).read_bytes(),kind)
        def do_POST(self):
            if not self.host_ok():self.respond(403,dict(error='只接受本机地址'));return
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
                self.respond(403,dict(error='拒绝跨站请求'));return
            if self.path!='/api/retrieve':self.respond(404,dict(error='Not found'));return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=12000:raise ValueError('请求过长或为空')
                data=json.loads(self.rfile.read(size));text=data.get('text');method=data.get('method','fusion')
                if not isinstance(text,str) or not text.strip() or len(text)>3000:raise ValueError('请输入 1 至 3000 字符')
                if method not in ('boundary','fusion'):raise ValueError('未知检索方法')
                with lock:
                    n=len(retriever.tokenizer('为这个句子生成表示以用于检索相关文章：'+text)['input_ids'])
                    if n>512:raise ValueError('当前模型最多处理 512 个词元；请缩短输入，系统不会静默截断')
                    ranked=retriever.rank(text,method)
                self.respond(200,dict(mode='local_retrieval_only',decision=None,tokens=n,
                    cards=[dict(**r,card=cards[r['id']],source=sources[cards[r['id']]['source']]) for r in ranked]))
            except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:self.respond(400,dict(error=str(e)))
            except Exception:self.respond(500,dict(error='本地检索暂时不可用；可继续查看真实评测记录'))
    return Handler

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    if not (WEB/'data.js').exists():raise SystemExit('演示数据缺失，请重新解压完整项目')
    print('正在载入本地检索模型；演示不调用付费 API。',flush=True)
    from bioguard.retrieval import EvidenceRetriever
    policy=guard.read_json(ROOT/'policy/knowledge.json');retriever=EvidenceRetriever(policy['cards'])
    with ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(retriever,policy,args.port)) as server:
        print(f'演示已就绪：http://127.0.0.1:{args.port} ；关闭此窗口可结束。',flush=True)
        if not args.no_browser:webbrowser.open(f'http://127.0.0.1:{args.port}')
        try:server.serve_forever()
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
