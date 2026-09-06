"""Apply the prior registered trait transform on CPU only after pilot4."""
import importlib.util
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent


def main():
    summary=json.loads((OUT/'summary.json').read_text())
    compliance=summary['per_arm']['R']['round0_indent']
    if compliance['required']!=8 or compliance['compliant']>=4:
        (OUT/'trait-swap-disposition.json').write_text(json.dumps(dict(applied=False,reason='trigger not established' if compliance['required']!=8 else 'indentation gate passed'))+'\n')
        return
    source=OUT.parent/'composition-pilot-3/trait-swap/screen.py'
    spec=importlib.util.spec_from_file_location('registered_trait_swap',source)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    dest=OUT/'trait-swap';dest.mkdir(exist_ok=True)
    mod.OUT=dest;mod.PARENT=OUT
    (dest/'activation.json').write_text(json.dumps(dict(original_indent_gate_failed=True,compliant=compliance['compliant'],required=8,source_records_sha256={str(p.relative_to(OUT)):mod.p.sha(p) for p in (OUT/'records.jsonl',OUT/'continuation/records.jsonl') if p.exists()},authority='Pilot4 user brief; pilot3 conditional-registration fixed mapping'))+'\n')
    mod.cpu()
    (dest/'README.md').write_text('''# Registered trait swap — CPU APPLIED; GPU UNRUN\n\nPilot4 required R round-zero indentation is below4/8. Original outcomes stand.\nApplied the prior fixed mapping2->ALPHA,3->BETA,4->GAMMA docstring-prefix trait\nwithout candidate search; all8 transformed DEV episodes and system text frozen\nin frozen.json.32 positive/wrong/missing/capped witnesses pass through the actual\nloop/executor/checker. CPU validation is not measured model competence.\nPer user brief the swap is applied afterwards on CPU; no swapped GPU inference\nor hidden-state capture. Pilot3's failed lexical GPU screen remains historical.\n''')
    (OUT/'trait-swap-disposition.json').write_text(json.dumps(dict(applied=True,cpu_witnesses=32,gpu='UNRUN',original_results_stand=True))+'\n')


if __name__=='__main__':main()
