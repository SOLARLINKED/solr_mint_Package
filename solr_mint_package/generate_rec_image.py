#!/usr/bin/env python3
"""
Generate a SOLRAI REC image (PNG/JPEG) with mock/sample data suitable for NFT metadata.

- Reads defaults from config.yaml but allows CLI overrides.
- Embeds your plant screenshot and overlays certificate text.
- Adds QR codes for burn proof (XRPL Testnet explorer) and pay-to-owner reference.

Usage:
  python generate_rec_image.py \
    --kwh 1000 \
    --burn-tx-hash BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB \
    --output SOLRAI_REC_SAMPLE.png

Dependencies:
  pip install Pillow qrcode[pil] PyYAML
"""
import argparse
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from PIL import Image, ImageDraw, ImageFont
import qrcode

# ---------- Config ----------
DEFAULT_OUTPUT = "SOLRAI_REC_SAMPLE.png"
DEFAULT_SCREENSHOT = "IMG_A6FBCF8F-9700-4089-ADB0-5C914EF43766.jpeg"
CANVAS_SIZE = (1800, 1200)  # width x height
MARGIN = 60
CARD_BG = (248, 250, 252)  # very light gray-blue
ACCENT = (6, 95, 70)       # teal/dark green
TEXT_PRIMARY = (15, 23, 42) # slate-900
TEXT_SECOND = (71, 85, 105) # slate-600
BORDER = (203, 213, 225)    # slate-300


def load_config(path: str = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def try_load_font(names, size):
    # Try a list of fonts commonly available; fallback to default
    font_paths = [
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        # allow passing exact path or family hint
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
    for path in font_paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_header(draw: ImageDraw.ImageDraw, W: int, x: int, y: int, title: str, subtitle: str) -> int:
    title_font = try_load_font(["Arial Bold", "Helvetica Neue Bold"], 64)
    sub_font = try_load_font(["Arial", "Helvetica Neue"], 28)
    draw.text((x, y), title, fill=ACCENT, font=title_font)
    y += int(64 * 1.2)
    draw.text((x, y), subtitle, fill=TEXT_SECOND, font=sub_font)
    y += int(28 * 1.8)
    draw.line([(x, y), (W - MARGIN, y)], fill=BORDER, width=2)
    return y + 30


def paste_screenshot(canvas: Image.Image, screenshot_path: Path, area):
    # area = (left, top, right, bottom)
    box_w = area[2] - area[0]
    box_h = area[3] - area[1]
    img = Image.open(screenshot_path).convert("RGB")
    img.thumbnail((box_w, box_h))
    # center within area
    paste_x = area[0] + (box_w - img.width) // 2
    paste_y = area[1] + (box_h - img.height) // 2
    canvas.paste(img, (paste_x, paste_y))


def text_block(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, value: str, label_font, value_font, gap=6) -> int:
    draw.text((x, y), label, fill=TEXT_SECOND, font=label_font)
    y += int(label_font.size * 1.2)
    draw.text((x, y), value, fill=TEXT_PRIMARY, font=value_font)
    y += int(value_font.size * 1.5) + gap
    return y


def make_qr(data: str, size: int = 260) -> Image.Image:
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.NEAREST)


def fmt_addr(addr: str, start=6, end=6) -> str:
    if not addr:
        return ""
    if len(addr) <= start + end:
        return addr
    return f"{addr[:start]}…{addr[-end:]}"


def generate_rec(
    output: Path,
    screenshot: Path,
    issuer: str,
    hot: str,
    owner: str,
    buyer: str,
    currency: str,
    kwh: float,
    jurisdiction: str,
    program: str,
    vintage: str,
    meter_hash: str,
    oracle_ref: str,
    burn_tx: str,
    price_usd: str,
    price_drops: str,
    nft_id: Optional[str] = None,
    xumm_url: Optional[str] = None,
) -> Path:
    W, H = CANVAS_SIZE
    canvas = Image.new("RGB", (W, H), CARD_BG)
    draw = ImageDraw.Draw(canvas)

    # Header
    title = "SOLRAI Renewable Energy Certificate (Testnet)"
    subtitle = f"1 SOLRAI-REC minted per 1,000 {currency} burned | Transfer fee 10% | Price ${price_usd}"
    y = draw_header(draw, W, MARGIN, MARGIN, title, subtitle)

    # Left column info
    label_font = try_load_font(["Arial", "Helvetica Neue"], 26)
    value_font = try_load_font(["Arial", "Helvetica Neue"], 36)

    col1_x = MARGIN
    col2_x = W // 2 + 20

    y1 = y
    y1 = text_block(draw, col1_x, y1, "Issuer (STN)", fmt_addr(issuer), label_font, value_font)
    y1 = text_block(draw, col1_x, y1, "Hot Wallet", fmt_addr(hot), label_font, value_font)
    y1 = text_block(draw, col1_x, y1, "System Owner", fmt_addr(owner), label_font, value_font)
    y1 = text_block(draw, col1_x, y1, "Buyer", fmt_addr(buyer), label_font, value_font)

    y1 = text_block(draw, col1_x, y1, "Vintage", vintage, label_font, value_font)
    y1 = text_block(draw, col1_x, y1, "Jurisdiction / Program", f"{jurisdiction} / {program}", label_font, value_font)
    # Optional extended compliance fields if present in config
    cfg = load_config()
    if cfg.get("facility_name"):
        y1 = text_block(draw, col1_x, y1, "Facility", cfg.get("facility_name", ""), label_font, value_font)
    if cfg.get("facility_location"):
        y1 = text_block(draw, col1_x, y1, "Location", cfg.get("facility_location", ""), label_font, value_font)
    if cfg.get("grid_region") or cfg.get("technology"):
        y1 = text_block(draw, col1_x, y1, "Grid / Tech", f"{cfg.get('grid_region','')} / {cfg.get('technology','')}", label_font, value_font)
    if cfg.get("vintage_start") or cfg.get("vintage_end"):
        y1 = text_block(draw, col1_x, y1, "Vintage Window", f"{cfg.get('vintage_start','')} → {cfg.get('vintage_end','')}", label_font, value_font)

    # Right column info
    y2 = y
    y2 = text_block(draw, col2_x, y2, "Production (kWh)", f"{kwh:,.2f}", label_font, value_font)
    y2 = text_block(draw, col2_x, y2, f"{currency} Minted", f"{kwh:,.2f} {currency}", label_font, value_font)
    y2 = text_block(draw, col2_x, y2, f"{currency} Burned", "1,000.00", label_font, value_font)
    y2 = text_block(draw, col2_x, y2, "Price (XRP drops)", f"{price_drops}", label_font, value_font)

    # Screenshot panel box
    panel_top = max(y1, y2) + 10
    panel_rect = (MARGIN, panel_top, W - MARGIN, panel_top + 480)
    # border
    draw.rounded_rectangle(panel_rect, radius=16, outline=BORDER, width=2, fill=(255, 255, 255))
    # paste screenshot centered in panel
    paste_screenshot(canvas, screenshot, (panel_rect[0] + 16, panel_rect[1] + 16, panel_rect[2] - 16, panel_rect[3] - 16))

    # Proofs & QR codes row
    section_y = panel_rect[3] + 24
    draw.line([(MARGIN, section_y), (W - MARGIN, section_y)], fill=BORDER, width=2)
    section_y += 20

    small_label = try_load_font(["Arial", "Helvetica Neue"], 22)
    small_value = try_load_font(["Arial", "Helvetica Neue"], 26)

    # Burn proof
    burn_url = f"https://testnet.xrpl.org/transactions/{burn_tx}" if burn_tx else "https://testnet.xrpl.org/"
    burn_qr = make_qr(burn_url)
    qr_y = section_y + 10
    canvas.paste(burn_qr, (MARGIN, qr_y))
    txt_x = MARGIN + burn_qr.width + 18
    y_txt = section_y
    y_txt = text_block(draw, txt_x, y_txt, "Burn Proof (Tx Hash)", burn_tx or "<mock-burn-hash>", small_label, small_value)
    y_txt = text_block(draw, txt_x, y_txt, "Explorer URL", burn_url, small_label, try_load_font(["Arial"], 22))

    # Pay-to owner QR (address + drops as a simple string)
    # If xumm_url provided, prefer it for Xaman deep link; else fallback to simple JSON payload
    if xumm_url:
        pay_qr = make_qr(xumm_url)
        pay_caption = "Scan to sign in Xaman"
    else:
        pay_str = json.dumps({
            "to": owner,
            "amount_drops": price_drops,
            "note": "SOLRAI-REC Testnet Purchase"
        })
        pay_qr = make_qr(pay_str)
        pay_caption = "Scan to pay owner (XRP drops)"
    pay_x = W - MARGIN - pay_qr.width
    canvas.paste(pay_qr, (pay_x, qr_y))
    cap = pay_caption if (xumm_url or price_drops) else "Owner address"
    draw.text((pay_x, qr_y + pay_qr.height + 8), cap, fill=TEXT_SECOND, font=small_label)

    # Footer
    footer_y = H - MARGIN - 90
    draw.line([(MARGIN, footer_y), (W - MARGIN, footer_y)], fill=BORDER, width=2)
    footer_y += 16
    foot_font = try_load_font(["Arial", "Helvetica Neue"], 22)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    footer_text = f"Generated: {now} • NFT Flags: Transferable, Burnable • Transfer Fee: 10% • Testnet"
    draw.text((MARGIN, footer_y), footer_text, fill=TEXT_SECOND, font=foot_font)

    # Optional NFT ID text (if provided)
    if nft_id:
        draw.text((MARGIN, footer_y + 30), f"NFTokenID: {fmt_addr(nft_id, 10, 10)}", fill=TEXT_SECOND, font=foot_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    ext = output.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        canvas.save(output, format="JPEG", quality=92)
    else:
        canvas.save(output, format="PNG")
    return output


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Generate a SOLRAI REC image with mock/sample data")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output image path (.png or .jpg)")
    parser.add_argument("--image", default=cfg.get("image_path", DEFAULT_SCREENSHOT), help="Screenshot image path")
    parser.add_argument("--kwh", type=float, default=1000.0, help="Total kWh produced for sample")
    parser.add_argument("--burn-tx-hash", default="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", help="Mock burn tx hash")
    parser.add_argument("--nft-id", default=None, help="Optional NFTokenID to display")
    parser.add_argument("--xumm-url", default=None, help="Optional Xumm/Xaman sign URL to embed as QR")
    args = parser.parse_args()

    output = Path(args.output)
    screenshot = Path(args.image)

    issuer = cfg.get("issuer_address", "r3S15u4jgVru2wzHDbhyzjMhGBCXvozQWR")
    hot = cfg.get("hot_address", "rUowmT93AQ4ag2C4onY29sVRTNbmqXqQWQ")
    owner = cfg.get("system_owner_address", "rNeTREnTe9kXUoGqS2LH4kL8uQVgZzCH5a")
    buyer = cfg.get("nft_buyer_address", "rsgpdWshJQYRVkDLEHtHJWFzxLoEs6cFe4")
    currency = cfg.get("currency_code", "STN")
    jurisdiction = cfg.get("jurisdiction", "US-NJ")
    program = cfg.get("program", "NJ-SREC")
    vintage = cfg.get("vintage", "2025")
    meter_hash = cfg.get("meter_hash", "meterhashdeadbeef...")
    oracle_ref = cfg.get("oracle_reference", "https://example.com/oracle-proof")
    price_usd = cfg.get("price_usd", "90")
    price_drops = cfg.get("price_xrp_drops", "270000000")  # mock ~270 XRP for $90 if 1 XRP=$0.333

    generate_rec(
        output=output,
        screenshot=screenshot,
        issuer=issuer,
        hot=hot,
        owner=owner,
        buyer=buyer,
        currency=currency,
        kwh=args.kwh,
        jurisdiction=jurisdiction,
        program=program,
        vintage=vintage,
        meter_hash=meter_hash,
        oracle_ref=oracle_ref,
        burn_tx=args.burn_tx_hash,
        price_usd=str(price_usd),
        price_drops=str(price_drops),
        nft_id=args.nft_id,
        xumm_url=args.xumm_url,
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
