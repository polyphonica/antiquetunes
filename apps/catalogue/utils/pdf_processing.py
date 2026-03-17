"""
PDF processing pipeline.
- generate_cover_thumbnail: convert page 1 to WebP image
- generate_watermarked_preview: render page 1, stamp "PREVIEW" watermark, save as PDF
"""
import io
import os
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


def generate_cover_thumbnail(pdf_path: str, width: int = 600) -> ContentFile | None:
    """
    Convert the first page of a PDF to a WebP thumbnail.
    Returns a ContentFile ready to save to an ImageField, or None on failure.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return None

    try:
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            dpi=150,
            fmt='jpeg',
        )
    except Exception:
        return None

    if not images:
        return None

    img = images[0]

    # Resize proportionally
    ratio = width / img.width
    height = int(img.height * ratio)
    img = img.resize((width, height), Image.LANCZOS)

    # Convert to WebP
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=85, method=6)
    buf.seek(0)
    return ContentFile(buf.read())


def generate_watermarked_preview(pdf_path: str, slug: str) -> ContentFile | None:
    """
    Render the first page of the PDF, overlay a diagonal "PREVIEW" watermark,
    and save back as a single-page PDF.
    Returns a ContentFile, or None on failure.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return None

    try:
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            dpi=150,
        )
    except Exception:
        return None

    if not images:
        return None

    img = images[0].convert('RGBA')
    w, h = img.size

    # Create transparent watermark layer
    watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)

    text = 'PREVIEW — ANTIQUETUNES.COM'
    font_size = max(60, w // 10)

    font = None
    for font_path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except (IOError, OSError):
            continue
    if font is None:
        font = ImageFont.load_default()

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Place at centre, diagonal
    angle = 30
    x = (w - text_w) / 2
    y = (h - text_h) / 2

    # Draw semi-transparent text
    draw.text((x, y), text, font=font, fill=(180, 0, 0, 170))

    # Rotate watermark
    watermark = watermark.rotate(angle, expand=False)
    img = Image.alpha_composite(img, watermark).convert('RGB')

    # Save as PDF via Pillow
    buf = io.BytesIO()
    img.save(buf, format='PDF', resolution=150)
    buf.seek(0)
    return ContentFile(buf.read())
