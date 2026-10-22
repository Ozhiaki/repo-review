"""Expose completed mechanical work and targeted source reads to the reviewer."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import uuid

from prepass_runtime import ledger, records as r, scope, tokens
from .instructions import FILES, LIMITS


def schema(fields, required):
    return dict(type="object",properties=fields,required=required,additionalProperties=False)


TEXT = dict(type="string")
SIDE = dict(type="string",enum=["focal","twin"],default="focal")
INT = dict(type="integer",minimum=0)
TOOLS = [
 dict(name="lookup",description="Query the completed mechanical index. Locate paths, declarations, call spellings, module imports, and text anchors. This replaces directory listing and structural grep. Results are leads, not proof of behavior.",
      inputSchema=schema(dict(repo=SIDE,kind=dict(type="string",enum=["path","symbol","call","module","import","text","lead"]),query=TEXT,offset=INT),["kind","query"])),
 dict(name="read_source",description="Read exact captured source to answer a behavioral question. Do not repeat mechanical counts or maps from the packet. Large files need an explicit LF range of at most 16384 bytes.",
      inputSchema=schema(dict(repo=SIDE,path=TEXT,question=TEXT,start=dict(type="integer",minimum=1),end=dict(type="integer",minimum=1)),["path","question"])),
 dict(name="coverage",description="Check host-confirmed source delivery for a selected file. Packet facts and lookup hits are not whole-file readings.",inputSchema=schema(dict(repo=SIDE,path=TEXT),["path"]))]
for tool in TOOLS:
    tool["annotations"] = dict(readOnlyHint=True,destructiveHint=False,openWorldHint=False)


def tool_hash():
    return r.hashed_json(TOOLS)


def verified_reads(run_home):
    """Only host-captured complete tool_result bytes count as source delivery."""
    result = []
    for path in sorted(Path(run_home).glob("passes/*/attempt-*/delivered/*.json")):
        home = path.parent.parent
        captured = r.read(path)
        produced = r.read(home/"produced"/path.name)
        capture = Path(captured["capture"])
        r.require(capture.is_relative_to(home/"captures") and capture.is_file() and not capture.is_symlink(), "A source capture is outside its attempt.")
        data = capture.read_bytes()
        r.require(len(data)==produced["produced_bytes"] and ledger.sha(data)==produced["produced_sha256"], "Confirmed source bytes differ.")
        result.append(produced)
    return result


def confirm(home):
    home = Path(home)
    produced = [r.read(path) for path in (home/"produced").glob("*.json")]
    observed = {row["id"] for row in verified_reads(home.parents[2]) if row["id"] in {p["id"] for p in produced}}
    r.require(observed=={row["id"] for row in produced}, "Some source responses have no verified host capture.")
    return len(observed)


def bounded(items, offset=0):
    r.require(type(offset) is int and offset>=0, "Use a nonnegative offset.")
    kept=[]
    for row in items[offset:offset+12]:
        if tokens.tokens(json.dumps([*kept,row],ensure_ascii=True))>1600:
            break
        kept.append(row)
    r.require(kept or offset>=len(items), "A lookup row exceeds the response budget.")
    end=offset+len(kept)
    return dict(items=kept,total_matches=len(items),offset=offset,next_offset=end if end<len(items) else None,
                reading_credit="none; use read_source for behavioral evidence")


class Service:
    def __init__(self,config):
        self.config=config
        r.require(config["pass"] in FILES, "Unknown prepared review pass.")
        r.require(config["prepared_tool_sha256"]==tool_hash(), "The prepared review tool definitions changed.")
        self.home=Path(config["home"])
        self.packet=Path(config["packet"])
        from .cli import check, SEAL
        check(self.packet)
        r.require(r.digest(self.packet/SEAL)==config["packet_manifest_sha256"],"The connected packet version changed.")
        recorded = sum(1 for path in Path(config["run_home"]).glob("passes/" + config["pass"] + "/attempt-*/tool-calls.jsonl")
                       for line in path.read_text().splitlines() if line.strip())
        self.calls=max(config.get("prior_tool_calls",0), recorded)
        self.tables={}

    def selected(self,repo):
        r.require(repo in ("focal","twin"),"Unknown repository.")
        r.require(repo!="twin" or self.config["pass"]=="04","The comparison source is available only during pass 04.")
        folder=self.packet/"data"/repo
        r.require(folder.is_dir(),"This packet has no selected comparison repository.")
        if repo not in self.tables:
            self.tables[repo]=r.read(folder/"tables.json")
        return folder,self.tables[repo]

    def invoke(self,name,args):
        self.calls+=1
        r.require(self.calls<=LIMITS["calls_per_pass"],"The pass call limit is reached. Finish the report and state its limits.")
        tool=next((row for row in TOOLS if row["name"]==name),None)
        r.require(tool is not None,"Unknown prepared review tool.")
        shape=tool["inputSchema"]
        r.require(isinstance(args,dict) and args.keys()<=shape["properties"].keys() and set(shape["required"])<=args.keys(),"Unknown or missing tool argument.")
        for key,value in args.items():
            definition=shape["properties"][key]
            r.require((definition["type"]=="string" and isinstance(value,str)) or
                      (definition["type"]=="integer" and type(value)is int and value>=definition["minimum"]),"Invalid tool argument type.")
            if "enum" in definition:
                r.require(value in definition["enum"],"Invalid tool argument value.")
        repo=args.get("repo","focal")
        folder,tables=self.selected(repo)
        files={row["path"]:row for row in tables["files"]}
        if name=="lookup":
            query=args["query"].strip()
            r.require(1<=len(query)<=160 and "\x00" not in query,"Supply a short nonempty literal lookup query.")
            folded=query.casefold()
            kind=args["kind"]
            collections=dict(path=tables["files"],symbol=tables["symbols"],call=tables["call_sites"],module=tables["modules"],lead=tables["leads"],import_=tables["imports"])
            if kind=="import":kind="import_"
            if kind=="text":
                matches=[]
                for row in tables["files"]:
                    if row["binary"] or row["lfs"]: continue
                    data,_=scope.read_regular(folder/"source",row["path"])
                    r.require(ledger.sha(data)==row["sha256"],"Captured source changed.")
                    try:
                        text=data.decode("utf-8")
                    except UnicodeError:
                        continue
                    for index,line in enumerate(text.split("\n"),1):
                        if folded in line.casefold(): matches.append(dict(path=row["path"],line=index,excerpt=line[:180]))
            else:
                matches=[row for row in collections[kind] if folded in json.dumps(row,ensure_ascii=False).casefold()]
                if kind=="lead":
                    matches=[dict(row,text=row.get("text","")[:240],excerpt_only=len(row.get("text",""))>240) for row in matches]
                if kind=="module":
                    matches=[{key:row[key] for key in ("path","lines","line_coverage","production_files","test_files","local_dependencies","local_dependents","literal_imports","module_root_known","dependency_scope","parse_errors")} for row in matches]
                    for row in matches:
                        for key in ("local_dependencies","local_dependents","literal_imports","parse_errors"):
                            row[key+"_count"]=len(row[key])
                            row[key]=row[key][:10]
            return bounded(matches,args.get("offset",0))
        path=str(scope.checked_name(args["path"]))
        r.require(path in files,"The path is outside selected source.")
        row=files[path]
        if name=="coverage":
            reads=[record for record in verified_reads(self.config["run_home"]) if record["path"]==path and record["repo"]==repo and record["sha256"]==row["sha256"]]
            intervals=sorted((record["start_line"],record["end_line"]) for record in reads)
            end=0
            for start,last in intervals:
                if start>end+1:break
                end=max(end,last)
            return dict(path=path,verified_ranges=intervals,whole_file_delivered=bool(reads) and end>=(row["lines"] or 0),
                        note="Delivery does not prove attention or understanding.")
        r.require(8<=len(args["question"].strip())<=600,"State the behavioral question for this source read.")
        r.require(not row["binary"] and not row["lfs"],"The selected file has no readable source text.")
        data,_=scope.read_regular(folder/"source",path)
        r.require(ledger.sha(data)==row["sha256"],"Captured source bytes changed.")
        lines=ledger.lines(data)
        r.require(("start" in args)==("end" in args),"Supply both LF range bounds.")
        start,end=args.get("start",1),args.get("end",len(lines))
        if "start" in args:r.require(1<=start<=end<=len(lines),"The LF range is invalid.")
        selected=b"".join(lines[start-1:end])
        r.require(len(selected)<=LIMITS["source_response_bytes"],"The range exceeds 16384 bytes. Use declaration line bounds from lookup.")
        text=selected.decode("utf-8")
        identifier=uuid.uuid4().hex
        r.save(self.home/"produced"/(identifier+".json"),dict(id=identifier,path=path,repo=repo,sha256=row["sha256"],
            start_line=start,end_line=end,question=args["question"],produced_bytes=len(selected),produced_sha256=ledger.sha(selected),truncated=False))
        return dict(delivery_id=identifier,path=path,source=text,truncated=False,start_line=start,end_line=end)


def serve(path):
    service=Service(r.read(path))
    for line in sys.stdin.buffer:
        r.require(len(line)<=1024*1024,"The MCP request is too large.")
        request=json.loads(line)
        if request.get("id") is None:continue
        try:
            method=request["method"]
            if method=="initialize":
                result=dict(protocolVersion=request["params"]["protocolVersion"],capabilities=dict(tools={}),serverInfo=dict(name="review",version="prepared-1"))
            elif method=="ping":result={}
            elif method=="tools/list":result=dict(tools=TOOLS)
            elif method=="tools/call":
                try:
                    value=service.invoke(request["params"]["name"],request["params"].get("arguments",{}))
                    value["discovery_budget"]=dict(limit=LIMITS["calls_per_pass"],used=service.calls,remaining=max(0,LIMITS["calls_per_pass"]-service.calls))
                    result=dict(content=[dict(type="text",text=json.dumps(value,ensure_ascii=True))],isError=False)
                except (r.PrepassError,OSError,ValueError,KeyError,UnicodeError) as exc:
                    result=dict(content=[dict(type="text",text=str(exc))],isError=True)
                r.output_directory(service.home)
                with (service.home/"tool-calls.jsonl").open("a") as stream:stream.write(json.dumps(dict(request=request,response=result))+"\n")
            else:raise r.PrepassError("Unknown MCP method.")
            response=dict(jsonrpc="2.0",id=request["id"],result=result)
        except Exception as exc:response=dict(jsonrpc="2.0",id=request["id"],error=dict(code=-32603,message=str(exc)))
        print(json.dumps(response,ensure_ascii=True),flush=True)
