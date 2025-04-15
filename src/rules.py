##
## OwlMind - Platform for Education and Experimentation with Hybrid Intelligent Systems
## rules.py :: implementations for Knowledge Element, Rules, and Rule Base
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

import re
import random
from collections.abc import Iterable

###
### UTILITIES
###

DEFAULT_NAMESPACE = '_'
GEN_ID_S = {}
GEN_ID = lambda ctx: f"{ctx}{GEN_ID_S.setdefault(ctx, 0) + 1}" if not (GEN_ID_S.update({ctx: GEN_ID_S.get(ctx, 0) + 1})) else None



###
### KNOWLEDGE ELEMENT
###

class Element():
    """
    Create a Knowledge Element.

    - facts: DICT or LIST OF TUPLES (key,value) 
    - any Iterable will be loaded as long as it can be unpacked as (key, value)
    """
    def __init__(self, facts=None):
        if facts and isinstance(facts, dict):
            facts = facts.items()
        
        if isinstance(facts, Iterable):
            for key, value in facts:
                self[key] = value

        return
    
    def __contains__(self, key):
        return hasattr(self, key)
    
    def __getitem__(self, key):
        return getattr(self, key, None)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        return "{" + ", ".join(f"{key}: {value!r}" for key, value in self.__dict__.items() if not key.startswith("__")) + "}"


    @staticmethod
    def _matcher(value, test):
        """
        Match a value against a test.
        Returns: match_quality =[0,1]
    
        - Exact match -> 1.0
        - Wildcard '*' matches anything -> 0.25
        - Supports str and int
        - Endswith match '*str' -> length of match / length of value1
        - Startswith match 'str*' -> length of match / length of value1
        - Contains match '*str*' -> length of match / length of value1
        - Startswith + endswith 'str1*str2' -> combined match / length of value1
        - Regex match 're/regex/' -> 0.75 if matches
        """

        match_quality = 0.0
        match_value = value
        match_target = None

        # Normalize for different types
        # ** Convert numeric strings to numbers before comparison **
        if isinstance(value, str) and isinstance(test, (int, float)):
            try:
                value = float(value) if "." in value else int(value)
            except ValueError:
                pass  # Ignore if conversion fails
        elif isinstance(test, str) and isinstance(value, (int, float)):
            try:
                test = float(test) if "." in test else int(test)
            except ValueError:
                pass  # Ignore if conversion fails


        # String match
        if isinstance(value, str) and isinstance(test, str):
            # Exact match
            if value == test:
                match_quality = 1.0
        
            # Wildcard match ('*' matches anything)
            elif test == '*':
                match_quality = 0.25
        
            # Regex match ('re/regex/')
            elif test.startswith("re/"):
                pattern = test[3:-1] if test.endswith("/") else test[3:]
                try:
                    match = re.search(pattern, value)

                    if match:
                        match_value = match.group(1) if match.groups() else match.group(0)
                        match_quality = 0.75
                except re.error:
                    pass 

            # Start-matching or Extract-matching   
            elif '*' in test:

                # Extract-matching 
                if '$*' in test:
                    match_target = 'match'
                    if '/@' in test:
                        test, match_target = test.split('/@')

                    pattern = re.escape(test).replace(r'\$\*\$', r"([^\s]+)") if '$*$' in test \
                                else  re.escape(test).replace(r'\$\*', "(.*)")

                    match = re.search(pattern, value)
                
                    if match:
                        match_value = match.group(1)
                        match_quality = 0.75

                # Star-matching for *str and *str*
                elif test.startswith('*'):
                    if test.endswith('*'):
                        pattern = test[1:-1]
                        if pattern in value:
                            match_quality = len(pattern) / len(value)
                    else:
                        pattern = test[1:]
                        if value.endswith(pattern):
                            match_quality = len(pattern) / len(value)
                
                # Star-matching for str*
                elif test.endswith('*'):
                    pattern = test[:-1]
                    if pattern in value:
                        match_quality = len(pattern) / len(value)
                
                # Star-matching for str*str
                else:
                    prefix, _, suffix = test.partition('*')
                    if value.startswith(prefix) and value.endswith(suffix):
                        match_quality = (len(prefix) + len(suffix)) / len(value)
        
        # Numeric match
        elif isinstance(value, (int, float)) and isinstance(test, (int, float)):
            if value == test:  
                match_quality = 1.0
            elif abs(value - test) < 1e-6:  # Allow close matches for floats
                match_quality = 0.9
                    
        return match_quality, match_value if match_quality else None, match_target


    def match(self, test):
        """
        Check whether this Element embeds (contains) the Test-Element.

        - All fields in this Elements (except the ones starting with '__') must exist in the test Element.
        - All values of the intersecting fields must match.
        - The match score is calculated based on the number of matching fields and quality of matching.
        - Returns match score (0 means no match; add (100 + match_quality) for each field being matched.
        """

        if isinstance(test, dict):
            test = Element(test)

        score = 0
        for key, test in test.__dict__.items():
            if key.startswith("__"):
                pass
            else:
                if hasattr(self, key):
                    score_l, value_l, target_l = Element._matcher(value=self[key], test=test)
                    if target_l:
                        self[key + '/' + target_l] = value_l
                    score += 100 + score_l
                    if not score_l:
                        score = 0
                        break
                else: # means that a key is not in the test element
                    score = 0
                    break
        return score

###
### RULE
###

class Rule():
    def __init__(self, conditions, actions, weight=1.0, namespace=DEFAULT_NAMESPACE):
        """
        Create the Rule.

        - conditions: ELEMENT as test condition for Knowledge Element
        - actions: LIST OF TUPLES (action,params) e.g. [(action_1, value_1), ..., (action_n, value_n)]
        """ 
        self.__id__ = GEN_ID('r-')
        self.__namespace__ = namespace if namespace else DEFAULT_NAMESPACE
        self.__conditions__ = Element(conditions) if isinstance(conditions, dict) else conditions
        self.__actions__ = actions
        self.__weight__ = weight
        self.__repr_cache__ = None
        return 
    
    def __repr__(self):
        if not self.__repr_cache__:
            actions_repr = ", ".join(f"({action}, {params})" for action, params in self.__actions__)
            self.__repr_cache__ = f"Rule[{self.__id__}]:conditions=[{self.__conditions__ }], actions=[{actions_repr}], weight={self.__weight__}"
        return self.__repr_cache__


    @property
    def id(self):
        """ Return rule identifier """
        return self.__id__
    
    def match(self, knowledge:Element):
        """
        Check whether the Rule.condition matches the Knowledge.
        - Returns match score (=0 means no match; 100 * fields matched + sum(match_qualities).
        """
        return knowledge.match(self.__conditions__)
    
    @staticmethod
    def _action_memory(key, value, immediate, long):
        """
        """
        force_long = False

        # Adjust key to consider @key
        if key.startswith('@'):
            key = key[1:]
            force_long = True
        
        # Adjust `value` to consider @value
        if value and isinstance(value,str) and value.startswith('$'):
            v_key = value[1:]
            value = immediate[v_key] if v_key in immediate \
                    else long[v_key] if long and v_key in long \
                    else None
            
        # Process memory assignment
        if long and (key in long or force_long):
            long[key] = value
        elif immediate and not force_long:
            immediate[key] = value
        return 

    @staticmethod
    def _is_action_artifact(action):
        return isinstance(action, str) and action.startswith('!') 

    @staticmethod
    def _action_artifact(artifacts, func_name, params=None):
        pass

    def execute(self, immediate, long=None, artifacts=None):
        """
        Execution a rule against target environment:
        - Immediate memory
        - Long-term memory
        - Artifacts: class providing method process(func_name, kwargs)
    
        Rule language; if action is formatted as:
        - VALUE (no key): exec as DEFAULT_KEY:VALUE, if default_key, else Fail!
        - KEY:VALUE: call `_action_memory`  $$$ key:value assignment to `immediate` then `long`; if none, apply to `immediate`
        - @KEY:VALUE: call `_action_memory` apply key:value assignment to `long`
        - !FUNCTION:PARAMS: call `_action_artifact`
        - {[@]key:value, ...} (dict): for each <*key,value>, exec *KEY:VALUE
        - ([@]key,value) (tuple): exec *KEY:VALUE
        - (!function, params, ...): exec @FUNCTION:VALUES 
        """
        for action in self.__actions__:
            if isinstance(action, dict):
                for k, v in action.elements():
                    Rule._action_memory(k, v, immediate, long)
            elif isinstance(action, tuple):
                # If only ONE element, it could be an FUNCTION:PARAM  or DEFAULT_KEY
                if len(action) == 1:
                    if Rule._is_action_artifact(action[0]):
                        Rule._action_artifact(artifacts, action[0])
                    elif self.DEFAULT_KEY:
                        Rule._action_memory(self.DEFAULT_KEY, action, immediate, long)
                # If only TWO elements, it could be an FUNCTION:PARAM or KEY:VALUE
                elif len(action) == 2:
                    if Rule._is_action_artifact(action[0]):
                        Rule._action_artifact(artifacts, action[0], action[1])
                    else:
                        Rule._action_memory(action[0], action[1], immediate, long)

        return


###
### RULE BASE
###

class RuleBase(dict):
    """
    Matching strategies.

    - FIRST_MATCH: it will cut the process on the first match, regardless of match_quality
    - BEST_MATCHES: it will consider the options between the best matches only
    - ALL_MATCHES: it will consider the options between all matches
    """
    FIRST_MATCH = 0
    BEST_MATCHES = 1
    ALL_MATCHES = 2

    def __init__(self):
        """
        Init as a dict of sets.
        Indexed by namespaces.
        """
        super().__init__()
        return 
    
    def __iadd__(self, rule:Rule):
        """
        Add Rule to base grouping per namespace.
        """
        if not rule.__namespace__ in self:
            self[rule.__namespace__] = set()
        self[rule.__namespace__].add(rule)
        return self

    def select(self, test:Element, namespace=None, strategy=1):
        """
        Select Best Rules that match the Test-Element.
        Default strategy = RuleBase.BEST_MATCHES

        - namespace (str or list): restricts the search space to a search_space; namespace=None means it will run across the whole base
        - strategy: define selection strategy (see above)
        - returns: tuple with 3-elements; best_rule, best_score, cached_matches (if strategys is not FIRST_MATCH)
        """

        best_score = 0
        best_rule = None
        weight_calculation = False
        cache_matches = [] if strategy in (RuleBase.BEST_MATCHES, RuleBase.ALL_MATCHES) else None

        # interact through all rules on possible namespaces
        # namespace can be str (convert to tuple); any Iterable (tuple/list); None, return all namespaces 
        search_space = [namespace] if namespace and isinstance(namespace, Iterable) \
                            else namespace if namespace  \
                            else self.keys()

        for ns in search_space:
            # failsafe in case the namespace is not populated
            if not ns in self: 
                continue
            
            # process every rule within namespace
            for rule in self[ns]:
                if score_l := rule.match(test):
                    if strategy is RuleBase.FIRST_MATCH:
                        best_score = score_l
                        best_rule = rule
                        break
                    elif score_l > best_score:
                        best_score = score_l
                        best_rule = rule
                        if strategy is RuleBase.BEST_MATCHES:
                            cache_matches.clear()
                        cache_matches.append(rule)
                        if rule.__weight__ != 1.0:
                            weight_calculation = True
                    elif score_l == best_score:
                        cache_matches.append(rule)
                        if rule.__weight__ != 1.0:
                            weight_calculation = True


            # if a rule has been found and cut_short, dont go through other namespaces
            if best_rule and strategy is RuleBase.FIRST_MATCH:
                break

        #
        # Explanation:
        # If multiple rules share the best score, they are considered in ``cache_matches``
        # The selection is performed using random.choices, which selects one rule based on weight probability.
        # If the weights are all 1.0, simplify the selection based on flat distribution.
        # Otherwise, the weight of each rule is calculated relative to the total weight of all competing rules.
        # https://chatgpt.com/share/67c90d85-2700-8002-9acc-fc7c1e93954c
        #
        if cache_matches:
            if len(cache_matches) == 1:
                best_rule = cache_matches[0]
            elif weight_calculation:
                total_weight = sum(rule.__weight__ for rule in cache_matches)
                choices = [(rule, rule.__weight__ / total_weight) for rule in cache_matches]
                best_rule = random.choices(
                        [rule for rule, _ in choices],
                        weights=[weight for _, weight in choices],k=1)[0]
            else:
                best_rule = random.choices(cache_matches)
        return best_rule, best_score, cache_matches