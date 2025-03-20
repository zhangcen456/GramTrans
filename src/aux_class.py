class SentinelNode:
    def __init__(self,parent):
        self.parent=parent
        self.type='sentinel'

class CustomException(Exception):
    def __init__(self,message):
        self.message=message
        super().__init__(self.message)

#build a node for string
class StringNode:
    def __init__(self,content):
        if(isinstance(content,dict)):
            self.type=content['type']
        else:#type(content)=string
            self.type=content
        self.is_named=False

    def __str__(self):
        return f"<StringNode type={self.type}>"
    
class AuxInf:
    def __init__(self,ori_idx=None,field_name=None,applied_rules=None):
        self.ori_idx=ori_idx
        self.field_name=field_name
        self.applied_rules=applied_rules

    def rules_applied(self,rule_index):#whether the rule has been applied in this position
        if(not self.applied_rules):
            return False
        return rule_index in self.applied_rules
    
    def add_rule(self,rule_index):
        if not self.applied_rules:
            self.applied_rules=[rule_index]
        else:
            self.applied_rules.append(rule_index)
    
    def to_str(self):
        return " ".join([str(self.ori_idx),str(self.field_name),str(self.applied_rules).replace(" ","")])
    
    @classmethod
    def load_from_str(cls,string):
        ori_idx,field_name,applied_rules=string.split(" ")
        if(field_name=='None'):
            field_name=None
        return cls(eval(ori_idx),field_name,eval(applied_rules))