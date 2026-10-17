import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--lines", action="store_true", help="count lines instead of words")
    p.add_argument("--verbose", action="store_true", help="print a count per file")
    a = p.parse_args()
    total = 0
    for f in a.files:
        with open(f, encoding="utf-8") as fh:
            text = fh.read()
        n = len(text.splitlines()) if a.lines else len(text.split())
        if a.verbose:
            print(f"{f}: {n}")
        total += n
    print(total)


if __name__ == "__main__":
    main()
