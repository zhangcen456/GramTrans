import argparse
from tree_sitter import Language

if __name__=="__main__":
    argument_parser=argparse.ArgumentParser()
    argument_parser.add_argument("--output_path",type=str)
    argument_parser.add_argument("--repo_path",type=str)
    args=argument_parser.parse_args()
    Language.build_library(
        args.output_path,[args.repo_path]
    )