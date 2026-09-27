"""Render a memory as a polaroid-style JPEG: square photo, note and sender below."""
import io

from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CANVAS_W = 1200
PHOTO_SIZE = 1080  # square, centered horizontally with 60px margins
MARGIN = 60
TEXT_W = PHOTO_SIZE
FOOTER_GAP = 44


def _wrap(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = f"{cur} {word}"
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def _fit_note(draw, text, max_width):
    """Pick the largest font size (56 -> 30) whose wrapped text stays within 6 lines."""
    for size in range(56, 29, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = _wrap(draw, text, font, max_width)
        if len(lines) <= 6:
            return font, lines
    font = ImageFont.truetype(FONT_PATH, 30)
    lines = _wrap(draw, text, font, max_width)[:6]
    if lines:
        lines[-1] = lines[-1][:60] + "…"
    return font, lines


def render_polaroid(photo_file, note, sender_name, when):
    photo = Image.open(photo_file)
    photo = ImageOps.exif_transpose(photo).convert("RGB")

    # Center-crop to square, then resize.
    side = min(photo.size)
    left = (photo.width - side) // 2
    top = (photo.height - side) // 2
    photo = photo.crop((left, top, left + side, top + side)).resize(
        (PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS
    )

    # Measure text to size the canvas like a real polaroid's wide bottom border.
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    note = (note or "").strip()
    note_font, note_lines = (None, [])
    if note:
        note_font, note_lines = _fit_note(scratch, note, TEXT_W)
    footer_font = ImageFont.truetype(FONT_BOLD_PATH, 34)

    line_h = 0
    if note_lines:
        bbox = scratch.textbbox((0, 0), "Ag", font=note_font)
        line_h = int((bbox[3] - bbox[1]) * 1.35)
    note_h = line_h * len(note_lines)
    footer_h = 42
    canvas_h = MARGIN + PHOTO_SIZE + 50 + note_h + (FOOTER_GAP if note_lines else 24) + footer_h + MARGIN

    canvas = Image.new("RGB", (CANVAS_W, canvas_h), "#FFFFFF")
    canvas.paste(photo, (MARGIN, MARGIN))
    draw = ImageDraw.Draw(canvas)

    y = MARGIN + PHOTO_SIZE + 50
    for line in note_lines:
        w = draw.textbbox((0, 0), line, font=note_font)[2]
        draw.text(((CANVAS_W - w) // 2, y), line, fill="#1F2937", font=note_font)
        y += line_h
    y += FOOTER_GAP if note_lines else 24

    footer = f"— {sender_name} · {when:%B %Y}"
    w = draw.textbbox((0, 0), footer, font=footer_font)[2]
    draw.text(((CANVAS_W - w) // 2, y), footer, fill="#6B7280", font=footer_font)

    out = io.BytesIO()
    canvas.save(out, "JPEG", quality=92)
    out.seek(0)
    return out
