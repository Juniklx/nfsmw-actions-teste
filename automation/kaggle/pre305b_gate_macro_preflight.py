#!/usr/bin/env python3
"""PRE305B: safe synthetic C++ preprocessor audit for scoped menu #define.
No PRE99 archive, APK, game object, save, signing material, or Drive access.
"""
from pathlib import Path
import ast, subprocess, shutil, sys, tempfile, json

ROOT=Path(__file__).resolve().parents[2]
BUILDER=ROOT/"automation/kaggle/pre305_build_signed_v40_bmw_menu_gate_experimental.py"
RECIPE=ROOT/"automation/kaggle/pre264_bmw_hero_menu_patch_dryrun.py"
DIRECTIVE="#define NFSMW_PRE264_BMW_MENU_ENABLE 1"

def constants_from(tree):
    return [n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]

def recipe_constant(tree, name):
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("pre264 constant missing")

def main():
    data=BUILDER.read_text(encoding="utf8")
    recipe=RECIPE.read_text(encoding="utf8")
    tree=ast.parse(data,filename=str(BUILDER))
    rt=ast.parse(recipe,filename=str(RECIPE))
    macros=[x for x in constants_from(tree) if x.startswith(DIRECTIVE)]
    if len(macros)!=2 or any(x!=DIRECTIVE+"\n" for x in macros):
        raise ValueError("bad literal line ending in Python macro")
    inject=recipe_constant(rt,"INJECTION")
    if inject.count("NFSMW_PRE264_BMW_MENU_LOCAL")!=1:
        raise ValueError("unexpected recipe injection")
    sample='''struct Compare { bool eq; };
struct Register { int s32; };
struct Ctx { Register r3; };
void menu(Ctx ctx) {
  Compare cr6{ctx.r3.s32 == 41};
'''
    sample+=macros[0]+inject+'\n  (void)cr6;\n}\n'
    if sample.count(DIRECTIVE+"\n")!=1 or DIRECTIVE+r"\n" in sample:
        raise ValueError("malformed generated C++ macro")
    comp=shutil.which("clang++") or shutil.which("g++")
    if not comp:
        raise ValueError("no C++ compiler")
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre305b-") as d:
        file=Path(d)/"test.cpp"
        file.write_text(sample,encoding="utf8")
        p=subprocess.run([comp,"-std=c++17","-Wall","-Wextra","-Werror",
                          "-fsyntax-only",str(file)],capture_output=True,text=True,timeout=40)
        if p.returncode:raise ValueError("synthetic compiler rejected macro or guarded C++")
    print("PRE305B_MACRO_AST_OK True")
    print("PRE305B_SYNTHETIC_CPP_COMPILE_OK True")
    print("PRE305B_GAME_SOURCE_MODIFIED False")
    print("PRE305B_APK_BUILT False")

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("PRE305B_PREFLIGHT_FAILED",type(e).__name__)
        raise SystemExit(1)
