##
## OwlMind - Platform for Education and Experimentation with Hybrid Intelligent Systems
## test_units.py :: tests for the diverse components
## 
# Copyright (c) 2025, The Generative Intelligence Lab @ FAU
# 
# v0.1 Initial release
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# Documentation:
#    https://github.com/genilab-fau/owlmind
#
# Disclaimer: 
# Generative AI has been used extensively while developing this package.
# 

from owlmind.rules import Element, Rule, RuleBase

##
## TEST :: ELEMENT MATCH
##

def test_element_match():
    print(Element._matcher("string key=1.0 string", r"re/key=([^\s]+)/"))  # (0.75, '1.0')
    print(Element._matcher("string key=1.0 string", "key=$*$"))  # (0.75, '1.0')
    print(Element._matcher("string key=1.0 string", "key=$*"))  # (0.75, '1.0 string')
    print(Element._matcher("string key=1.0 string", "*key*"))  # (x1, full_string)
    print(Element._matcher("string key=1.0 string", "*key=1.0*"))  # (x2>x1, full_string)
    print(Element._matcher("string key=1.0 string", "str*"))  # (x3==x1, full_string)
    print(Element._matcher("string key=1.0 string", "*ring"))  # (x4>x1, full_string)
    print(Element._matcher("42", 42))  # (1.0, 42)
    print(Element._matcher("3.14", 3.14))  # (1.0, 3.14)
    print(Element._matcher("100.0", 100))  # (0.9, 100.0001)
    print(Element._matcher(42, 43))  # (0, None)
    print(Element._matcher("hello", 42))  # (0, None)
    print(Element._matcher("3.14", "42"))  # (0, None)
    return

##
## TEST :: RULE SELECT
##

def test_rule_select():
    session = Element({'target':'api.openai.com', 'body':'string model=ollama string'})

    rb = RuleBase()
    rb += Rule(namespace='level-1', conditions={'target': '*.openai.com'}, actions= [('destination', 'ollama')], weight=0.20)
    rb += Rule(namespace='level-1', conditions={'target': '*.com'}, actions= [('destination', 'openai')], weight=0.80)
    rb += Rule(namespace='level-2', conditions={'target': '*.openai.com'}, actions= [('destination', 'Should_Not_Get_Here')], weight=1.00)

    best_rule, _, _ = rb.select(session, namespace='level-1', strategy=RuleBase.FIRST_MATCH)
    print('- RuleBase.FIRST_MATCH -->',best_rule)

    best_rule, _, _ = rb.select(session, namespace='level-1', strategy=RuleBase.BEST_MATCHES)
    print('- RuleBase.BEST_MATCHES -->',best_rule)

    best_rule, _, all_matches = rb.select(session, namespace='level-1', strategy=RuleBase.ALL_MATCHES)
    print('- RuleBase.ALL_MATCHES -->',best_rule, len(all_matches))

    count = dict()
    for i in range(100):
        best_rule, _, _ = rb.select(session, namespace='level-1', strategy=RuleBase.ALL_MATCHES)
        if best_rule:
            key = best_rule.__actions__[0][1]
            count[key] = count.get(key, 0) + 1
    print(count)

##
## TEST :: RULES EXECUTION
##

def test_rule_exec():

    rb = RuleBase()
    rb += Rule(namespace='f_provider', conditions={'h_host':'*openai*'}, actions= [('provider', 'openai')])
    rb += Rule(namespace='f_model', conditions={'provider':'openai', 'h_body':'model=$*$/@model'}, actions= [('model', '$h_body/model')])

    belief = Element()
    session = Element({'h_host':'api.openai.com', 'h_method':'/api/chat', 'h_body':'string model=llama3.2 string'})

    for ns in ['f_provider', 'f_model']:
        best_rule, _, _ = rb.select(namespace=ns, test=session, strategy=RuleBase.ALL_MATCHES)

        if best_rule:
            best_rule.execute(immediate=session, long=belief)
            print('NAMESPACE', ns)
            print('-- Session ->', session)
            print('-- Belief ->', belief)
            print()

##
## EXECUTE TEST UNITS
##
if __name__ == "__main__":
    #test_element_match()
    #test_rule_select()
    test_rule_exec()
    