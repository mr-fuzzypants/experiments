
"""
Toy Lexer/Parser with a simple grammar compactly describes a node tree.

@Author: Robert Pringle
@license: MIT

Grammar is roughly:
    identifier :=         <sequence of alphanumeric chars>
    type :=               '{' + identifier + '}'
    repeat_item : =       '|' + identifier
    repeat_block :=       '[' + identifier + ']'
                        | '[' + identifier + repeat_item + ']'
    node_expression :=    identifier
                        | repeat_block
                        | type + identifier
                        | type + repeat_block
    node :=               '.' + node_expression
    nodes :=              node | nodes + node


Parser Input: '/{folder}[local|cloud]/{user}rpringle/{stage}[home|work]/{file}contacts'
Parser Output:
    local (folder) /local
         rpringle (user) /local/rpringle
             home (stage) /local/rpringle/home
                 contacts (file) /local/rpringle/home/contacts
             work (stage) /local/rpringle/work
                 contacts (file) /local/rpringle/work/contacts
     cloud (folder) /cloud
         rpringle (user) /cloud/rpringle
             home (stage) /cloud/rpringle/home
                 contacts (file) /cloud/rpringle/home/contacts
             work (stage) /cloud/rpringle/work
                 contacts (file) /cloud/rpringle/work/contacts

"""
class ParseNodeInterface(object):
    """
    Developers can inherit/implement this class to use their own node when the parse tree is constructed.
    """

    @property
    def _parsernode_parent(self):
        raise NotImplementedError

    @_parsernode_parent.setter
    def _parsernode_parent(self, node_type):
        raise NotImplementedError

    @staticmethod
    def _parsernode_create(self, code, node_type, path, parent):
        raise NotImplementedError



class ParseNode(ParseNodeInterface):
    def __init__(self,code, node_type, path, parent):
        self.code = code
        self.node_type = node_type
        self.path = path
        self.parent = parent
        self.children = []

        if self.parent:
            self.parent.children.append(self)

    @staticmethod
    def _parsernode_create(code, node_type, path, parent):
        """
        Inherited from ParseNodeInterface.
        :param code: the parsed identifier
        :param node_type: parsed type
        :param path: current path of this node
        :param parent: node parent
        :return:
        """
        return ParseNode(code, node_type, path, parent)


    @property
    def _parsernode_parent(self):
        """
        Inherited from ParseNodeInterface.
        :return: parent of this node.
        """
        return self.parent

    @_parsernode_parent.setter
    def _parsernode_parent(self, parent):
        self.parent = parent


    def dump_tree(self, level=0):
        print("    " * level, self.code, "(%s)" % self.node_type, self.path)
        for node in self.children:
            node.dump_tree(level + 1)


class Tokens:
    TOKEN_IDENTIFIER = 0
    TOKEN_LEVEL = 1
    TOKEN_BEGIN_REPEAT = 2
    TOKEN_END_REPEAT = 3
    TOKEN_REPEAT_OR = 4
    TOKEN_BEGIN_TYPE = 5
    TOKEN_END_TYPE = 6

    TOKEN_END_TOKENS = 20


    def __init__(self, tokens):

        if isinstance(tokens, str):
            self.tokens = self.tokenize(tokens)
        else:
            self.tokens = tokens

        self.token_idx = -1
        self.token_type = None

        self.cur_token = None
        self.cur_type = None
        self.next_token = None
        self.next_type = None

    def classify_token(self, token):

        if not token:
            return Tokens.TOKEN_END_TOKENS

        elif token[0].isalnum() or token[0] == '_':
            return Tokens.TOKEN_IDENTIFIER
        elif token == '/':
            return Tokens.TOKEN_LEVEL
        elif token == '[':
            return Tokens.TOKEN_BEGIN_REPEAT
        elif token == ']':
            return Tokens.TOKEN_END_REPEAT
        elif token == '|':
            return Tokens.TOKEN_REPEAT_OR
        elif token == '{':
            return Tokens.TOKEN_BEGIN_TYPE
        elif token == '}':
            return Tokens.TOKEN_END_TYPE

        raise Exception("Unclassified token", token)

    def remainder(self):
        return self.tokens[self.token_idx:]

    def peek_next(self, num_tokens=1):
        if self.token_idx < len(self.tokens) - num_tokens:
            self.next_token =  self.tokens[self.token_idx + num_tokens]
            self.next_type = self.classify_token(self.next_token)

    def advance_token(self):
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.cur_token = self.tokens[self.token_idx]
            self.cur_type = self.classify_token(self.cur_token)

            self.peek_next()

        else:
            self.cur_token = None


    def tokenize(self, path):
        token_list = []
        idx = 0
        length = len(path)

        while idx < length:
            token = ''
            if path[idx].isalnum() or path[idx] == '_':
                while idx < length and (path[idx].isalnum() or path[idx] == '_'):
                    token += path[idx]
                    idx += 1
            else:
                token = path[idx]
                idx += 1
            token_list.append(token)

        return token_list


class ParseError(Exception):
    """General Parse Error
    
        index: current line index at the time of error
        token:  current token being evaluated when the error occurred
        message: (optional) string with additional information
    """

    def __init__(self, message, index, token):
        self.index = index
        self.token = token
        self.message = message
        super(ParseError, self).__init__(self.message)

    def __str__(self):

        return f'Parse Error: {self.message} [idx={self.index}] got {self.token}'


class Parser:

    def __init__(self, parser_node_cls=ParseNode):
        self.parser_node_cls = parser_node_cls


    def build_tree(self, tokens, node_type='Folder', subpath='', parent = None):
        node_list = []

        cur_node_type = node_type
        cur_node = parent
        current_subpath = subpath

        tokens.advance_token()

        while tokens.cur_token:

            if tokens.cur_type == Tokens.TOKEN_LEVEL:
                if not (tokens.next_type == Tokens.TOKEN_IDENTIFIER
                        or tokens.next_type == Tokens.TOKEN_BEGIN_REPEAT
                        or tokens.next_type == Tokens.TOKEN_BEGIN_TYPE):
                    raise ParseError("", tokens.token_idx, tokens.cur_token)

                tokens.advance_token()


            if tokens.cur_type == Tokens.TOKEN_IDENTIFIER:
                current_subpath += '/'+ tokens.cur_token
                node = self.parser_node_cls._parsernode_create(code=tokens.cur_token, node_type=cur_node_type,
                                                                path=current_subpath, parent=cur_node)

                node_list.append(node)
                cur_node = node

            elif tokens.cur_type == Tokens.TOKEN_BEGIN_REPEAT:
                    repeat_nodes = []

                    while tokens.cur_type != Tokens.TOKEN_END_REPEAT:
                        tokens.advance_token()

                        if tokens.cur_type != Tokens.TOKEN_IDENTIFIER:
                            raise ParseError("Expected identifier", tokens.token_idx, tokens.cur_token)

                        node = self.parser_node_cls._parsernode_create(code=tokens.cur_token, node_type=cur_node_type,
                                                                        path=current_subpath + "/" + tokens.cur_token ,
                                                                        parent=cur_node)

                        repeat_nodes.append(node)

                        tokens.advance_token()

                        if tokens.cur_type != Tokens.TOKEN_REPEAT_OR:
                            if tokens.cur_type != Tokens.TOKEN_END_REPEAT:
                                raise ParseError("Expected ']' in repeat block.", tokens.token_idx, tokens.cur_token)

                    tokens.advance_token()

                    sub_nodes = node_list
                    for n in repeat_nodes:
                        sub_nodes.append(n)
                        sub_nodes +=  self.build_tree(Tokens(tokens.remainder()), node_type=cur_node_type,
                                                      subpath=current_subpath+'/'+n.code, parent=n)

                    return sub_nodes

            elif tokens.cur_type == Tokens.TOKEN_BEGIN_TYPE:

                tokens.advance_token()
                if tokens.cur_type != Tokens.TOKEN_IDENTIFIER:
                    raise ParseError("Expected type identifier.",tokens.token_idx, tokens.cur_token)

                # now have the identifier. set the type
                cur_node_type = tokens.cur_token

                tokens.advance_token()
                if tokens.cur_type != Tokens.TOKEN_END_TYPE:
                    raise ParseError("Expected type end of type.", tokens.token_idx, tokens.cur_token)

            else:
                raise ParseError("Unrecognized token", tokens.token_idx, tokens.cur_token)

            tokens.advance_token()

        return node_list


    def parse(self, tstring):
        tokens = Tokens(tstring)
        parse_root = ParseNode(code='root', node_type='root', path='', parent=None)
        nodes = self.build_tree(tokens, parent=parse_root)


        return [parse_root] + nodes

# a . can be followed by an identifier or a modifier
# an identifier can be followed only by a ,
#

if __name__ == "__main__":

    ts1 = '/{folder}[local|cloud]/{user}rpringle/{stage}[home|work]/{file}contacts'

    parser = Parser()
    parse_nodes = parser.parse(ts1)
    parse_nodes[0].dump_tree()

