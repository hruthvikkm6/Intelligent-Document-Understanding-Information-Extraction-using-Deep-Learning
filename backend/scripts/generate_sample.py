"""Create a wholly synthetic invoice image for demos and smoke checks."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def main():
    out = Path(__file__).resolve().parents[2] / "sample_data" / "clean_invoice.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1500, 1900), "white")
    draw = ImageDraw.Draw(image)
    font_path = "C:/Windows/Fonts/arial.ttf"
    bold_path = "C:/Windows/Fonts/arialbd.ttf"

    def font(size, bold=False):
        try:
            return ImageFont.truetype(bold_path if bold else font_path, size)
        except OSError:
            return ImageFont.load_default()

    draw.text((110, 90), "NORTHSTAR OFFICE SUPPLIES", fill="#18334a", font=font(44, True))
    draw.text(
        (110, 155), "42 Market Road, Bengaluru, Karnataka 560001", fill="#333333", font=font(24)
    )
    draw.text((110, 195), "GSTIN: 29ABCDE1234F1Z5", fill="#333333", font=font(24))
    draw.line((110, 250, 1390, 250), fill="#9daab4", width=3)
    draw.text((110, 290), "TAX INVOICE", fill="#18334a", font=font(36, True))
    draw.text((110, 370), "Invoice Number: NS-2026-1042", fill="#222222", font=font(26))
    draw.text((850, 370), "Invoice Date: 18 Nov 2026", fill="#222222", font=font(26))
    draw.text((110, 420), "Due Date: 18 Dec 2026", fill="#222222", font=font(26))
    draw.text((110, 510), "Bill To: Acme Research Labs", fill="#222222", font=font(27, True))
    draw.text((110, 555), "12 Innovation Park, Bengaluru", fill="#333333", font=font(24))
    draw.rectangle((110, 650, 1390, 720), fill="#eaf0f4")
    draw.text((130, 670), "Description", fill="#18334a", font=font(24, True))
    draw.text((830, 670), "Qty", fill="#18334a", font=font(24, True))
    draw.text((1010, 670), "Unit Price", fill="#18334a", font=font(24, True))
    draw.text((1230, 670), "Amount", fill="#18334a", font=font(24, True))
    draw.text((130, 760), "A4 Recycled Paper (Box)", fill="#222222", font=font(23))
    draw.text((860, 760), "2", fill="#222222", font=font(23))
    draw.text((1010, 760), "₹ 5,000.00", fill="#222222", font=font(23))
    draw.text((1230, 760), "₹ 10,000.00", fill="#222222", font=font(23))
    draw.text((130, 825), "Laser Toner Cartridge", fill="#222222", font=font(23))
    draw.text((860, 825), "7", fill="#222222", font=font(23))
    draw.text((1010, 825), "₹ 5,000.00", fill="#222222", font=font(23))
    draw.text((1230, 825), "₹ 35,000.00", fill="#222222", font=font(23))
    draw.line((110, 910, 1390, 910), fill="#ccd2d7", width=2)
    draw.text((990, 990), "Subtotal", fill="#333333", font=font(24))
    draw.text((1220, 990), "₹ 45,000.00", fill="#333333", font=font(24))
    draw.text((990, 1050), "GST (18%)", fill="#333333", font=font(24))
    draw.text((1220, 1050), "₹ 8,100.00", fill="#333333", font=font(24))
    draw.line((960, 1100, 1390, 1100), fill="#9daab4", width=2)
    draw.text((990, 1140), "TOTAL INR", fill="#18334a", font=font(30, True))
    draw.text((1220, 1140), "₹ 53,100.00", fill="#18334a", font=font(28, True))
    draw.text((110, 1320), "Payment terms: Net 30 days", fill="#444444", font=font(23))
    draw.text((110, 1370), "Thank you for your business.", fill="#777777", font=font(22))
    image.save(out)

    # Alternate synthetic layout with right-aligned metadata and a compact table.
    alternate = Image.new("RGB", (1500, 1900), "white")
    alt = ImageDraw.Draw(alternate)
    alt.text((105, 95), "BLUEBIRD DESIGN STUDIO", fill="#18334a", font=font(42, True))
    alt.text((105, 155), "88 Residency Road · Bengaluru 560025", fill="#333333", font=font(24))
    alt.text((105, 195), "GSTIN: 29PQRSX5678L1Z1", fill="#333333", font=font(24))
    alt.text((1080, 330), "INVOICE", fill="#18334a", font=font(34, True))
    alt.text((850, 395), "No: BB-26-208", fill="#222222", font=font(25))
    alt.text((850, 440), "Date: 19 Nov 2026", fill="#222222", font=font(25))
    alt.text((850, 485), "Due: 19 Dec 2026", fill="#222222", font=font(25))
    alt.line((105, 550, 1395, 550), fill="#9daab4", width=3)
    alt.text((110, 600), "Invoice for", fill="#687687", font=font(22))
    alt.text((110, 640), "Cedar Analytics Pvt Ltd", fill="#222222", font=font(28, True))
    alt.text((110, 685), "7 Science Park, Bengaluru", fill="#333333", font=font(24))
    alt.rectangle((105, 790, 1395, 855), fill="#eaf0f4")
    alt.text((125, 808), "Service", fill="#18334a", font=font(23, True))
    alt.text((900, 808), "Units", fill="#18334a", font=font(23, True))
    alt.text((1170, 808), "INR", fill="#18334a", font=font(23, True))
    alt.text((125, 900), "Data visualization consulting", fill="#222222", font=font(24))
    alt.text((925, 900), "10", fill="#222222", font=font(24))
    alt.text((1170, 900), "₹ 24,000.00", fill="#222222", font=font(24))
    alt.line((105, 970, 1395, 970), fill="#ccd2d7", width=2)
    alt.text((980, 1040), "Subtotal: ₹ 24,000.00", fill="#333333", font=font(24))
    alt.text((980, 1100), "GST: ₹ 4,320.00", fill="#333333", font=font(24))
    alt.text((980, 1180), "Amount Due: ₹ 28,320.00", fill="#18334a", font=font(27, True))
    alternate.save(out.with_name("alternate_layout.png"))

    # A deliberately degraded scan for OCR robustness demonstrations.
    low_quality = (
        image.resize((750, 950)).resize(image.size).filter(ImageFilter.GaussianBlur(radius=0.8))
    )
    low_quality.save(out.with_name("low_quality_invoice.jpg"), quality=38, optimize=True)

    continuation = Image.new("RGB", image.size, "white")
    cont = ImageDraw.Draw(continuation)
    cont.text((110, 100), "NORTHSTAR OFFICE SUPPLIES", fill="#18334a", font=font(40, True))
    cont.text((110, 190), "Invoice NS-2026-1042 · Continued", fill="#333333", font=font(28))
    cont.line((110, 270, 1390, 270), fill="#9daab4", width=3)
    cont.text((110, 340), "Additional notes", fill="#18334a", font=font(28, True))
    cont.text((110, 405), "Delivery completed on 18 Nov 2026.", fill="#333333", font=font(24))
    cont.text((110, 455), "Payment terms: Net 30 days.", fill="#333333", font=font(24))
    cont.text(
        (110, 560),
        "Please reference invoice NS-2026-1042 with payment.",
        fill="#333333",
        font=font(22),
    )
    image.save(
        out.with_name("multipage_invoice.pdf"),
        "PDF",
        save_all=True,
        append_images=[continuation],
        resolution=150,
    )
    image.save(out.with_suffix(".pdf"), "PDF", resolution=150)
    print(out)


if __name__ == "__main__":
    main()
