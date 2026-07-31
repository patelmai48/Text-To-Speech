import csv
import io
from xml.sax.saxutils import escape as xml_escape
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Characters that spreadsheet apps interpret as formula prefixes
_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def _csv_safe(value):
    """Prefix spreadsheet formula-injection characters with a single quote."""
    s = str(value) if value is not None else ''
    if s and s[0] in _FORMULA_PREFIXES:
        return "'" + s
    return s


class CSVReportGenerator:
    """Service to generate CSV reports for user history."""

    @staticmethod
    def generate(history_records):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Date', 'Voice', 'Language', 'Characters', 'Speed', 'Pitch', 'Volume', 'Text'])

        for item in history_records:
            date_str = item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
            writer.writerow([
                _csv_safe(item.id),
                _csv_safe(date_str),
                _csv_safe(item.voice),
                _csv_safe(item.language),
                _csv_safe(item.character_count),
                _csv_safe(item.speed),
                _csv_safe(item.pitch),
                _csv_safe(item.volume),
                _csv_safe(item.text),
            ])

        output.seek(0)
        return output.getvalue()


class PDFReportGenerator:
    """Service to generate PDF document reports for user history."""

    @staticmethod
    def generate(history_records, username="User"):
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#4f46e5'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=20
        )
        table_text_style = ParagraphStyle(
            'TableText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1f2937')
        )

        safe_username = xml_escape(str(username))
        story.append(Paragraph("VoxAI Studio - Conversion History", title_style))
        story.append(Paragraph(f"Exported Report for User: <b>{safe_username}</b> | Total Records: {len(history_records)}", subtitle_style))
        story.append(Spacer(1, 10))

        data = [["ID", "Date", "Voice", "Chars", "Text Snippet"]]

        for item in history_records:
            date_str = item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else ''
            raw_snippet = item.text[:65] + '...' if len(item.text) > 65 else item.text
            safe_snippet = xml_escape(raw_snippet)
            data.append([
                str(item.id),
                date_str,
                item.voice,
                str(item.character_count),
                Paragraph(safe_snippet, table_text_style)
            ])

        col_widths = [30, 100, 110, 45, 255]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))

        story.append(t)
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer
