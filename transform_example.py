from src.build_parser import build_parser
from src.build_unparser import build_unparser

def read_source_code(filepath):
    with open(filepath,'r') as f:
        lines=f.readlines()
    return "".join(lines)

ori_parser=build_parser(True)
new_parser=build_parser(False)

unparser1=build_unparser(ori_to_new=True,new_to_ori=False,filepath="grammar_configs/simpy.ori_to_new.json")
unparser2=build_unparser(ori_to_new=False,new_to_ori=True,filepath="grammar_configs/simpy.new_to_ori.json")

source_code=read_source_code("examples/example.py")
ori_tree=ori_parser.parse(bytes(source_code,'utf8'))
unparser1.unparse(ori_tree)
new_code=unparser1.get_code()
print(new_code)
print("")
new_tree=new_parser.parse(bytes(new_code,'utf8'))
unparser2.unparse(new_tree)
converted_code=unparser2.get_code()
print(converted_code)