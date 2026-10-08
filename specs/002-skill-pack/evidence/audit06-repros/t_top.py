"""Top edge: tall Vietnamese capitals in the first line of a top- or bottom-anchored box (Georgia = stock voice `field`)."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck

def run(mode, voice_name):
    d = Deck("swiss", mode, voice_name)
    cases = [
        ("statement title 'Hello world' (control)", lambda d: d.add("statement", "Hello world"), "title"),
        ("statement title 'Ẩn số'", lambda d: d.add("statement", "Ẩn số"), "title"),
        ("statement title 'Ỗ Ẫ Ẩ'", lambda d: d.add("statement", "Ỗ Ẫ Ẩ"), "title"),
        ("statement title 'Ấn Độ'", lambda d: d.add("statement", "Ấn Độ"), "title"),
        ("section title 'Ẩm thực'", lambda d: d.add("section", "Ẩm thực"), "title"),
        ("quote title 'Ẩn'", lambda d: d.add("quote", "Ẩn mình chờ thời"), "title"),
        ("statement main lede 'Ẩm thực'", lambda d: d.add("statement", "x").text("Ẩm thực Việt Nam", style="lede"), "main"),
        ("section main label 'ẩm thực'", lambda d: d.add("section", "x").text("ẩm thực", style="label"), "main"),
        ("close main lede 'Ẩn'", lambda d: d.add("close", "x").text("Ẩn số", style="lede"), "main"),
    ]
    order = build(d, cases, W / f"top-{mode}-{Path(voice_name).stem}.pptx")
    pdf, imgs = render(W / f"top-{mode}-{Path(voice_name).stem}.pptx")
    print(f"== {mode} {voice_name}")
    measure(order, imgs)

for mode in ("presented", "read"):
    run(mode, "field")
