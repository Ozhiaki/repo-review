// Parse selected Go source. Never load, build, import, or execute subject code.
package main

import (
 "encoding/json"
 "fmt"
 "go/ast"
 "go/parser"
 "go/token"
 "os"
 "path/filepath"
 "sort"
 "strconv"
 "strings"
)

type Config struct { Root string `json:"root"`; Files []string `json:"files"`; Modules map[string]string `json:"modules"` }
type Decl struct { Name string `json:"name"`; Kind string `json:"kind"`; Line int `json:"line"`; End int `json:"end_line"`; Receiver string `json:"receiver,omitempty"` }
type Call struct { Name string `json:"name"`; Line int `json:"line"`; Resolution string `json:"resolution"` }
type File struct { Path string `json:"path"`; Package string `json:"package"`; Test bool `json:"test"`; Imports []string `json:"imports"`; Declarations []Decl `json:"declarations"`; Calls []Call `json:"calls"`; Error string `json:"error,omitempty"` }
type Edge struct { From string `json:"from"`; To string `json:"to"`; Import string `json:"import"`; Resolution string `json:"resolution"`; Test bool `json:"test"` }

func clean(root, name string) (string,error) {
 if filepath.IsAbs(name) { return "", fmt.Errorf("absolute source path") }
 name=filepath.Clean(filepath.FromSlash(name))
 if name==".." || strings.HasPrefix(name,".."+string(filepath.Separator)) { return "",fmt.Errorf("source path escapes root") }
 path:=filepath.Join(root,name)
 rel,err:=filepath.Rel(root,path)
 if err!=nil || rel==".." || strings.HasPrefix(rel,".."+string(filepath.Separator)) { return "",fmt.Errorf("source path escapes root") }
 for here:=path; here!=root; here=filepath.Dir(here) {
  info,err:=os.Lstat(here); if err!=nil { return "",err }; if info.Mode()&os.ModeSymlink!=0 { return "",fmt.Errorf("linked source path") }
 }
 return path,nil
}
func receiver(e ast.Expr) string {
 switch n:=e.(type) { case *ast.Ident:return n.Name; case *ast.StarExpr:return "*"+receiver(n.X); case *ast.IndexExpr:return receiver(n.X); case *ast.IndexListExpr:return receiver(n.X) }; return "?"
}
func owner(dir string, modules map[string]string) (string,string,bool) {
 best:=""; mod:=""; found:=false
 for root,m:=range modules { if root=="." || dir==root || strings.HasPrefix(dir,root+"/") { if !found || len(root)>len(best) { best=root;mod=m;found=true } } }
 return best,mod,found
}
func main() {
 var cfg Config
 if len(os.Args)!=2 {panic("supply one request file")}
 request,err:=os.Open(os.Args[1]);if err!=nil {panic(err)};defer request.Close()
 if err:=json.NewDecoder(request).Decode(&cfg);err!=nil { panic(err) }
 root,err:=filepath.Abs(cfg.Root);if err!=nil {panic(err)}
 resolved,err:=filepath.EvalSymlinks(root);if err!=nil || resolved!=root {panic("linked source root")}
 sort.Strings(cfg.Files)
 files:=[]File{}; dirs:=map[string]string{}
 for _,name:=range cfg.Files {
  path,err:=clean(root,name); if err!=nil {panic(err)}
  row:=File{Path:name,Test:strings.HasSuffix(name,"_test.go"),Imports:[]string{},Declarations:[]Decl{},Calls:[]Call{}}
  set:=token.NewFileSet()
  tree,err:=parser.ParseFile(set,path,nil,parser.ParseComments|parser.SkipObjectResolution)
  if err!=nil {row.Error=err.Error();files=append(files,row);continue}
  row.Package=tree.Name.Name
  for _,im:=range tree.Imports { value,err:=strconv.Unquote(im.Path.Value);if err!=nil {panic(err)};row.Imports=append(row.Imports,value) }
  for _,decl:=range tree.Decls {
   switch d:=decl.(type) {
   case *ast.FuncDecl:
    item:=Decl{Name:d.Name.Name,Kind:"function",Line:set.PositionFor(d.Pos(),false).Line,End:set.PositionFor(d.End(),false).Line}
    if d.Recv!=nil && len(d.Recv.List)>0 {item.Kind="method";item.Receiver=receiver(d.Recv.List[0].Type)}
    row.Declarations=append(row.Declarations,item)
   case *ast.GenDecl:
    for _,spec:=range d.Specs { switch sp:=spec.(type) {
    case *ast.TypeSpec:row.Declarations=append(row.Declarations,Decl{Name:sp.Name.Name,Kind:"type",Line:set.PositionFor(sp.Pos(),false).Line,End:set.PositionFor(sp.End(),false).Line})
    case *ast.ValueSpec:for _,n:=range sp.Names {row.Declarations=append(row.Declarations,Decl{Name:n.Name,Kind:d.Tok.String(),Line:set.PositionFor(sp.Pos(),false).Line,End:set.PositionFor(sp.End(),false).Line})}
    } }
   }
  }
  ast.Inspect(tree,func(node ast.Node) bool {
   call,ok:=node.(*ast.CallExpr);if !ok{return true}; name:=""
   switch fun:=call.Fun.(type) {case *ast.Ident:name=fun.Name;case *ast.SelectorExpr:name=receiver(fun.X)+"."+fun.Sel.Name}
   if name!="" {row.Calls=append(row.Calls,Call{Name:name,Line:set.PositionFor(call.Pos(),false).Line,Resolution:"syntax_only_not_a_call_graph"})};return true
  })
  sort.Strings(row.Imports)
  dir:=filepath.ToSlash(filepath.Dir(name))
  if !row.Test {base,mod,ok:=owner(dir,cfg.Modules);if ok {suffix:=dir;if dir==base {suffix=""} else if base!="." {suffix=strings.TrimPrefix(dir,base+"/")};key:=mod;if suffix!="" && suffix!="." {key+="/"+suffix};dirs[key]=dir} }
  files=append(files,row)
 }
 edges:=[]Edge{}
 for _,f:=range files {if f.Error!="" {continue};for _,im:=range f.Imports {target:=dirs[im];if target!="" {edges=append(edges,Edge{From:filepath.ToSlash(filepath.Dir(f.Path)),To:target,Import:im,Resolution:"local_source_candidate_build_tags_not_evaluated",Test:f.Test})}}}
 json.NewEncoder(os.Stdout).Encode(map[string]any{"files":files,"edges":edges,"module_roots":cfg.Modules,"limits":[]string{"Static syntax only. Build tags and platform selection are not evaluated.","Call spellings are source locations, not resolved execution edges.","Imports outside selected local modules may be standard-library, external, or unresolved.","Generated Go templates are not parsed as Go. No subject code is executed."}})
}
