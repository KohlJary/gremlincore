from meatbag import filters


def test_no_topics_by_default_means_every_override_generalizes(home):
    row = {"override": True, "move": "reject the landlord's framing", "default_rejected": "comply"}
    assert filters.do_not_generalize() is None
    assert filters.generalizable_move(row)
    assert not filters.generalizable_move({"override": False, "move": "x"})


def test_configured_topics_stay_out_of_moves(home):
    with (home / "gremlin.toml").open("a") as f:
        f.write('\n[filters]\ndo_not_generalize = ["landlord", "custod"]\n')
    assert not filters.generalizable_move({"override": True, "move": "push back on the LANDLORD"})
    assert not filters.generalizable_move({"override": True, "quote": "the custody hearing is a farce"})
    assert filters.generalizable_move({"override": True, "move": "raise the ambition"})


def test_explicit_topics_override_config(home):
    assert not filters.generalizable_move({"override": True, "move": "ignore the HOA"}, topics=["hoa"])


def test_paste_detection_uses_the_owners_name(home):
    assert filters.is_paste("Pat said the barbecue is at 3.")
    assert not filters.is_paste("the barbecue is at 3, bring a chair")
    assert filters.is_paste("Greg said the barbecue is at 3.", owner="Greg")
    assert filters.is_paste("x" * 3001)
    assert filters.is_paste("\n".join(["la la la"] * 12))
