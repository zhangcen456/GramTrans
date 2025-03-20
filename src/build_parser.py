from tree_sitter import Language, Parser
# import tree_sitter_python as ts_python
import json
with open("config.json",'r') as f:
    config=json.load(f)

def build_parser(ori=True):
    if(ori):
        path = config['original_library']
    else:
        path = config['new_library']
    LANGUAGE = Language(path,config['language'])
    parser = Parser()
    parser.set_language(LANGUAGE)
    return parser