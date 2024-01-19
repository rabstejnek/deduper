import pytest

from pyscaffold.work import bottles, super_add


def test_bottles(capsys):
    bottles(1, "pepsi")
    captured = capsys.readouterr()
    assert "1 bottles of pepsi on the wall" in captured.out


def test_super_add():
    # test expected
    assert super_add(2, 2) == 4

    # test unexpected
    with pytest.raises(TypeError):
        super_add(2, "skunk")
