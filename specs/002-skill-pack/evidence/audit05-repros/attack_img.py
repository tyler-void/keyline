"""image(): formats Pillow opens but the writer cannot embed; EXIF orientation."""
from PIL import Image

from keyline.pen import Deck, PenError

OUT = "/tmp/keyline-audit05"
im = Image.new("RGB", (400, 100), "#336699")
for fmt, ext in [("PNG", "png"), ("JPEG", "jpg"), ("GIF", "gif"), ("BMP", "bmp"), ("TIFF", "tif"),
                 ("WEBP", "webp"), ("PPM", "ppm"), ("TGA", "tga"), ("ICO", "ico")]:
    path = f"{OUT}/img.{ext}"
    im.save(path, format=fmt)
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    try:
        deck.add("evidence", "A picture").image(path, alt="A blue band")
    except PenError as exc:
        print(f"{fmt:5}: refused at image(): {exc}")
        continue
    try:
        deck.save(f"{OUT}/img-{ext}.pptx")
        print(f"{fmt:5}: accepted and saved")
    except Exception as exc:  # noqa: BLE001
        print(f"{fmt:5}: accepted by image(), save() raised {type(exc).__name__}: {str(exc)[:80]}")

# EXIF orientation 6: stored 400x100, displayed 100x400 by viewers that honour EXIF
exif = Image.Exif()
exif[0x0112] = 6
im2 = Image.new("RGB", (400, 100), "#336699")
for x in range(0, 400, 50):
    for y in range(100):
        im2.putpixel((x, y), (255, 255, 255))
im2.save(f"{OUT}/exif6.jpg", format="JPEG", exif=exif.tobytes())
deck = Deck(pack="swiss", mode="presented", voice="neutral")
deck.add("evidence", "A rotated picture").image(f"{OUT}/exif6.jpg", alt="Stripes")
deck.save(f"{OUT}/img-exif6.pptx")
print("EXIF6 saved")

# the file changes between image() and save(): the box keeps the old aspect
Image.new("RGB", (100, 100), "#336699").save(f"{OUT}/swap.png")
deck = Deck(pack="swiss", mode="presented", voice="neutral")
deck.add("evidence", "A swapped picture").image(f"{OUT}/swap.png", alt="A square")
Image.new("RGB", (800, 100), "#993333").save(f"{OUT}/swap.png")
deck.save(f"{OUT}/img-swap.pptx")
print("swap saved")
