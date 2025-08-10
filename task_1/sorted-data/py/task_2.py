class LexicalError(Exception):
    """Виключення для помилок лексичного аналізу."""

    pass


class ParsingError(Exception):
    """Виключення для помилок синтаксичного аналізу."""

    pass


class TokenType:
    """Типи токенів для арифметичних операцій."""

    INTEGER = "INTEGER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    LPAREN = "("
    RPAREN = ")"
    EOF = "EOF"


class Token:
    """Клас токена з типом i значенням."""

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return f"Token({self.type}, {repr(self.value)})"


class Lexer:
    """Лексичний аналізатор, що розбиває рядок на токени."""

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        """Перехід до наступного символу y вхідному тексті."""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        """Пропуск пробілів."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Зчитування цілого числа."""
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Головний метод лексера для побудови токенів."""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(TokenType.INTEGER, self.integer())

            if self.current_char == "+":
                self.advance()
                return Token(TokenType.PLUS, "+")

            if self.current_char == "-":
                self.advance()
                return Token(TokenType.MINUS, "-")

            if self.current_char == "*":
                self.advance()
                return Token(TokenType.MUL, "*")

            if self.current_char == "/":
                self.advance()
                return Token(TokenType.DIV, "/")

            if self.current_char == "(":
                self.advance()
                return Token(TokenType.LPAREN, "(")

            if self.current_char == ")":
                self.advance()
                return Token(TokenType.RPAREN, ")")

            raise LexicalError(f"Невідомий символ: {self.current_char}")

        return Token(TokenType.EOF, None)


class AST:
    """Базовий клас вузлів абстрактного синтаксичного дерева."""

    pass


class BinOp(AST):
    """Бінарна операція: лівий i правий вузол + оператор."""

    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class Num(AST):
    """Числовий вузол з токеном та значенням."""

    def __init__(self, token):
        self.token = token
        self.value = token.value


class Parser:
    """Парсер будує синтаксичне дерево з токенів."""

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise ParsingError("Помилка синтаксичного аналізу")

    def eat(self, token_type):
        """Очікує певний тип токена й переходить до наступного."""
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """Фактор - це число чи вираз y дужках."""
        token = self.current_token
        if token.type == TokenType.INTEGER:
            self.eat(TokenType.INTEGER)
            return Num(token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node

    def term(self):
        """Терм - це множення чи ділення факторів."""
        node = self.factor()
        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self):
        """Вираз - це додавання та віднімання термів."""
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)
            node = BinOp(left=node, op=token, right=self.term())
        return node

    def parse(self):
        """Починає парсинг i повертає кореневий вузол дерева."""
        node = self.expr()
        if self.current_token.type != TokenType.EOF:
            self.error()
        return node


class Interpreter:
    """Інтерпретатор, що обходить дерево i обчислює значення виразу."""

    def __init__(self, parser):
        self.parser = parser

    def visit(self, node):
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Немає методу visit_{type(node).__name__}")

    def visit_BinOp(self, node):
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.DIV:
            right_val = self.visit(node.right)
            if right_val == 0:
                raise ZeroDivisionError("Ділення на нуль")
            return self.visit(node.left) / right_val

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)


def main():
    while True:
        try:
            text = input("Введіть вираз (чи 'exit'): ")
            if text.lower() == "exit":
                print("Вихід із програми.")
                break
            lexer = Lexer(text)
            parser = Parser(lexer)
            interpreter = Interpreter(parser)
            result = interpreter.interpret()
            print("Результат:", result)
        except Exception as e:
            print("Помилка:", e)


if __name__ == "__main__":
    main()
