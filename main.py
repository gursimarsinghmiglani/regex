from collections import deque


def preprocess(regex):
    new_regex = []
    new_regex.append(regex[0])
    prev_char = regex[0]
    for ch in regex[1:]:
        if ch not in ")|*" and prev_char not in "|(":
            new_regex.append(".")
        new_regex.append(ch)
        prev_char = ch
    return "".join(new_regex)


def infix_to_postfix(regex):
    regex = preprocess(regex)
    stack = []
    precedence = {"|": 0, ".": 1, "*": 2}
    postfix = []
    for ch in regex:
        if ch == "(":
            stack.append(ch)
        elif ch not in precedence and ch != ")":
            postfix.append(ch)
        elif ch in precedence:
            while (
                len(stack) > 0
                and stack[-1] != "("
                and precedence[stack[-1]] >= precedence[ch]
            ):
                postfix.append(stack.pop())
            stack.append(ch)
        else:
            while stack[-1] != "(":
                postfix.append(stack.pop())
            stack.pop()
    while len(stack) > 0:
        postfix.append(stack.pop())
    return "".join(postfix)


class NFA:
    ALPHABET_SIZE = 256

    def __init__(self, num_states, delta, start_state, final_state):
        self.num_states = num_states
        self.delta = delta
        self.start_state = start_state
        self.final_state = final_state

    @classmethod
    def single_char_nfa(cls, char):
        num_states = 2
        delta = [
            [set() for _ in range(NFA.ALPHABET_SIZE + 1)] for _ in range(num_states)
        ]
        delta[0][ord(char)].add(1)
        start_state = 0
        final_state = 1
        return NFA(num_states, delta, start_state, final_state)

    def kleene_star(self):
        self.delta[self.final_state][self.ALPHABET_SIZE].add(self.start_state)
        self.final_state = self.start_state

    def concatenate(self, other):
        for _ in range(other.num_states):
            self.delta.append([set() for _ in range(NFA.ALPHABET_SIZE + 1)])
        for i in range(other.num_states):
            for j in range(NFA.ALPHABET_SIZE + 1):
                s = set()
                for k in other.delta[i][j]:
                    s.add(k + self.num_states)
                self.delta[self.num_states + i][j] = s
        self.delta[self.final_state][self.ALPHABET_SIZE].add(
            self.num_states + other.start_state
        )
        self.final_state = self.num_states + other.final_state
        self.num_states += other.num_states

    def union(self, other):
        for _ in range(other.num_states):
            self.delta.append([set() for _ in range(NFA.ALPHABET_SIZE + 1)])
        for i in range(other.num_states):
            for j in range(NFA.ALPHABET_SIZE + 1):
                s = set()
                for k in other.delta[i][j]:
                    s.add(k + self.num_states)
                self.delta[self.num_states + i][j] = s
        self.delta[self.start_state][self.ALPHABET_SIZE].add(
            self.num_states + other.start_state
        )
        self.delta[self.final_state][self.ALPHABET_SIZE].add(
            self.num_states + other.final_state
        )
        self.final_state = self.num_states + other.final_state
        self.num_states += other.num_states

    def epsilon_closure(self, state):
        stack = [state]
        closure = set()
        while stack:
            current_state = stack.pop()
            if current_state not in closure:
                closure.add(current_state)
                for next_state in self.delta[current_state][self.ALPHABET_SIZE]:
                    if next_state not in closure:
                        stack.append(next_state)
        return closure

    def to_dfa(self):
        num_states = 0
        delta = []
        start_state = 0
        final_states = set()
        state_map = {}
        queue = deque([frozenset(self.epsilon_closure(self.start_state))])
        while queue:
            current_set = queue.popleft()
            if current_set in state_map:
                continue
            state_map[current_set] = num_states
            delta.append([set() for _ in range(NFA.ALPHABET_SIZE)])
            for char in range(NFA.ALPHABET_SIZE):
                s = set()
                for nfa_state in current_set:
                    for state in self.delta[nfa_state][char]:
                        s = s.union(self.epsilon_closure(state))
                delta[num_states][char] = s
                queue.append(frozenset(s))
            num_states += 1
        for i in range(num_states):
            for char in range(NFA.ALPHABET_SIZE):
                delta[i][char] = state_map[frozenset(delta[i][char])]
        for x in state_map:
            if self.final_state in x:
                final_states.add(state_map[x])
        return DFA(num_states, delta, start_state, final_states)


def postfix_to_nfa(postfix):
    stack = []
    for ch in postfix:
        if ch not in "|.*":
            stack.append(NFA.single_char_nfa(ch))
        elif ch == "*":
            stack[-1].kleene_star()
        elif ch == "|":
            nfa = stack.pop()
            stack[-1].union(nfa)
        else:
            nfa = stack.pop()
            stack[-1].concatenate(nfa)
    return stack.pop()


class DFA:
    ALPHABET_SIZE = NFA.ALPHABET_SIZE

    def __init__(self, num_states, delta, start_state, final_states):
        self.num_states = num_states
        self.delta = delta
        self.start_state = start_state
        self.final_states = final_states

    def accept(self, string):
        current_state = self.start_state
        for char in string:
            current_state = self.delta[current_state][ord(char)]
        return current_state in self.final_states


def dfa_from_regex(regex):
    postfix = infix_to_postfix(regex)
    nfa = postfix_to_nfa(postfix)
    dfa = NFA.to_dfa(nfa)
    return dfa


def main():
    regex = "(a|b)*abb"
    dfa = dfa_from_regex(regex)
    test_strings = ["aabb", "ab", "aa", "bba", "abab"]
    for s in test_strings:
        print(f"String '{s}' accepted: {dfa.accept(s)}")


if __name__ == "__main__":
    main()
