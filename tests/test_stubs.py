"""The steps that aren't built say so and fail, instead of faking it."""
import pytest

from meatbag.cli import main


@pytest.mark.parametrize("cmd", ["distill", "select-cases"])
def test_unbuilt_steps_exit_nonzero_and_say_why(cmd, capsys):
    assert main([cmd]) != 0
    err = capsys.readouterr().err
    assert "not built yet" in err and "What to do today" in err


def test_unknown_command(capsys):
    assert main(["bake"]) == 2


def test_sort_and_hunt_prompts_use_config_examples(home):
    from meatbag import gremlin_hunt, sort_gremlin
    p = gremlin_hunt.system()
    assert "invented examples" in p and "things Pat said" in p
    with (home / "gremlin.toml").open("a") as f:
        f.write('\n[gremlin]\nexamples = ["the HOA can fine me, so I fined the HOA"]\n'
                'near_misses = ["plain joke: Chad\'s boat pun"]\n')
    p = gremlin_hunt.system()
    assert "Pat's own, confirmed" in p and "fined the HOA" in p and "boat pun" in p
    assert "become the spreadsheet" not in p
    assert "fined the HOA" in sort_gremlin.system()
