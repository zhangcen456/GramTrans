class PythonConfig:
    extras=['comment',"line_continuation"]
    zero_len_tokens=['_indent','_dedent',"_newline","_string_content","_space","_start_line","_space_line","_node_content"]
    inline_symbols=['_as_pattern', '_collection_elements', '_compound_statement', '_comprehension_clauses', 
                    '_dedent', '_expression_within_for_in_clause', '_expressions', '_f_expression', '_import_list', 
                    '_indent', '_is_not', '_key_value_pattern', '_left_hand_side', '_list_pattern', '_match_block', 
                    '_named_expression_lhs', '_newline', '_node_content', '_not_escape_sequence', '_not_in', 
                    '_parameters', '_patterns', '_right_hand_side', '_simple_pattern', '_simple_statement', 
                    '_simple_statements', '_space', '_space_line', '_start_line', '_statement', '_string_content', 
                    '_suite', '_tuple_pattern', 'expression', 'keyword_identifier', 'parameter', 'pattern', 
                    'primary_expression']
    externals=["_indent","_dedent","string_start","string_end","_newline","comment","_string_content","escape_interpolation"]
    custom_externals=["_space","_start_line","_space_line","_node_content"]
    supertypes=["_simple_statement","_compound_statement","expression","primary_expression",
                "pattern","parameter"]

import json
with open("config.json",'r') as f:
    config=json.load(f)
if(config['language']=='python'):
    language_config=PythonConfig
else:
    raise NotImplementedError(f"language {config['language']} not implemented")