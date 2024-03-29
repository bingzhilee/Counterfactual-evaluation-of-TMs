#contient les classes Node, Arc et DependencyTree
# (j'avais besoin que ce fichier soit au même niveau que Camille.py)

class Node(object):

    def __init__(self, index=None, word="", lemma="", head_id=None, pos="", dep_label="", morph="_",
                 size=None, dep_label_new=None):
        """
        :param index: int
        :param word: str
        :param head_id: int
        :param pos: str
        :param dep_label: str
        """
        self.index = index
        self.word = word
        self.lemma = lemma
        self.head_id = head_id
        self.pos = pos
        self.dep_label = dep_label
        self.morph = morph
        if dep_label_new is None:
            self.dep_label_new = dep_label
        else:
            self.dep_label_new = dep_label_new
        # to assign after tree creation
        self.size = size
        self.dir = None

    def __str__(self):
        return "\t".join([str(self.index), self.word, self.pos, self.morph, str(self.head_id), str(self.dep_label)])

    def __repr__(self):
        return "\t".join([str(v) for (a, v) in self.__dict__.items() if v])

    @classmethod
    def from_str(cls, string):
        index, word, pos, head_id, dep_label = [None if x == "None" else x for x in string.split("\t")]
        return Node(index, word, head_id, pos, dep_label)

    def __eq__(self, other):
        return other is not None and \
               self.index == other.index and \
               self.word == other.word and \
               self.head_id == other.head_id and \
               self.pos == other.pos and \
               self.dep_label == other.dep_label

    def __hash__(self):
        return hash(tuple(self.__dict__.values()))

    def is_root(self):
        generic_root = DependencyTree.generic_root(conll_utils.UD_CONLL_CONFIG)
        if self.word == generic_root.word and self.pos == generic_root.pos:
            return True
        return False


class Arc(object):
    LEFT = "L"
    RIGHT = "R"

    def __init__(self, head, direction, child):
        self.head = head
        self.dir = direction
        self.child = child
        self.dep_label = child.dep_label

    def __str__(self):
        return str(self.head) + " " + self.dir + " " + str(self.child)

    def __repr__(self):
        return str(self)

    @classmethod
    def from_str(cls, string):
        head_str, dir, child_str = string.split(" ")
        return Arc(Node.from_str(head_str), dir, Node.from_str(child_str))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __hash__(self):
        return hash(tuple(self.__dict__.values()))

    def length(self):
        # arcs to ROOT node have length 0
        if self.head.is_root():
            return 0
        else:
            return abs(self.child.index - self.head.index)


class DependencyTree(object):
    def __init__(self, nodes, arcs):
        self.nodes = nodes
        self.arcs = arcs

    def __str__(self):
        return "\n".join([str(n) for n in self.nodes])
        # word  Pos   morph head_index dep_label

    def __repr__(self):
        return str(self)

    def children(self, head):
        children = []
        for arc in self.arcs:
            if arc.head == head:
                children.append(arc.child)
        return children

    def subtree(self, head):
        """
        ex: The thing to keep in mind is that...
        subtree(is) --> nodes of the whole tree [node1,node2...]
        subtree(thing) --> [the, thing, to, keep, in, mind]
        subtree(keep) --> nodes of the context [to, keep in mind]

        """
        elements = set()
        queue = Queue()
        queue.put(head)
        #head_ = Node(head.index, head.word, head.pos + "X")
        elements.add(head)
        visited = set()
        while not queue.empty():
            next_node = queue.get()#Remove and return an item from the queue. If queue is empty, wait until an item is available
            if next_node in visited:
                continue
            visited.add(next_node)
            for child in self.children(next_node):
                elements.add(child)
                queue.put(child)

        return sorted(elements, key=lambda element: int(element.index))

    def is_projective_arc(self, arc):
        st = self.subtree(arc.head)
        # all nodes in subtree of the arc head
        st_idx = [node.index for node in st]
        # span between the child and the head
        indexes = range(arc.child.index + 1, arc.head.index) if arc.child.index < arc.head.index else range(
            arc.head.index + 1, arc.child.index)
        # each node/word between child and head should be part of the subtree
        # if not, than the child-head arc is crossed by some other arc and is non-projective
        for i in indexes:
            if i not in st_idx:
                return False
        return True

    def is_projective(self):
        return all(self.is_projective_arc(arc) for arc in self.arcs)

    def length(self):
        return sum(arc.length() for arc in self.arcs)

    def average_branching_factor(self):
        heads = [node.head_id for node in self.nodes]
        return len(self.nodes)/len(set(heads))

    def root(self):
        return DependencyTree.generic_root()

    @classmethod
    def generic_root(cls):
        return Node(0, "ROOT", "ROOT", 0, "ROOT", size=0)

    @classmethod
    def from_sentence(cls, sentence):
        nodes = []
        for i in range(len(sentence)):
            row = sentence[i]
            morph = row[5]
            lemma = row[2]
            if "-" not in row[0]: 
                nodes.append(
                        Node(int(row[0]),
                            row[1],
                            lemma=lemma,
                            head_id=int(row[6]),
                            pos=row[3],
                            dep_label=row[7],
                            morph=morph))
        arcs = []
        for node in nodes:
            head_index = int(node.head_id)
            head_element = nodes[head_index - 1]
            if head_index == 0:
                arcs.append(Arc(cls.generic_root(), Arc.LEFT, node))
            elif head_index < int(node.index):
                arcs.append(Arc(head_element, Arc.RIGHT, node))
                node.dir = Arc.RIGHT
            else:
                arcs.append(Arc(head_element, Arc.LEFT, node))
                node.dir = Arc.LEFT
        return cls(nodes, arcs)

    def __str__(self):
        """
        Conll string for the dep tree
        """
        lines = []
        for node in self.nodes:
            L = ["_"] * 10
            L[0] = str(node.index)
            if node.word:
              L[1] = node.word
            if node.lemma:
              L[2] = node.lemma
            if node.pos:
              L[3] = node.pos
            if node.morph:
              L[5] = node.morph
            #label, head = revdeps[node] if node in revdeps else ("root", 0)
            L[6] = str(node.head_id)
            if node.dep_label:
              L[7] = node.dep_label
            lines.append("\t".join(L))
        return "\n".join(lines)

""" convert conll to depTrees """

def read_blankline_block(stream):
    s = ''
    list = []
    while True:
        line = stream.readline()
        if not line:# End of file:
            list.append(s)
            return list
        # Blank line: end of a sentence
        elif line and not line.strip():
            list.append(s)
            s = ''
        # Other line:
        elif not line.startswith("#"):
            s += line # concatenate all lines of a sentence to one string

def read_sentences_from_columns(stream):
    # grids are sentences in column format : [sent1,sent2...], sent1: [[conll_line1],[line2]...]
    grids = []
    for block in read_blankline_block(stream):
        # each block is a string that concatenate all conll lines of a sentence
        block = block.strip() # remove the final '\n' character
        #print(block)
        #print()
        if not block: continue

        grid = [line.split('\t') for line in block.split('\n')] # one sentence
        appendFlag = True
        # Check that the grid is consistent.
        for row in grid:
            if len(row) != len(grid[0]):
                #raise ValueError('Inconsistent number of columns:\n%s'% block)
                sys.stderr.write('Inconsistent number of columns', block)
                appendFlag = False
                break
        if appendFlag:
            grids.append(grid)

    return grids

def load_trees_from_conll(file_name):
    # sentences : a list of sents, sent: a list of lines, line : list of columns values : ['1','It','it'...]
    stream = open(file_name, encoding = "utf-8")
    sentences = read_sentences_from_columns(stream)
    trees = []
    for s in sentences:
        trees.append(DependencyTree.from_sentence(s))
    stream.close()
    return trees