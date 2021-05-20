from main import *

def test_select():
    assert select('1', '2', '3') == [1, 2, 3]
    assert select('1', '2>3') == [1, 2, 3]
    assert select([1, 2, 3]) == [1, 2, 3]
    assert select(1, 2, 3) == [1, 2, 3]
    assert select(1, 2, '3>5') == [1, 2, 3, 4, 5]

def test_clear():
    assert clear() == []

def test_read_line():
    print(read_line('@120 macs si 25 in 2 # cue name'))