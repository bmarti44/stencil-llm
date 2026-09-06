"""Exercise the actual streaming consumer with synthetic EOS/cap replies, no model."""
import http.server, importlib.util, json, tempfile, threading, time
from pathlib import Path

def main():
    spec=importlib.util.spec_from_file_location('replay',Path(__file__).with_name('replay.py'))
    replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
    outputs=[[42,151645],[43]*512]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert request['prompt']==[1,2,3] and request['logprobs'] is None
            assert request['max_tokens']==512 and request['stop_token_ids']==[151645,151643]
            ids=outputs.pop(0)
            self.send_response(200);self.end_headers()
            for i,tok in enumerate(ids):
                last=i==len(ids)-1
                choice=dict(index=0,token_ids=[tok],prompt_token_ids=[1,2,3] if i==0 else None,finish_reason=('stop' if tok==151645 else 'length') if last else None,stop_reason=tok if last and tok==151645 else None)
                self.wfile.write(('data: '+json.dumps({'choices':[choice]})+'\n\n').encode())
            self.wfile.write(('data: '+json.dumps({'choices':[],'usage':{'completion_tokens':len(ids),'prompt_tokens':3}})+'\n\ndata: [DONE]\n\n').encode())
    server=http.server.HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever);thread.start()
    try:
        with tempfile.TemporaryDirectory() as directory:
            replay.OUT=Path(directory);replay.URL='http://127.0.0.1:'+str(server.server_port)
            for i in range(2):
                row=replay.call('smoke',i,dict(prompt=[1,2,3],arm='R',round=i),time.time()+300)
                assert row['complete'] and row['decode_tokens']==len(row['output_token_ids'])-1
            saved=[json.loads(x) for x in (replay.OUT/'records.jsonl').read_text().splitlines()]
            assert len(saved)==2 and saved[0]['output_token_ids']==[42,151645] and len(saved[1]['output_token_ids'])==512
    finally:server.shutdown();thread.join();server.server_close()
    print('PASS: real consumer preserves raw IDs, separate terminal EOS, cap512, usage, timings, per-call writer')
if __name__=='__main__':main()
