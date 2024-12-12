"""
Regex Parsing Script Meant to highlight recently learned NFA and Regex topics in 2800 made by Robbie Shekhtman
"""


def precedence(operator):
    # Returns the precedence level(1 through 3...should not return 0 but it is default) of a given operator.
    if operator in {'*', '+', '?'}:
        return 3
    if operator == '&':
        return 2
    if operator == '|':
        return 1
    return 0

def is_literal(c):
    # Returns true if 'c' is a literal, False otherwise
    return c is not None and c not in {'(', ')', '|', '*', '+', '?', '.'}

def insert_concat_operators(pattern):
    # Inserts a concatenation operator '&' between elements and returns the concatenated string
    tokens = []
    prev = None 

    for c in pattern:
        if prev is not None:
            # Determine if prev can be followed directly by another token
            prevCanConcat = (is_literal(prev) or prev in {')', '*', '+', '?', '.'})

            # Determine if curr starts a new token.
            startsToken = (is_literal(c) or c == '(' or c == '.')

            if prevCanConcat and startsToken:
                tokens.append('&')

        tokens.append(c)

        prev = c

    return ''.join(tokens)

def infix_to_postfix(pattern):
    # Converts from infix to postfix notation
    
    pattern = insert_concat_operators(pattern) 
    output = []  
    stack = []   
    i = 0

    while i < len(pattern):
        c = pattern[i]

        if c == '(':
            stack.append(c)

        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise Exception("Mismatched parentheses")
            stack.pop()

        elif c == '&':
            # pop while higher or == precedencee
            while stack and stack[-1] != '(' and precedence(stack[-1]) >= 2:
                output.append(stack.pop())
            stack.append(c)

        elif c == '|':
            # pop while higher or == precedence
            while stack and stack[-1] != '(' and precedence(stack[-1]) >= 1:
                output.append(stack.pop())
            stack.append(c)

        elif c in {'*', '+', '?'}:
            #pop while top of stack has greater precedence.
            while stack and stack[-1] != '(' and precedence(stack[-1]) > precedence(c):
                output.append(stack.pop())
            stack.append(c)
        else:
            # Otherwise c is literal or .
            if c == '.':
                output.append(('DOT',))
            else:
                output.append(('CHAR', c))
        i += 1

    while stack:
        top = stack.pop()
        if top in {'(', ')'}:
            raise Exception("Mismatched parentheses")
        output.append(top)

    return output


#NFA Handling begins here:
class State:
    def __init__(self):
        # Each state object in the NFA has a list of edges
        self.edges = []

class Fragment:
    def __init__(self, start, accepts):
        # A fragment object represents a incomplete NFA wiht a start state and list of accepting states
        self.start = start
        self.accepts = accepts

def thompson_construct(postfix):
    # Construct an NFA using Thompson's construction learned in 2800
    stack = []

    for token in postfix:
        if token == '&':
            #pop two fragments and connect the first's accept states
            if len(stack) < 2:
                raise Exception("Invalid regex: need 2 fragments")
            
            frag2 = stack.pop()
            frag1 = stack.pop()

            for a in frag1.accepts:
                a.edges.append((None, frag2.start))

            stack.append(Fragment(frag1.start, frag2.accepts))

        elif token == '|':
            # pop two fragments and make a new start and accept state
            if len(stack) < 2:
                raise Exception("Invalid regex: need 2 fragments")
            
            frag2 = stack.pop()
            frag1 = stack.pop()

            s = State()
            a = State()

            s.edges.append((None, frag1.start))
            s.edges.append((None, frag2.start))

            for acc in frag1.accepts:
                acc.edges.append((None, a))

            for acc in frag2.accepts:
                acc.edges.append((None, a))

            stack.append(Fragment(s, [a]))

        elif token == '*':
            # pop one fragment and create new start and accept states
            if not stack:
                raise Exception("applied to empty stack")
            
            frag = stack.pop()
            s = State()
            a = State()

            s.edges.append((None, frag.start))
            s.edges.append((None, a))

            for acc in frag.accepts:
                acc.edges.append((None, frag.start))
                acc.edges.append((None, a))

            stack.append(Fragment(s, [a]))

        elif token == '+':
            # like kleenes star but you must go through the fragment at least once.
            if not stack:
                raise Exception("applied to empty stack")
            
            frag = stack.pop()
            s = State()
            a = State()

            s.edges.append((None, frag.start))

            for acc in frag.accepts:
                acc.edges.append((None, frag.start))
                acc.edges.append((None, a))

            stack.append(Fragment(s, [a]))

        elif token == '?':
            # pop one fragment but allow skipping it.
            if not stack:
                raise Exception("applied to empty stack")
            
            frag = stack.pop()
            s = State()
            a = State()

            s.edges.append((None, frag.start))
            s.edges.append((None, a))

            for acc in frag.accepts:
                acc.edges.append((None, a))

            stack.append(Fragment(s, [a]))

        else:
            # its either char or .
            s = State()
            a = State()

            s.edges.append((token, a))
            stack.append(Fragment(s, [a]))

    if len(stack) != 1:
        # there should be exactly one fragment in the stack
        raise Exception("Leftover fragments")
    
    return stack.pop()

def add_empty_closure(states, s, visited):
    # Compute all states reachable from 's' by only empty transitions.
    if s in visited:
        return
    
    visited.add(s)
    states.add(s)

    for (ch, nxt) in s.edges:
        if ch is None:
            add_empty_closure(states, nxt, visited)

def step(states, c):
    # finds all states reachable by consuming 'c'
    new_states = set()

    for s in states:
        for (ch, nxt) in s.edges:
            if ch is not None:
                if ch[0] == 'CHAR' and ch[1] == c:
                    new_states.add(nxt)

                elif ch[0] == 'DOT':
                    new_states.add(nxt)

    closure = set()
    visited = set()

    for s in new_states:
        add_empty_closure(closure, s, visited)

    return closure

def nfa_match(fragment, text):
    #Determine if the entire text is matched by the NFA

    currentStates = set()
    visited = set()

    add_empty_closure(currentStates, fragment.start, visited)

    for c in text:
        # Consume each character and update current states
        currentStates = step(currentStates, c)
        
        if not currentStates:
            return False

    #  make sure any of states accepts
    return any(s in fragment.accepts for s in currentStates)

def full_match(regex, text):
    # Convert to postfix
    postfix = infix_to_postfix(regex)
    # build NFA
    frag = thompson_construct(postfix)
    # compare text to NFA
    return nfa_match(frag, text)


# Tests---should provide coverage for supported operations but certainly does not cover all regex expressions
if __name__ == "__main__":
    # Literal
    assert full_match("abc", "abc") == True
    assert full_match("abc", "ab") == False

    # .
    assert full_match("a.c", "abc") == True
    assert full_match("a.c", "acc") == True
    assert full_match("a.c", "ac") == False

    # *
    assert full_match("a*", "") == True
    assert full_match("a*", "aaaa") == True
    assert full_match("a*", "b") == False

    # +
    assert full_match("a+", "") == False
    assert full_match("a+", "a") == True
    assert full_match("a+", "aaa") == True
    assert full_match("a+", "b") == False

    # ?
    assert full_match("a?", "") == True
    assert full_match("a?", "a") == True
    assert full_match("a?", "aa") == False

    # |
    assert full_match("a|b", "a") == True
    assert full_match("a|b", "b") == True
    assert full_match("a|b", "c") == False

    # () and |
    assert full_match("(ab|cd)e", "abe") == True
    assert full_match("(ab|cd)e", "cde") == True
    assert full_match("(ab|cd)e", "ace") == False

    # More complex patterns
    # 1) Must contain 'ab'
    pattern = "(a|b)*ab(a|b)*"
    assert full_match(pattern, "ab") == True
    assert full_match(pattern, "aabbbb") == True
    assert full_match(pattern, "bbbbbb") == False
    assert full_match(pattern, "babab") == True

    # 2) Zero or more occurrences of one or more a|b followed by c
    pattern = "((a|b)+c)*"
    assert full_match(pattern, "") == True   
    assert full_match(pattern, "abc") == True  
    assert full_match(pattern, "aabc") == True 
    assert full_match(pattern, "abcabc") == True 
    assert full_match(pattern, "abcaab") == False #need the c at the end

    # 3) One or more occurrences of (ab|cd), followed by e, optional f, then g
    pattern = "(ab|cd)+ef?g"
    assert full_match(pattern, "abeg") == True   
    assert full_match(pattern, "abefg") == True  
    assert full_match(pattern, "cdegg") == False 
    assert full_match(pattern, "ababeg") == True 
    assert full_match(pattern, "cdcdcdefg") == True 

    # 4) Ensure at least two 'a's in the string
    pattern = "(a|b)*a(a|b)*a(a|b)*"
    assert full_match(pattern, "aa") == True   
    assert full_match(pattern, "aba") == True
    assert full_match(pattern, "bbb") == False 
    assert full_match(pattern, "bab") == False 
    assert full_match(pattern, "baabbb") == True 

    # 5) Ensures at least one segment that has two 'a's and we can repeat that segment one or more times
    pattern = "((a|b)*a(a|b)*a(a|b)*)+"
    assert full_match(pattern, "aa") == True
    assert full_match(pattern, "aabaa") == True 
    assert full_match(pattern, "bbbb") == False 
    assert full_match(pattern, "babababbbaa") == True 

    # 6) We have at least one character from (a|b)*, then any char, then more (a|b)*.
    pattern = "(a|b)*.(a|b)*"
    assert full_match(pattern, "a") == True  
    assert full_match(pattern, "ab") == True  
    assert full_match(pattern, "ba") == True  
    assert full_match(pattern, "aaa") == True 
    assert full_match(pattern, "bbbzzz") == False 


    print("All tests passed.")
