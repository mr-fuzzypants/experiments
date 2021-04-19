# experiments

This is just some playing around. "parser" is just a some fun implementing *very* basic lexing/parsing and some simple grammar rules. The fact that the grammar
is so simple, obviates the need for something like yacc/lex but clearly there are limits


Grammar is roughly:

identifier := <alphanumeric sequence>

type := '{' + identifier + '}'

repeat_item : =   '|' + identifier
repeat_block :=   '[' + identifier + ']' 
                | '[' + identifier + repeat_item + ']' 

node_expression :=  identifier 
                  | repeat_block
                  | type + identifier
                  | type + repeat_block
                  
node := '.' + node_expression 

nodes :=   node 
         | nodes + node 


Valid input examples:
.usr
.{directory}usr
.usr.[tmp|temp|scratch].rpringle.{file}settings
.usr.tmp.{file}[test|scratch]

The following string:
    .usr.[tmp|temp|scratch].rpringle.{file}settings
Expands to:
    /usr
        /tmp
            /rpringle
                settings
        /temp
            /rpringle
                settings
        /scratch
            /rpringle
                settings

            

