"""Save actual ARM assembly; counts are scans, not performance claims."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def selected_sections(text):
    sections=[];current=[];name=None
    for line in text.splitlines():
        header=re.match(r'^[0-9a-f]+ <(.+)>:$',line)
        if header:
            if name is not None:sections.append((name,'\n'.join(current)+'\n'))
            name=header[1];current=[line]
        elif name is not None:current.append(line)
    if name is not None:sections.append((name,'\n'.join(current)+'\n'))
    return[(name,body)for name,body in sections if any(part in name for part in
        ('NativeMG::Impl::clover_range(','NativeMG::Impl::local_range(','clover_range_sve_reused('))]

def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--old-library',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(exist_ok=False)
    records={}
    for label,path in(('new',args.library),('old',args.old_library)):
        result=subprocess.run(['objdump','-d','--demangle','--no-show-raw-insn',str(path)],capture_output=True,text=True,check=True,timeout=60)
        sections=selected_sections(result.stdout);assert any('NativeMG::Impl::clover_range('in name for name,_ in sections)
        if label=='new':assert any('clover_range_sve_reused('in name for name,_ in sections),'Opt-in kernel absent in compiled ARM library'
        text='\n'.join(body for _,body in sections);target=args.output/(label+'-clover-assembly.txt');target.write_text(text)
        records[label]=dict(library=str(path),library_sha256=sha(path),assembly_sha256=sha(target),sections=[dict(symbol=name,
            instructions=len(re.findall(r'^\s*[0-9a-f]+:',body,re.M)),
            direct_sve_stack_lines=[line.strip()for line in body.splitlines()if re.search(r'\b(?:str|st1w|st1d|ldr|ld1w|ld1d)\s+.*\bz\d+',line)and'[sp'in line],
            frame_setup=[line.strip()for line in body.splitlines()if re.search(r'\b(?:sub|addvl)\s+sp,\s*sp,',line)],
            multiply_add_instructions=len(re.findall(r'\bf(?:mla|mls|madd|msub)\b',body)),
            load_instructions=len(re.findall(r'\bld1w\b',body)))for name,body in sections])
    report=dict(complete=True,actual_assembly=True,performance_ranked=False,records=records,
        interpretation='Static direct-SP SVE load/store scan only; indirect stack addresses, dynamic frequency and whole-solve regression need review/measurement')
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
