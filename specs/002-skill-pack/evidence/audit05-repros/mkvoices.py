from pathlib import Path

src = Path("./src/keyline/packs/swiss/voices/neutral.toml").read_text()
out = Path("/tmp/keyline-audit05/voices")
out.mkdir(exist_ok=True)
for family, name in [("Courier New", "courier"), ("Calibri", "calibri"), ("Cambria", "cambria"),
                     ("Times New Roman", "times")]:
    text = (src.replace('name = "neutral"', f'name = "{name}"')
               .replace('display = "Arial"', f'display = "{family}"')
               .replace('text = "Arial"', f'text = "{family}"'))
    (out / f"{name}.toml").write_text(text)
    print(out / f"{name}.toml")
