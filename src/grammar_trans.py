from functools import reduce
from operator import iconcat
from typing import Union
from .custom_grammar import *

def flatten_list(lst):
    return reduce(iconcat, (flatten_list(x) if isinstance(x, list) else [x] for x in lst), [])

def dedup_list(lst:list):
    if(not lst or isinstance(lst,Node)):
        return [lst]
    new_list=[]
    add_none=False
    for item in lst:
        if(not item):
            add_none=True
            continue
        for it in new_list:
            if(item.equal(it)):
                break
        else:
            new_list.append(item)
    if(add_none):
        new_list.append(None)
    return new_list

def list_to_str(lst):
    if(not lst):
        return "None"
    elif(isinstance(lst,Node)):
        return str(lst)
    else:
        return ' , '.join(map(str, dedup_list(lst)))

class Node:
    def __init__(self,parent,type,index,leaf_node):#index in the parent node
        self.parent=parent
        self.type=type
        self.index=index
        self.leaf_node=leaf_node
        self.transform_rules=dict()
        self.deleted_child=list()
        self.deleted=False
        self.insert_end=dict()
    
    def __len__(self):
        return 1
    
    def get_children(self):
        if(hasattr(self,"members")):
            return self.members
        elif(hasattr(self,"content")):
            return [self.content]
        else:
            raise RuntimeError

    def get_first(self):
        return self
    
    def get_last(self):
        return self
    
    def get_next(self):
        if(not self.parent):
            return None
        if(isinstance(self.parent,SeqNode) and self.index<len(self.parent)-1):
            next_node=self.parent[self.index+1]
            return next_node.get_first()
        else:
            return self.parent.get_next()
    
    def get_prev(self):
        if(not self.parent):
            return None
        if(isinstance(self.parent,SeqNode) and self.index>0):
            prev_node=self.parent[self.index-1]
            return prev_node.get_last()
        else:
            return self.parent.get_prev()
        
    def get_field_name(self):
        current=self.parent
        while(current):
            if(isinstance(current,FieldNode)):
                return current.name
            current=current.parent
        return None
    
    def reconstruct_node(self):
        raise NotImplementedError

    def replace_child(self,index,new_node):
        if(hasattr(self,"members")):
            self.members[index]=new_node
        elif(hasattr(self,'content')):
            assert index==0
            self.content=new_node
        else:
            raise RuntimeError
        
    def delete_child(self,index):
        if(hasattr(self,"members")):
            self.deleted_child.append(index)
            if(len(self.members)==len(self.deleted_child)):
                self.parent.delete_child(self.index)
                self.deleted=True
        elif(hasattr(self,'content')):
            assert index==0
            self.parent.delete_child(self.index)
            self.deleted=True
        else:
            raise RuntimeError()

    def add_transformation(self,rule,applied_rules:set,conflict_rules:list):
        if(rule['action'] in self.transform_rules):
            if(rule['index']==self.transform_rules[rule['action']]['index']):
                return
            print("duplicated rules: "+str(self.transform_rules[rule['action']])+"; "+str(rule))
        elif(not rule['action'].startswith("custom")):
            self.transform_rules[rule['action']]=rule
            applied_rules.add(rule['index'])
            if(rule['action']=='insert_before' and 
               rule['index'] in self.insert_end):
                prev_node,prev_nexts=self.insert_end[rule['index']]
                self_prevs=self.get_prev()
                if(len(self_prevs)==1):
                    del self.transform_rules['insert_before']
                elif(len(prev_nexts)==1):
                    del prev_node.transform_rules['insert_after']
                    del self.insert_end[rule['index']]
                else:
                    conflict_rules.append((rule['index'],prev_node,self))
                # if(prev_node.get_depth()>self.get_depth()):
                #     del self.transform_rules['insert_before']
                # else:
                #     del prev_node.transform_rules['insert_after']
                #     del self.insert_end[rule['index']]
            elif(rule['action']=='insert_after' and 
               ("next_sibling" in rule['condition'] or "next_sibling_field" in rule['condition'])):
                nexts=self.get_next()
                if(isinstance(nexts,Node)):
                    nexts.insert_end[rule['index']]=(self,[nexts])
                elif(isinstance(nexts,list)):
                    for ne in nexts:
                        ne.insert_end[rule['index']]=(self,nexts)

    def get_depth(self):
        dep=1
        parent=self.parent
        while(parent):
            parent=parent.parent
            dep+=1
        return dep

class SeqNode(Node):
    def __init__(self,parent,members,idx):
        super().__init__(parent,"SEQ",idx,False)
        self.members=[build_node(self,members[i],i) for i in range(len(members))]

    def __len__(self):
        return len(self.members)
    
    def __getitem__(self,index):
        return self.members[index]

    def get_first(self):
        return self.members[0].get_first()

    def get_last(self):
        return self.members[-1].get_last()
    
    def reconstruct_node(self):
        assert not self.deleted
        members=[self.members[i].reconstruct_node() for i in range(len(self.members)) if i not in self.deleted_child]
        return {"type":"SEQ","members":members}
    
    def equal(self,node2):
        while(isinstance(node2,SeqNode) and len(node2)==1):
            node2=node2.members[0]
        node1=self
        while(isinstance(node1,SeqNode) and len(node1)==1):
            node1=node1.members[0]
        if(node1.type!=node2.type ):
            return False
        if(hasattr(node1,"members")):#seq,choice
            if(len(node1)!=len(node2)):
                return False
            for i in range(len(node1)):
                if(not node1.members[i].equal(node2.members[i])):
                    return False
            return True
        else:
            return node1.equal(node2)

class SymbolNode(Node):
    def __init__(self,parent,name,idx):
        super().__init__(parent,"SYMBOL",idx,True)
        self.name=name

    def __str__(self) -> str:
        return f"<SYMBOL> {self.name}"

    def equal(self,node2):
        if(not isinstance(node2,self.__class__)):
            return False
        return self.name==node2.name and self.get_field_name()==node2.get_field_name()
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":"SYMBOL","name":self.name}

class StringNode(Node):
    def __init__(self,parent,node_type,value,idx):
        super().__init__(parent,node_type,idx,True)
        self.value=value

    def __str__(self) -> str:
        return f"<{self.type}> {self.value}"
    
    def equal(self,node2):
        if(not isinstance(node2,self.__class__)):
            return False
        return self.type==node2.type and self.value==node2.value and self.get_field_name()==node2.get_field_name()

    def reconstruct_node(self):
        assert not self.deleted
        return {"type":self.type,"value":self.value}
    
class FieldNode(Node):
    def __init__(self,parent,name,content,idx):
        super().__init__(parent,"FIELD",idx,False)
        self.name=name
        self.content=build_node(self,content,0)

    def get_first(self):
        return self.content.get_first()
    
    def get_last(self):
        return self.content.get_last()
    
    def equal(self,node2):
        if(not isinstance(node2,FieldNode)):
            return False
        if(self.name!=node2.name):
            return False
        return self.content.equal(node2.content)
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":"FIELD","name":self.name,"content":self.content.reconstruct_node()}
    
class Repeat1Node(Node):
    def __init__(self,parent,content:Node,idx):
        super().__init__(parent,"REPEAT1",idx,False)
        self.content=build_node(self,content,0)

    def get_first(self):
        return self.content.get_first()
    
    def get_last(self):
        return self.content.get_last()
    
    def get_prev(self):
        return flatten_list([super().get_prev(),self.get_last()])
    
    def get_next(self):
        return flatten_list([super().get_next(),self.get_first()])
    
    def equal(self,node2):
        if(not isinstance(node2,Repeat1Node)):
            return False
        return self.content.equal(node2.content)
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":"REPEAT1","content":self.content.reconstruct_node()}

class ChoiceNode(Node):
    def __init__(self, parent, members,idx):
        super().__init__(parent, "CHOICE",idx,False)
        self.members=[build_node(self,members[i],i) for i in range(len(members))]

    def __len__(self):
        return len(self.members)

    def get_first(self):
        firsts=list()
        for ch in self.members:
            if(isinstance(ch,BlankNode)):
                firsts.append(self.get_next())
            else:
                firsts.append(ch.get_first())
        return flatten_list(firsts)
    
    def get_last(self):
        lasts=list()
        for ch in self.members:
            if(isinstance(ch,BlankNode)):
                lasts.append(self.get_prev())
            else:
                lasts.append(ch.get_last())
        return flatten_list(lasts)
    
    def equal(self,node2):
        if(not isinstance(node2,ChoiceNode)):
            return False
        if(len(self.members)!=len(node2.members)):
            return False
        for i in range(len(self.members)):
            if(not self.members[i].equal(node2.members[i])):
                return False
        return True
    
    def reconstruct_node(self):
        assert not self.deleted
        members=list()
        for i in range(len(self.members)):
            if(i in self.deleted_child):
                continue
            node_i=self.members[i].reconstruct_node()
            for m in members:
                if(check_node_equal(node_i,m)):
                    break
            else:
                members.append(node_i)
        if(len(members)==1):
            return members[0]
        return {"type":"CHOICE","members":members}

class RepeatNode(Node):
    def __init__(self,parent,content,idx):
        super().__init__(parent,"REPEAT",idx,False)
        self.content=build_node(self,content,0)

    def get_first(self):
        return flatten_list([self.content.get_first(),super().get_next()])
    
    def get_last(self):
        return flatten_list([self.content.get_last(),super().get_prev()])
    
    def get_prev(self):
        return self.get_last()
    
    def get_next(self):
        return self.get_first()
    
    def equal(self,node2):
        if(not isinstance(node2,RepeatNode)):
            return False
        return self.content.equal(node2.content)
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":"REPEAT","content":self.content.reconstruct_node()}
    
class AliasNode(Node):
    def __init__(self,parent,content,named,value,idx):
        super().__init__(parent,"ALIAS",idx,True)
        self.content=build_node(self,content,0)
        self.named=named
        self.value=value
        self.fake_node=self.build_fake_node(named,value)#no transform rules will apply

    def build_fake_node(self,named,value):
        if(named):
            self.type=f"${value}"
            return SymbolNode(self,value,-1)
        else:
            self.type=value
            return StringNode(self,"STRING",value,-1)

    def get_first(self):
        return self.fake_node
    
    def get_last(self):
        return self.fake_node
    
    def equal(self,node2):
        if(not isinstance(node2,AliasNode)):
            return False
        if(self.value!=node2.value or self.named!=node2.named):
            return False
        return self.content.equal(node2.content)
    
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":"ALIAS","content":self.content.reconstruct_node(),"named":self.named,"value":self.value}
    
    def apply_replace_rule(self,rule):
        ori_element=rule['ori_element']
        if(ori_element['type'].startswith("$")):
            self.named=True
            self.value=ori_element['type'].replace("$","")
        else:
            self.named=False
            self.value=ori_element['type']
        self.content=StringNode(self,"STRING",ori_element['text'],0)
        # self.build_fake_node(self.named,self.value)

class BlankNode(Node):
    def __init__(self,parent,idx):
        assert isinstance(parent,ChoiceNode)
        super().__init__(parent,"BLANK",idx,True)

    def reconstruct_node(self):
        return {"type":"BLANK"}
    
    def get_first(self):
        raise RuntimeError
    
    def get_last(self):
        raise RuntimeError
    
    def get_prev(self):
        raise RuntimeError
    
    def get_next(self):
        raise RuntimeError
    
    def equal(self,node2):
        return isinstance(node2,BlankNode)
    
class PrecNode(Node):
    def __init__(self,parent,node_type,content,value,idx):
        super().__init__(parent,node_type,idx,False)
        self.content=build_node(self,content,0)
        self.value=value

    def get_first(self):
        return self.content.get_first()
    
    def get_last(self):
        return self.content.get_last()
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":self.type,"content":self.content.reconstruct_node(),"value":self.value}
    
    def equal(self,node2):
        if(not isinstance(node2,PrecNode)):
            return False
        return self.type==node2.type and self.value==node2.value and self.content.equal(node2.content)

class TokenNode(Node):
    def __init__(self,parent,node_type,content,idx):
        super().__init__(parent,node_type,idx,True)
        self.content=build_node(self,content,0)

    # def get_first(self):
    #     return self.content.get_first()
    
    # def get_last(self):
    #     return self.content.get_last()
    
    def reconstruct_node(self):
        assert not self.deleted
        return {"type":self.type,"content":self.content.reconstruct_node()}
    
    def equal(self,node2):
        if(not isinstance(node2,TokenNode)):
            return False
        return self.type==node2.type and self.content.equal(node2.content)
    
class RootNode:
    def __init__(self,child:Node):
        self.parent=None
        self.leaf_node=False
        assert child.parent==None
        self.child=child
        self.child.parent=self
        self.start=SentinelNode(True)
        self.end=SentinelNode(False)
    
    def get_children(self):
        return [self.child]
    
    def get_prev(self):
        return self.start
    
    def get_next(self):
        return self.end
    
    def get_first(self):
        return self.child.get_first()
    
    def get_last(self):
        return self.child.get_last()
    
    def replace_child(self, index, new_node):
        self.child=new_node

    #delete child -> delete the whole rule

    def reconstruct_node(self):
        children=list()
        if(self.start.transform_rules):
            for ln in self.start.transform_rules['insert_after']['ori_elements']:
                leaf_node=build_leaf_node(self,ln,-1)
                children.append(leaf_node.reconstruct_node())
        children.append(self.child.reconstruct_node())
        if(self.end.transform_rules):
            for ln in self.start.transform_rules['insert_before']['ori_elements']:
                leaf_node=build_leaf_node(self,ln,-1)
                children.append(leaf_node.reconstruct_node())
        if(len(children)==1):
            return children[0]
        else:
            return {"type":"SEQ","members":children}

class SentinelNode(Node):
    def __init__(self,start:bool):
        self.start=start
        self.transform_rules=dict()
        self.leaf_node=True

    def get_field_name(self):
        return None
    
    def equal(self,node2):
        if(not isinstance(node2,SentinelNode)):
            return False
        return self.start==node2.start
    
    def get_prev(self):
        return self
    
    def get_next(self):
        return self
    
    def add_transformation(self,rule,applied_rules,conflict_rules):
        if(self.start):
            assert rule['action']=='insert_after'
        else:
            assert rule['action']=='insert_before'
        super().add_transformation(rule,applied_rules,conflict_rules)

def build_tree(rule):
    #build a tree for one rule(to find parent)
    return build_node(None,rule,0)

def reconstruct_rule(root_node:Node):
    return root_node.reconstruct_node()

def check_node_equal(node1:dict,node2:dict):
    while("members" in node1 and len(node1['members'])==1):#seq & choice
        node1=node1['members'][0]
    while("members" in node2 and len(node2['members'])==1):
        node2=node2['members'][0]
    for k,v in node1.items():
        if(k not in node2):
            return False
        if(k=='members' or k=='content'):
            continue
        if(node2[k]!=v):
            return False
    if("content" in node1):
        return check_node_equal(node1['content'],node2['content'])
    if("members" in node1):
        if(len(node1['members'])!=len(node2['members'])):
            return False
        for i in range(len(node1['members'])):
            if(not check_node_equal(node1['members'][i],node2['members'][i])):
                return False
    return True

def build_node(parent,node,idx):
    if(isinstance(node,Node)):
        return node
    elif(node['type']=='SEQ'):
        return SeqNode(parent,node['members'],idx)
    elif(node['type']=='CHOICE'):
        return ChoiceNode(parent,node['members'],idx)
    elif(node['type']=='REPEAT'):
        return RepeatNode(parent,node['content'],idx)
    elif(node['type']=='REPEAT1'):
        return Repeat1Node(parent,node['content'],idx)
    elif(node['type']=='SYMBOL'):
        return SymbolNode(parent,node['name'],idx)
    elif(node['type'] in ['STRING','PATTERN']):
        return StringNode(parent,node['type'],node['value'],idx)
    elif(node['type']=='FIELD'):
        return FieldNode(parent,node['name'],node['content'],idx)
    elif(node['type']=='BLANK'):
        return BlankNode(parent,idx)
    elif(node['type']=='ALIAS'):
        return AliasNode(parent,node['content'],node['named'],node['value'],idx)
    elif(node['type'] in ['PREC','PREC_LEFT','PREC_RIGHT','PREC_DYNAMIC']):
        return PrecNode(parent,node['type'],node['content'],node['value'],idx)
    elif(node['type'] in ['IMMEDIATE_TOKEN','TOKEN']):
        return TokenNode(parent,node['type'],node['content'],idx)
    else:
        raise NotImplementedError
    
def build_leaf_node(parent,node,idx):
    if(isinstance(node,str)):
        node={"type":node}
    if(node['type'].startswith("$")):
        build_node=SymbolNode(parent,node['type'].replace("$",""),idx)
    else:
        build_node=StringNode(parent,"STRING",node['type'],idx)
    if(node.get("field",None)):
        field_node=FieldNode(parent,node['field'],build_node,idx)
        build_node.parent=field_node
        return field_node
    else:
        return build_node
    
def build_rules_applied_node(node:Node):
    assert isinstance(node,SymbolNode) or isinstance(node,StringNode) \
        or isinstance(node,TokenNode) or isinstance(node,AliasNode) \
        or isinstance(node,FieldNode) or isinstance(node,PrecNode) \
        or len(node.transform_rules)==0
    if(len(node.transform_rules)==0):
        return
    node_list=list()
    if("insert_before" in node.transform_rules):
        node_list.extend([build_leaf_node(node,ln,-1) for ln in node.transform_rules['insert_before']['ori_elements']])
    if("delete" not in node.transform_rules and "replace" not in node.transform_rules):
        node_list.append(node)
    elif("replace" in node.transform_rules):
        if(isinstance(node,AliasNode)):
            node.apply_replace_rule(node.transform_rules['replace'])
            node_list.append(node)
        else:
            node_list.append(build_leaf_node(node,node.transform_rules['replace']['ori_element'],-1))
    if("insert_after" in node.transform_rules):
        node_list.extend([build_leaf_node(node,ln,-1) for ln in node.transform_rules['insert_after']['ori_elements']])
    if(len(node_list)==0):
        node.parent.delete_child(node.index)
    elif(len(node_list)==1):
        node.parent.replace_child(node.index,node_list[0])
    else:
        new_node=SeqNode(node.parent,node_list,node.index)
        node.parent.replace_child(node.index,new_node)

def adjust_transform_rule(node:Node):
    parent_node=node
    while(isinstance(parent_node.parent,FieldNode) or isinstance(parent_node.parent,PrecNode)):
        parent_node=parent_node.parent
    if(parent_node!=node):
        if("insert_before" in node.transform_rules):
            parent_node.transform_rules['insert_before']=node.transform_rules['insert_before']
            del node.transform_rules['insert_before']
        if("insert_after" in node.transform_rules):
            parent_node.transform_rules['insert_after']=node.transform_rules['insert_after']
            del node.transform_rules['insert_after']

def traverse_tree(root_node:Node,func,visit_inter=False,**args):
    if(root_node.leaf_node):
        func(root_node,**args)
    else:
        children=root_node.get_children()
        for child in children:
            traverse_tree(child,func,visit_inter,**args)
        if(visit_inter):
            func(root_node,**args)

def check_prev_next_sibling(node:Node):
    print(str(node))
    if(isinstance(node,BlankNode)):
        return
    print(list_to_str(node.get_prev()))
    print(list_to_str(node.get_next()))
    print("")

def record_rules_applied(node,**args):
    if(isinstance(node,BlankNode)):
        return
    information=get_information(node)
    if(args['rname']):
        information['parent_type']=args['rname']
    for r in args['rules']:
        check_rule(r,node,information,args['applied_rules'],args['conflict_rules'])

def get_type(node:Union[SymbolNode,StringNode]):
    if(not node):
        return None
    elif(isinstance(node,SentinelNode)):
        return None
    elif(isinstance(node,SymbolNode)):
        return f"${node.name}"
    elif(isinstance(node,StringNode)):
        return node.value
    elif(isinstance(node,TokenNode)):
        return None
    elif(isinstance(node,AliasNode)):
        return node.type
    else:
        raise NotImplementedError

def get_information(node:Union[SymbolNode,StringNode,SentinelNode]):
    node_type=get_type(node)
    field_name=node.get_field_name()
    symbol=True if isinstance(node,SymbolNode) else False
    prev_sibs=dedup_list(node.get_prev())
    prev_sibs_field=set([sib.get_field_name() if sib else None for sib in prev_sibs])
    prev_inf={}
    if(len(prev_sibs)==1):
        prev_inf['prev_sibling']=get_type(prev_sibs[0])
    if(len(prev_sibs_field)==1):
        prev_inf['prev_sibling_field']=next(iter(prev_sibs_field))
    next_sibs=dedup_list(node.get_next())
    next_sibs_field=set([sib.get_field_name() if sib else None for sib in next_sibs])
    next_inf={}
    if(len(next_sibs)==1):
        next_inf['next_sibling']=get_type(next_sibs[0])
    if(len(next_sibs_field)==1):
        next_inf['next_sibling_field']=next(iter(next_sibs_field))
    return {"type":node_type,"field":field_name,"symbol":symbol,
            "prev_sibs":prev_sibs,"prev_sibs_field":prev_sibs_field,**prev_inf,
            "next_sibs":next_sibs,"next_sibs_field":next_sibs_field,**next_inf}

def check_rule(rule,node:Node,information,applied_rules,conflict_rules):
    # information=get_information(node)
    condition=rule['condition']
    if(check_condition(information,condition)):
        node.add_transformation(rule,applied_rules,conflict_rules)
    elif(rule['action']=='insert_after' and 
         ("next_sibling" in condition or "next_sibling_field" in condition) and 
         ("prev_sibling" not in condition and "prev_sibling_field" not in condition)):
        new_condition=insert_after_to_before(condition)
        for ns in information['next_sibs']:
            next_information=get_information(ns)
            if("parent_type" in information):
                next_information['parent_type']=information['parent_type']
            if(check_condition(next_information,new_condition)):
                new_rule={"condition":new_condition,
                            "action":"insert_before","content":rule['content'],
                            'index':rule['index'],"ori_elements":rule['ori_elements']}
                ns.add_transformation(new_rule,applied_rules,conflict_rules)
                break
    elif(rule['action']=='insert_before' and 
         ("prev_sibling" in condition or "prev_sibling_field" in condition) and 
         ("next_sibling" not in condition and "next_sibling_field" not in condition)):
        new_condition=insert_before_to_after(condition)
        for ps in information['prev_sibs']:
            prev_information=get_information(ps)
            if("parent_type" in information):
                prev_information['parent_type']=information['parent_type']
            if(check_condition(prev_information,new_condition)):
                new_rule={"condition":new_condition,
                            "action":"insert_after","content":rule['content'],
                            'index':rule['index'],"ori_elements":rule['ori_elements']}
                ps.add_transformation(new_rule,applied_rules,conflict_rules)
                break
    
def check_condition(information,condition):
    for k,v in condition.items():
        if(k not in information or information[k]!=v):
            return False
    return True

def insert_after_to_before(condition):
    assert "prev_sibling" not in condition and "prev_sibling_field" not in condition
    new_condition={}
    if("type" in condition):
        new_condition["prev_sibling"]=condition['type']
    if("field" in condition):
        new_condition["prev_sibling_field"]=condition['field']
    if("next_sibling" in condition):
        new_condition['type']=condition['next_sibling']
    if("next_sibling_field" in condition):
        new_condition['field']=condition['next_sibling_field']
    if("parent_type" in condition):
        new_condition['parent_type']=condition['parent_type']
    return new_condition

def insert_before_to_after(condition):
    assert "next_sibling" not in condition and "next_sibling_field" not in condition
    new_condition={}
    if("type" in condition):
        new_condition["next_sibling"]=condition['type']
    if("field" in condition):
        new_condition["next_sibling_field"]=condition['field']
    if("prev_sibling" in condition):
        new_condition['type']=condition['prev_sibling']
    if("prev_sibling_field" in condition):
        new_condition['field']=condition['prev_sibling_field']
    if("parent_type" in condition):
        new_condition['parent_type']=condition['parent_type']
    return new_condition

def replace_named_nodes(root_node,rule,applied_rules):
    if(not rule):
        return
    root_node.replace_child(0,build_leaf_node(root_node,rule['ori_element']['text'],0))
    applied_rules.add(rule['index'])

def modify_grammar_json(grammar_rules,compiled_transform_rules,custom_modifications=None):
    normal_rules=list()
    named_replace_rules=dict()
    not_update_rules=list()
    for i,r in enumerate(compiled_transform_rules):
        r['index']=i
        #replace a rule
        if(not r.get("update_grammar",True)):
            not_update_rules.append(i)
        elif(r['action']=='replace'
            and len(r['condition'])==1 and "type" in r['condition']
            and r['condition']['type'].startswith("$")
            and r['condition']['type']==r['ori_element']['type']):#change the grammar rule of itself
                rname=r['condition']['type'].replace("$","")
                named_replace_rules[rname]=r
        else:
            normal_rules.append(r)
    applied_rules=set()
    conflict_rules=list()
    new_grammar=dict()
    for rname,rcontent in grammar_rules.items():
        # print(rname)
        root_node=build_tree(rcontent)
        root_node=RootNode(root_node)
        # traverse_tree(root_node,check_prev_next_sibling)
        # print("----")
        #conflict rules: the same rule(converted between insert_before and insert_after) apply to the same position 
        # and neither contains the other
        traverse_tree(root_node,record_rules_applied,rname=rname,rules=normal_rules,
                      applied_rules=applied_rules,conflict_rules=conflict_rules)
        #if rule=insert&node.type in [field,prec] -> the element should be added outside field/prec
        traverse_tree(root_node,adjust_transform_rule)
        traverse_tree(root_node.child,build_rules_applied_node,visit_inter=True)
        replace_named_nodes(root_node,named_replace_rules.get(rname,None),applied_rules)
        new_content=reconstruct_rule(root_node)
        new_grammar[rname]=new_content
    unapplied_rules=list()
    for r in compiled_transform_rules:
        if(r['index'] not in not_update_rules and r['index'] not in applied_rules):
            unapplied_rules.append(r)
        del r['index']
        if("ori_elements" in r):
            del r['ori_elements']
        elif('ori_element' in r):
            del r['ori_element']
    if(len(unapplied_rules)>0):
        print("unapplied transformation rules:")
        for r in unapplied_rules:
            print(str(r))
    if(len(conflict_rules)>0):
        print("conflict occurs when applying transformation rules:")
        for it in conflict_rules:
            print(str(it))
    if(custom_modifications):
        for func_name in custom_modifications:
            globals()[func_name](new_grammar)
    return new_grammar