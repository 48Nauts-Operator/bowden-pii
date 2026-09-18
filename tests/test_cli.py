from bowden_pii.cli import main
from bowden_pii.types import Detection


class FakeMiniLMTokenDetector:
    @classmethod
    def from_model_dir(
        cls,
        model_dir: str,
        device: str | None = None,
        max_length: int = 256,
    ) -> "FakeMiniLMTokenDetector":
        assert model_dir == "fake-model"
        assert device is None
        assert max_length == 256
        return cls()

    def __call__(self, _text: str) -> list[Detection]:
        return [
            Detection(
                start=0,
                end=10,
                label="PERSON",
                value="Mia Keller",
                source="neural",
                rule_id="fake-person",
                confidence=0.95,
            )
        ]


def test_cli_hybrid_mode_redacts_with_model_detector(monkeypatch, capsys) -> None:
    import bowden_pii.cli as cli

    monkeypatch.setattr(cli, "MiniLMTokenDetector", FakeMiniLMTokenDetector)

    code = main(
        [
            "--mode",
            "hybrid",
            "--model-dir",
            "fake-model",
            "Mia Keller uses mia@example.ch",
        ]
    )

    assert code == 0
    assert capsys.readouterr().out.strip() == "[PERSON_1] uses [EMAIL_1]"


def test_cli_requires_model_dir_for_hybrid_mode(capsys) -> None:
    code = main(["--mode", "hybrid", "Mia Keller uses mia@example.ch"])

    assert code == 2
    assert "--model-dir is required for hybrid mode" in capsys.readouterr().err
