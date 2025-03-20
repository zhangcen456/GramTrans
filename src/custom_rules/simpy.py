from ..utils import writing_op
from ..aux_class import StringNode,AuxInf,CustomException

@writing_op
def choice_comment_line_sep(self,node,**kwargs):
    #if there are comments, write down; otherwise append <line_sep>
    if(self.comments):
        self.maybe_newline(add_comment=True)
    else:
        self.write("<line_sep>")

def raise_exception(self,node,**kwargs):
    message=kwargs['message']
    raise CustomException(message)


def empty_parameters(self,index,**args):
    #if the parameters is empty, the children is missed in spy parse tree
    assert self.children[index].type=='identifier'
    new_index=index
    if(self.children[new_index+1].type=='type_parameter'):
        new_index=new_index+1
    if(self.children[new_index+1].type!='parameters'):
        parameter_node=TreeNode("parameters",True,[StringNode("("),StringNode(")")],[None,None],b'()')
        self.children.insert(new_index+1,parameter_node)
        self.aux_infs.insert(new_index+1,AuxInf(field_name="parameters"))
    return index

class TreeNode:
    def __init__(self,type,is_named:bool,children,field_names,text):
        self.type=type
        self.is_named=is_named
        self.children=children
        self.field_names=field_names
        self.text=text

    def __str__(self):
        return f"<TreeNode type={self.type}>"
    
    def field_name_for_child(self,index):
        if(index<0 or index>=len(self.field_names)):
            return None
        return self.field_names[index]
    
    
def text_replace(self,index,**args):
    text=args['text']
    node_type=self.children[index].type
    self.children[index]=TreeNode(node_type,True,list(),list(),text.encode("utf8"))
    return index