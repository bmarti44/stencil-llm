"""Read-only5s server gauge sampling; no model requests."""
import json,time,urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent
def main():
    with (OUT/'scheduler-samples.jsonl').open('a') as f:
        while (OUT/'RUNNING.flag').exists():
            try:
                with urllib.request.urlopen('http://127.0.0.1:18081/metrics',timeout=3) as response:
                    rows=[s for s in response.read().decode().splitlines() if s.startswith(('vllm:num_requests_running{','vllm:num_requests_waiting{','vllm:kv_cache_usage_perc{'))]
                f.write(json.dumps(dict(time=time.time(),gauges=rows))+'\n');f.flush()
            except Exception:pass
            time.sleep(5)
if __name__=='__main__':main()
