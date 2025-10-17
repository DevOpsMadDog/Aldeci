from services.score_ext.bayes import bayes_fuse


def test_bayes_monotonic_cvss() -> None:
    low = bayes_fuse(3.0, 0.1, False, 0.0, ["internal"])
    high = bayes_fuse(9.0, 0.1, False, 0.0, ["internal"])
    assert high > low


def test_bayes_epss_and_kev_increase_probability() -> None:
    baseline = bayes_fuse(5.0, 0.05, False, 0.0, ["internal"])
    epss_boost = bayes_fuse(5.0, 0.5, False, 0.0, ["internal"])
    kev_boost = bayes_fuse(5.0, 0.05, True, 0.0, ["internal"])
    assert epss_boost > baseline
    assert kev_boost > baseline
