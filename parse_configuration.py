import argparse
from src.parse_config import read_rules_from_json

if __name__=="__main__":
    argument_parser=argparse.ArgumentParser()
    argument_parser.add_argument("--rule_path",type=str,default="grammar_configs/example.json")
    argument_parser.add_argument("--custom_grammar_modification",type=str)
    args=argument_parser.parse_args()
    grammar_modification=args.custom_grammar_modification.split(",") if args.custom_grammar_modification else None
    read_rules_from_json(args.rule_path,grammar_modification)