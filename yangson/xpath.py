from typing import Any, Callable, List, Optional, Tuple, Union
from .constants import Axis, MultiplicativeOp
from .context import Context
from .instance import InstanceNode
from .parser import Parser, ParserException, EndOfInput, UnexpectedInput
from .typealiases import *

# Type aliases

NodeExpr = Callable[[InstanceNode], List[InstanceNode]]
XPathExpr = Callable[[InstanceNode, InstanceNode], bool]
XPathValue = Union["NodeSet", str, float, bool]

def comparison(meth):
    def wrap(self, arg):
        if isinstance(arg, NodeSet):
            for n in arg:
                if meth(self, str(n.value)): return True
            return False
        return meth(self, arg)
    return wrap

class NodeSet(list):

    def union(self, ns: "NodeSet") -> "NodeSet":
        elems = {n.path():n for n in self}
        elems.update({n.path():n for n in ns})
        return self.__class__(elems.values())

    def sort(self, reverse: bool = False):
        super().sort(key=InstanceNode.path, reverse=reverse)

    def bind(self, trans: NodeExpr) -> "NodeSet":
        res = self.__class__([])
        for n in self:
            res = res.union(NodeSet(trans(n)))
        return res

    def as_float(self) -> float:
        return float(self[0].value)

    def __str__(self) -> str:
        return str(self[0].value) if self else ""

    @comparison
    def __eq__(self, val) -> bool:
        for n in self:
            if (str(n.value) if isinstance(val, str) else n.value) == val:
                return True
        return False

    @comparison
    def __ne__(self, val) -> bool:
        for n in self:
            if (str(n.value) if isinstance(val, str) else n.value) != val:
                return True
        return False

    @comparison
    def __gt__(self, val) -> bool:
        try:
            val = float(val)
        except (ValueError, TypeError):
            return False
        for n in self:
            try:
                if float(n.value) > val:
                    return True
            except (ValueError, TypeError):
                continue
        return False

    @comparison
    def __lt__(self, val) -> bool:
        try:
            val = float(val)
        except (ValueError, TypeError):
            return False
        for n in self:
            try:
                if float(n.value) < val:
                    return True
            except (ValueError, TypeError):
                continue
        return False

    @comparison
    def __ge__(self, val) -> bool:
        try:
            val = float(val)
        except (ValueError, TypeError):
            return False
        for n in self:
            try:
                if float(n.value) >= val:
                    return True
            except (ValueError, TypeError):
                continue
        return False

    @comparison
    def __le__(self, val) -> bool:
        try:
            val = float(val)
        except (ValueError, TypeError):
            return False
        for n in self:
            try:
                if float(n.value) <= val:
                    return True
            except (ValueError, TypeError):
                continue
        return False

class Expr:
    """Abstract class for XPath expressions."""

    indent = 2

    def __str__(self):
        return self._tree()

    def evaluate(self, node: InstanceNode):
        return self._eval(node, node)

    @staticmethod
    def _as_float(val) -> float:
        return val.as_float() if isinstance(val, NodeSet) else float(val)

    def _tree(self, indent: int = 0):
        node_name = self.__class__.__name__
        attr = self._properties()
        attr_str  = " (" + attr + ")\n" if attr else "\n"
        return (" " * indent + node_name + attr_str +
                self._children(indent + self.indent))

    def _properties(self):
        return ""

    def _children(self, indent):
        return ""

    def _predicates_str(self, indent):
        if not self.predicates: return ""
        res = " " * indent + "-- Predicates:\n"
        newi = indent + 3
        for p in self.predicates:
            res += p._tree(newi)
        return res

    def _apply_predicates(self, ns: XPathValue, origin: InstanceNode) -> XPathValue:
        for p in self.predicates:
            res = NodeSet([])
            for n in ns:
                pval = p._eval(n, origin)
                try:
                    if isinstance(pval, float):
                        i = int(pval) - 1
                        res.append(ns[i])
                        break
                except IndexError:
                    return res
                if pval:
                    res.append(n)
            ns = res
        return ns

class DyadicExpr(Expr):
    """Abstract superclass of dyadic expressions."""

    def __init__(self, left: "Expr", right: "Expr") -> None:
        self.left = left
        self.right = right

    def _children(self, indent: int):
        return self.left._tree(indent) + self.right._tree(indent)

    def _eval_ops(self, node: InstanceNode,
                  origin: InstanceNode) -> Tuple[XPathValue, XPathValue]:
        return (self.left._eval(node, origin),
                self.right._eval(node, origin))

class OrExpr(DyadicExpr):

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        return lres or rres

class AndExpr(DyadicExpr):

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        return lres and rres

class EqualityExpr(DyadicExpr):

    def __init__(self, left: Expr, right: Expr, negate: bool) -> None:
        super().__init__(left, right)
        self.negate = negate

    def _properties(self):
        return "!=" if self.negate else "="

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        return lres != rres if self.negate else lres == rres

class RelationalExpr(DyadicExpr):

    def __init__(self, left: Expr, right: Expr, less: bool,
                 equal: bool) -> None:
        super().__init__(left, right)
        self.less = less
        self.equal = equal

    def _properties(self):
        res = "<" if self.less else ">"
        if self.equal: res += "="
        return res

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        if self.less:
            return lres <= rres if self.equal else lres < rres
        return lres >= rres if self.equal else lres > rres

class AdditiveExpr(DyadicExpr):

    def __init__(self, left: Expr, right: Expr, plus: bool) -> None:
        super().__init__(left, right)
        self.plus = plus

    def _properties(self):
        return "+" if self.plus else "-"

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        return (self._as_float(lres) + self._as_float(rres) if self.plus
                else self._as_float(lres) - self._as_float(rres))

class MultiplicativeExpr(DyadicExpr):

    def __init__(self, left: Expr, right: Expr,
                 operator: MultiplicativeOp) -> None:
        super().__init__(left, right)
        self.operator = operator

    def _properties(self):
        if self.operator == Axis.multiply: return "*"
        if self.operator == Axis.divide: return "/"
        if self.operator == Axis.modulo: return "mod"

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        if self.operator == Axis.multiply:
            return self._as_float(lres) * self._as_float(rres)
        if self.operator == Axis.divide:
            return self._as_float(lres) / self._as_float(rres)
        return self._as_float(lres) % self._as_float(rres)

class UnaryExpr(Expr):

    def __init__(self, expr: Expr, negate: bool):
        self.expr = expr
        self.negate = negate

    def _properties(self):
        return "-" if self.negate else "+"

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        res = self._as_float(self.expr._eval(node, origin))
        return -res if self.negate else res

class UnionExpr(DyadicExpr):

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres, rres = self._eval_ops(node, origin)
        return lres.union(rres)

class Literal(Expr):

    def __init__(self, value: str) -> None:
        self.value = value

    def _properties(self):
        return self.value

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        return self.value

class Number(Expr):

    def __init__(self, value: float) -> None:
        self.value = value

    def _properties(self):
        return str(self.value)

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        return self.value

class PathExpr(Expr):

    def __init__(self, filter: Expr, path: Expr) -> None:
        self.filter = filter
        self.path = path

    def _children(self, indent: int):
        return self.filter._tree(indent) + self.path._tree(indent)

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        res = self.filter._eval(node, origin)
        return self.path._eval(res, origin)

class FilterExpr(Expr):

    def __init__(self, primary: Expr, predicates: List[Expr]) -> None:
        self.primary = primary
        self.predicates = predicates

    def _children(self, indent):
        return self.primary._tree(indent) + self._predicates_str(indent)

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        res = self.primary._eval(node, origin)
        return self._apply_predicates(res, origin)

class LocationPath(DyadicExpr):

    def __init__(self, left: Expr, right: Expr, absolute: bool = False) -> None:
        super().__init__(left, right)
        self.absolute = absolute

    def _properties(self):
        return "ABS" if self.absolute else "REL"

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        lres = self.left._eval(node.top() if self.absolute else node, origin)
        ns = lres.bind(self.right._node_trans())
        for p in self.right.predicates:
            ns = [n for n in ns if p.eval(n, origin)]
        return NodeSet(ns)

class Step(Expr):

    def __init__(self, axis: Axis, qname: QualName,
                 predicates: List[Expr]) -> None:
        self.axis = axis
        self.qname = qname
        self.predicates = predicates

    def _properties(self):
        return "{} {}".format(self.axis.name, self.qname)

    def _children(self, indent):
        return self._predicates_str(indent)

    def _node_trans(self) -> NodeExpr:
        if self.axis == Axis.child:
            return lambda n: n.children(self.qname)
        if self.axis == Axis.ancestor_or_self:
            return lambda n: n.ancestors_or_self(self.qname)
        if self.axis == Axis.descendant:
            return lambda n: n.descendants(self.qname)

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        ns = NodeSet(self._node_trans()(node))
        return self._apply_predicates(ns, origin)

class FuncTrue(Expr):

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        return True

class FuncFalse(Expr):

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        return False

class FuncLast(Expr):

    def _eval(self, node: InstanceNode, origin: InstanceNode):
        return 0.0

class XPathParser(Parser):
    """Parser for XPath expressions."""

    def __init__(self, text: str, mid: ModuleId) -> None:
        """Initialize the parser instance.

        :param mid: id of the context module
        """
        super().__init__(text)
        self.mid = mid

    def parse(self) -> Expr:
        """Parse an XPath 1.0 expression."""
        self.skip_ws()
        return self._or_expr()

    def _or_expr(self) -> Expr:
        op1 = self._and_expr()
        while self.test_string("or"):
            self.skip_ws()
            op2 = self._and_expr()
            op1 = OrExpr(op1, op2)
        return op1

    def _and_expr(self) -> Expr:
        op1 = self._equality_expr()
        while self.test_string("and"):
            self.skip_ws()
            op2 = self._equality_expr()
            op1 = AndExpr(op1, op2)
        return op1

    def _equality_expr(self) -> Expr:
        op1 = self._relational_expr()
        while True:
            negate = False
            try:
                next = self.peek()
            except EndOfInput:
                return op1
            if next == "!":
                self.offset += 1
                negate = True
                try:
                    next = self.peek()
                except EndOfInput:
                    raise InvalidXPath(self)
            if next != "=":
                if negate:
                    raise InvalidXPath(self)
                return op1
            self.adv_skip_ws()
            op2 = self._relational_expr()
            op1 = EqualityExpr(op1, op2, negate)

    def _relational_expr(self) -> Expr:
        op1 = self._additive_expr()
        while True:
            try:
                rel = self.peek()
            except EndOfInput:
                return op1
            if rel not in "<>": return op1
            self.offset += 1
            eq = self.test_string("=")
            self.skip_ws()
            op2 = self._additive_expr()
            op1 = RelationalExpr(op1, op2, rel == "<", eq)

    def _additive_expr(self) -> Expr:
        op1 = self._multiplicative_expr()
        while True:
            try:
                pm = self.peek()
            except EndOfInput:
                return op1
            if pm not in "+-": return op1
            self.adv_skip_ws()
            op2 = self._multiplicative_expr()
            op1 = AdditiveExpr(op1, op2, pm == "+")

    def _multiplicative_expr(self) -> Expr:
        op1 = self._unary_expr()
        while True:
            if self.test_string("*"):
                mulop = MultiplicativeOp.multiply
            elif self.test_string("div"):
                mulop = MultiplicativeOp.divide
            elif self.test_string("mod"):
                mulop = MultiplicativeOp.modulo
            else:
                return op1
            self.skip_ws()
            op2 = self._unary_expr()
            op1 = MultiplicativeExpr(op1, op2, mulop)

    def _unary_expr(self) -> Expr:
        negate = None
        while self.test_string("-"):
            negate = not negate
            self.skip_ws()
        expr = self._union_expr()
        return expr if negate is None else UnaryExpr(expr, negate)

    def _union_expr(self) -> Expr:
        op1 = self._lit_num_path()
        while self.test_string("|"):
            self.skip_ws()
            op2 = self._lit_num_path()
            op1 = UnionExpr(op1, op2)
        return op1

    def _lit_num_path(self) -> Expr:
        next = self.peek()
        if next == "(":
            self.adv_skip_ws()
            return self._path_expr(None)
        if next in "'\"":
            self.offset += 1
            val = self.up_to(next)
            self.skip_ws()
            return Literal(val)
        if ("0" <= next <= "9" or
            next == "." and "0" <= self.input[self.offset + 1] <= 9):
            val = self.float()
            self.skip_ws()
            return Number(val)
        start = self.offset
        try:
            fname = self.yang_identifier()
        except UnexpectedInput:
            return self._location_path()
        self.skip_ws()
        if self.test_string("("):
            self.skip_ws()
            return self._path_expr(fname)
        self.offset = start
        return self._relative_location_path()

    def _path_expr(self, fname: str) -> Expr:
        fexpr = self._filter_expr(fname)
        if self.test_string("/"):
            return PathExpr(fexpr, self._relative_location_path())
        return fexpr

    def _filter_expr(self, fname: str) -> Expr:
        if fname is None:
            prim = self._or_expr()
        else:
            prim = self._function_call(fname)
        self.char(")")
        self.skip_ws()
        return FilterExpr(prim, self._predicates())

    def _predicates(self) -> List[Expr]:
        res = []
        while self.test_string("["):
            res.append(self.parse())
            self.char("]")
            self.skip_ws()
        return res

    def _location_path(self) -> LocationPath:
        if self.test_string("/"):
            path = self._relative_location_path()
            path.absolute = True
            return path
        return self._relative_location_path()

    def _relative_location_path(self) -> LocationPath:
        op1 = self._step()
        while self.test_string("/"):
            self.skip_ws()
            op2 = self._step()
            op1 = LocationPath(op1, op2)
        return op1

    def _step(self) -> Step:
        return Step(*self._axis_qname(), self._predicates())

    def _axis_qname(self) -> Tuple[Axis, Optional[QualName]]:
        next = self.peek()
        if next == "*":
            self.adv_skip_ws()
            return (Axis.child, None)
        if next == "/":
            self.adv_skip_ws()
            return (Axis.descendant_or_self, None)
        if next == ".":
            self.offset += 1
            res = (Axis.parent if self.test_string(".") else Axis.self, None)
            self.skip_ws()
            return res
        try:
            yid = self.yang_identifier()
        except UnexpectedInput:
            raise InvalidXPath(self) from None
        ws = self.skip_ws()
        try:
            next = self.peek()
        except EndOfInput:
            return (Axis.child, (yid, self.mid[0]))
        if next == ":":
            self.offset += 1
            next = self.peek()
            if next == ":":
                self.adv_skip_ws()
                return (Axis[yid.replace("-", "_")], self._qname())
            if ws:
                raise InvalidXPath(self)
            nsp = Context.prefix2ns(yid, self.mid)
            loc = self.yang_identifier()
            self.skip_ws()
            return (Axis.child, (loc, nsp))
        return (Axis.child, (yid, self.mid[0]))

    def _qname(self) -> Optional[QualName]:
        """Parse XML QName."""
        if self.test_string("*"):
            self.skip_ws()
            return None
        ident = self.yang_identifier()
        res = ((self.yang_identifier(), Context.prefix2ns(ident, self.mid))
               if self.test_string(":") else (ident, self.mid[0]))
        self.skip_ws()
        return res

    def _function_call(self, name: str):
        if name == "true":
            res = FuncTrue()
        elif name == "false":
            res = FuncFalse()
        elif name == "last":
            res = FuncLast()
        return res

class InvalidXPath(ParserException):
    """Exception to be raised for an invalid XPath expression."""

    def __init__(self, p: XPathParser, rule: str) -> None:
        super().__init__(p)
        self.rule = rule

    def __str__(self) -> str:
        return str(self.parser)
