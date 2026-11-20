"""Generate a synthetic, OCR-friendly invoice PDF for a manual project demo."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "stellar_analytics_invoice.pdf"
NAVY = colors.HexColor("#18334A")
INK = colors.HexColor("#252B32")
MUTED = colors.HexColor("#667483")
PALE = colors.HexColor("#EAF0F4")


def register_fonts() -> tuple[str, str]:
    windows_fonts = Path("C:/Windows/Fonts")
    regular = windows_fonts / "arial.ttf"
    bold = windows_fonts / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("DemoSans", str(regular)))
        pdfmetrics.registerFont(TTFont("DemoSans-Bold", str(bold)))
        return "DemoSans", "DemoSans-Bold"
    return "Helvetica", "Helvetica-Bold"


def draw_invoice(path: Path) -> None:
    regular, bold = register_fonts()
    page_width, page_height = letter
    pdf = canvas.Canvas(str(path), pagesize=letter, pageCompression=1)
    pdf.setTitle("Synthetic Tax Invoice - Stellar Analytics")
    pdf.setAuthor("Synthetic project demo data")

    # Vendor letterhead.
    pdf.setFillColor(NAVY)
    pdf.setFont(bold, 17)
    pdf.drawString(46, 742, "STELLAR ANALYTICS PRIVATE LIMITED")
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 9.5)
    pdf.drawString(46, 724, "44 Residency Road, Bengaluru, Karnataka 560025")
    pdf.drawString(46, 709, "GSTIN: 29AABCS4821Q1Z7")

    pdf.setFillColor(NAVY)
    pdf.setFont(bold, 23)
    pdf.drawRightString(page_width - 46, 742, "TAX INVOICE")
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 9)
    pdf.drawRightString(page_width - 46, 724, "ORIGINAL FOR RECIPIENT")
    pdf.setStrokeColor(colors.HexColor("#BCC7D0"))
    pdf.setLineWidth(1)
    pdf.line(46, 690, page_width - 46, 690)

    # Customer and invoice metadata.
    pdf.setFillColor(MUTED)
    pdf.setFont(bold, 9)
    pdf.drawString(46, 664, "BILL TO")
    pdf.setFillColor(INK)
    pdf.setFont(bold, 12)
    pdf.drawString(46, 644, "MERIDIAN ROBOTICS INDIA PRIVATE LIMITED")
    pdf.setFont(regular, 9.5)
    pdf.drawString(46, 627, "4th Floor, Tech Park, Bengaluru, Karnataka 560066")
    pdf.drawString(46, 612, "GSTIN: 29AABCM9152R1Z4")

    pdf.setFillColor(PALE)
    pdf.roundRect(356, 590, 210, 78, 6, fill=1, stroke=0)
    meta = [
        ("Invoice Number", "SA-2026-417"),
        ("Invoice Date", "20 Nov 2026"),
        ("Due Date", "20 Dec 2026"),
    ]
    for y, (label, value) in zip((644, 624, 604), meta):
        pdf.setFillColor(MUTED)
        pdf.setFont(bold, 9.5)
        pdf.drawString(369, y, label)
        pdf.setFillColor(INK)
        pdf.setFont(bold, 9.5)
        pdf.drawRightString(552, y, value)

    # Item table.
    table_left, table_right = 46, page_width - 46
    pdf.setFillColor(NAVY)
    pdf.roundRect(table_left, 548, table_right - table_left, 28, 4, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont(bold, 9)
    pdf.drawString(58, 558, "DESCRIPTION")
    pdf.drawRightString(372, 558, "QTY")
    pdf.drawRightString(465, 558, "UNIT PRICE (INR)")
    pdf.drawRightString(554, 558, "AMOUNT (INR)")

    rows = [
        ("Document AI integration services", "2", "14,000.00", "28,000.00"),
        ("Secure OCR processing credits", "4", "2,300.00", "9,200.00"),
    ]
    for index, row in enumerate(rows):
        y = 519 - index * 35
        pdf.setFillColor(INK)
        pdf.setFont(regular, 10)
        pdf.drawString(58, y, row[0])
        pdf.drawRightString(372, y, row[1])
        pdf.drawRightString(465, y, row[2])
        pdf.drawRightString(554, y, row[3])
        pdf.setStrokeColor(colors.HexColor("#E2E7EB"))
        pdf.line(table_left, y - 12, table_right, y - 12)

    # Totals are deliberately aligned and labeled for OCR.
    summary_x = 352
    summary_y = 412
    summary = [
        ("Subtotal", "INR 37,200.00"),
        ("GST (18%)", "INR 6,696.00"),
    ]
    for index, (label, value) in enumerate(summary):
        y = summary_y - index * 23
        pdf.setFillColor(MUTED)
        pdf.setFont(regular, 10)
        pdf.drawString(summary_x, y, label)
        pdf.setFillColor(INK)
        pdf.drawRightString(table_right - 8, y, value)

    pdf.setFillColor(PALE)
    pdf.roundRect(summary_x - 10, summary_y - 77, table_right - summary_x + 10, 32, 5, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.setFont(bold, 11)
    pdf.drawString(summary_x, summary_y - 66, "GRAND TOTAL INR")
    pdf.drawRightString(table_right - 8, summary_y - 66, "INR 43,896.00")

    pdf.setFillColor(MUTED)
    pdf.setFont(bold, 9)
    pdf.drawString(46, 296, "PAYMENT TERMS")
    pdf.setFillColor(INK)
    pdf.setFont(regular, 9.5)
    pdf.drawString(46, 279, "Net 30 days. Please quote invoice SA-2026-417 with your payment.")
    pdf.drawString(46, 262, "Thank you for choosing Stellar Analytics.")

    pdf.setStrokeColor(colors.HexColor("#BCC7D0"))
    pdf.line(46, 80, page_width - 46, 80)
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 8)
    pdf.drawCentredString(page_width / 2, 62, "Synthetic invoice created for an academic software demonstration.")
    pdf.showPage()
    pdf.save()


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    draw_invoice(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
