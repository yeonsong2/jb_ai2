from io import BytesIO
from textwrap import wrap


def _load_reportlab():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        font_name = "HYSMyeongJo-Medium"
    except Exception:
        font_name = "Helvetica"
    return {
        "colors": colors,
        "A4": A4,
        "mm": mm,
        "getSampleStyleSheet": getSampleStyleSheet,
        "ParagraphStyle": ParagraphStyle,
        "TA_LEFT": TA_LEFT,
        "Paragraph": Paragraph,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
        "font_name": font_name,
    }


def _build_pdf(title: str, sections: list[tuple[str, str]], tables: list[tuple[str, list[list[str]]]] | None = None) -> bytes:
    rl = _load_reportlab()
    buffer = BytesIO()
    doc = rl["SimpleDocTemplate"](buffer, pagesize=rl["A4"], leftMargin=16 * rl["mm"], rightMargin=16 * rl["mm"], topMargin=14 * rl["mm"], bottomMargin=14 * rl["mm"])
    styles = rl["getSampleStyleSheet"]()
    title_style = rl["ParagraphStyle"]("TitleKo", parent=styles["Title"], fontName=rl["font_name"], fontSize=18, leading=22, alignment=rl["TA_LEFT"])
    header_style = rl["ParagraphStyle"]("HeaderKo", parent=styles["Heading2"], fontName=rl["font_name"], fontSize=12, leading=16)
    body_style = rl["ParagraphStyle"]("BodyKo", parent=styles["BodyText"], fontName=rl["font_name"], fontSize=9.5, leading=14)

    story = [rl["Paragraph"](title, title_style), rl["Spacer"](1, 6 * rl["mm"])]
    for heading, content in sections:
        story.append(rl["Paragraph"](heading, header_style))
        for line in content.split("\n"):
            safe_line = line if line.strip() else " "
            story.append(rl["Paragraph"](safe_line.replace("  ", " &nbsp;"), body_style))
        story.append(rl["Spacer"](1, 4 * rl["mm"]))

    for table_title, rows in tables or []:
        story.append(rl["Paragraph"](table_title, header_style))
        table = rl["Table"](rows, repeatRows=1)
        table.setStyle(
            rl["TableStyle"]([
                ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#dbeafe")),
                ("TEXTCOLOR", (0, 0), (-1, -1), rl["colors"].black),
                ("FONTNAME", (0, 0), (-1, -1), rl["font_name"]),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.4, rl["colors"].HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl["colors"].white, rl["colors"].HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(table)
        story.append(rl["Spacer"](1, 4 * rl["mm"]))

    doc.build(story)
    return buffer.getvalue()


def _truncate_rows(df, limit: int = 8):
    rows = [list(df.columns)]
    for _, row in df.head(limit).iterrows():
        rows.append([str(value) for value in row.tolist()])
    return rows


def build_company_report_pdf(company_name: str, latest_month: str, snapshot: dict, portfolio_summary: dict, report_text: str, action_item_df) -> bytes:
    sections = [
        ("기본 요약", f"기준월: {latest_month}\n회사: {company_name}\n현재 연체율: {snapshot['current_rate']:.2f}%\n전월 대비: {snapshot['mom_change_pp']:+.2f}%p\n3개월 평균 대비: {snapshot['vs_3m_avg_pp']:+.2f}%p"),
        ("포트폴리오 구조", f"PF/프로젝트금융 비중: {portfolio_summary['pf_share']}%\n담보 기반 익스포저 비중: {portfolio_summary['secured_share']}%\n최대 익스포저 세그먼트: {portfolio_summary['largest_balance_segment']}\n집중 관리 세그먼트: {portfolio_summary['worst_segment']}"),
        ("임원 보고서", report_text),
    ]
    tables = []
    if action_item_df is not None and len(action_item_df) > 0:
        tables.append(("대응 일정 및 담당", _truncate_rows(action_item_df[[col for col in action_item_df.columns[:4]]], limit=8)))
    return _build_pdf(f"{company_name} 기업금융 리스크 보고서", sections, tables)


def build_group_brief_pdf(latest_month: str, executive_report: str, comparison_df, alerts_df) -> bytes:
    sections = [("그룹 리스크 브리프", executive_report)]
    tables = []
    if comparison_df is not None and len(comparison_df) > 0:
        tables.append(("계열사 비교 요약", _truncate_rows(comparison_df, limit=6)))
    if alerts_df is not None and len(alerts_df) > 0:
        tables.append(("주요 경보", _truncate_rows(alerts_df[["company_name", "alert_type", "severity", "detail"]], limit=8)))
    return _build_pdf(f"{latest_month} 그룹 리스크 브리프", sections, tables)
