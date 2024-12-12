This project demonstrates how to parse and compare regular expressions using NFAs and Thompson’s construction. It takes a regex pattern, converts it into postfix notation, builds an NFA, and then simulates that NFA to determine if a given text matches the pattern. 

Supported regex operations: * (Kleene's star), + (one or more), ? (zero or one), | (alternation), . (single char matching), and () (grouping)

The bottom of the script contains a various tests to asses the functionality of each operation as well as 6 more complex regex expressions to ensure full coverage and completeness.
