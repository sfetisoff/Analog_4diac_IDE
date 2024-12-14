from base_block import MyBlock


class BlockStart(MyBlock):
    def __init__(self, main_window, name='START', x=50, y=100):
        super().__init__(main_window, name=name, width=60, height=80, x=x, y=y,
                         n_rects_left=1, n_rects_right=2, labels=['E_RESTART', 'STOP', 'COLD', 'WARM'])


class BlockA(MyBlock):  # INT2INT
    def __init__(self, main_window, name='INT2INT', x=300, y=300):
        super().__init__(main_window, name=name, width=60, height=82, x=x, y=y,
                         n_rects_left=2, n_rects_right=2, labels=['INT2INT', 'REQ', 'IN', 'CNF', 'OUT'])


class BlockB(MyBlock):  # OUT_ANY_CONSOLE
    def __init__(self, main_window, name='OUT_ANY_CONSOLE', x=300, y=300):
        super().__init__(main_window, name=name, width=92, height=112, x=x, y=y,
                         n_rects_left=4, n_rects_right=2,
                         labels=['OUT_ANY_CONSOLE', 'REQ', 'QI', 'LABEL', 'IN', 'CNF', 'QO'])


class BlockC(MyBlock):  # STRING2STRING
    def __init__(self, main_window, name='STRING2STRING', x=300, y=300):
        super().__init__(main_window, name=name, x=x, y=y, width=84, height=82,
                         n_rects_left=2, n_rects_right=2, labels=['STRING2STRING', 'REQ', 'IN', 'CNF', 'OUT'])


class BlockD(MyBlock):  # F_ADD
    def __init__(self, main_window, name='F_ADD', x=300, y=300):
        super().__init__(main_window, name=name, width=50, height=96, x=x, y=y,
                         n_rects_left=3, n_rects_right=2, labels=['F_ADD', 'REQ', 'IN1', 'IN2', 'CNF', 'OUT'])


def all_block_classes():
    classes = {'E_RESTART': BlockStart,
               'INT2INT': BlockA,
               'OUT_ANY_CONSOLE': BlockB,
               'STRING2STRING': BlockC,
               'F_ADD': BlockD}
    return classes

def count_blocks():
    count = {'Block_A': 1, 'Block_B': 1, 'Block_C': 1, 'Block_D': 1}
    return count