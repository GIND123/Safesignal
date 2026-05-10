"""Backward-compatible wrapper for loading the original Margaret Chen demo case."""

from load_synthetic_patient import main


if __name__ == "__main__":
    raise SystemExit(main(default_case="margaret_chen"))
