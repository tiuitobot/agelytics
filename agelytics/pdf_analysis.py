"""Generate PDF for AI Analysis and Deep Coach reports.

Takes structured analysis text (from LLM) and renders it as a professional PDF
with the Agelytics visual style.

Usage:
    # AI Analysis
    pdf = AnalysisPDF(match, player_name="blzulian", report_type="ai")
    pdf.render_analysis(analysis_text)
    pdf.save("reports/ai_analysis_151.pdf")

    # Deep Coach
    pdf = AnalysisPDF(match, player_name="blzulian", report_type="deep")
    pdf.render_analysis(analysis_text)
    pdf.save("reports/deep_coach_151.pdf")
"""

import os
import re
from datetime import datetime

from fpdf import FPDF

from .pdf_style import COLORS


REPORT_TITLES = {
    "ai": "AI Analysis",
    "deep": "Deep Coach",
}

REPORT_COLORS = {
    "ai": (52, 152, 219),      # Blue
    "deep": (155, 89, 182),     # Purple
}


class AnalysisPDF(FPDF):
    """PDF renderer for LLM-generated analysis text."""

    def __init__(self, match=None, player_name=None, report_type="ai"):
        super().__init__()
        self.match = match or {}
        self.player_name = player_name
        self.report_type = report_type
        self.accent = REPORT_COLORS.get(report_type, (44, 62, 80))
        self.title_text = REPORT_TITLES.get(report_type, "Analysis")

    def header(self):
        # Logo
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(44, 62, 80)
        self.cell(0, 8, "AGELYTICS", 0, 0, "L")

        # Report type badge
        self.set_font("Helvetica", "B", 9)
        badge_w = self.get_string_width(self.title_text) + 8
        badge_x = 200 - badge_w
        self.set_fill_color(*self.accent)
        self.set_text_color(255, 255, 255)
        self.rect(badge_x, self.get_y() + 1, badge_w, 6, "F")
        self.set_xy(badge_x, self.get_y() + 1)
        self.cell(badge_w, 6, self.title_text, 0, 0, "C")
        self.ln(10)

        # Accent line
        self.set_draw_color(*self.accent)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10,
                  f"Agelytics {self.title_text} | Page {self.page_no()} | "
                  f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                  0, 0, "C")

    def _match_header(self):
        """Render match context at top of first page."""
        m = self.match
        players = m.get("players", [])
        if not players:
            return

        focus = next((p for p in players if p["name"] == self.player_name), players[0])
        opp = next((p for p in players if p["name"] != focus["name"]), None)

        # Match title
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(44, 62, 80)
        if opp:
            self.cell(0, 7,
                      f"{focus['name']} ({focus.get('civ_name', '?')}) vs "
                      f"{opp['name']} ({opp.get('civ_name', '?')})",
                      0, 1, "L")
        else:
            self.cell(0, 7, focus["name"], 0, 1, "L")

        # Match details
        self.set_font("Helvetica", "", 9)
        self.set_text_color(127, 140, 141)
        dur_s = m.get("duration_secs", 0)
        dur = f"{int(dur_s)//60}:{int(dur_s)%60:02d}"
        result = "Victory" if focus.get("winner") else "Defeat"
        r_color = COLORS["victory"] if focus.get("winner") else COLORS["defeat"]

        self.cell(0, 5,
                  f"{m.get('played_at', '?')}  |  {m.get('map_name', '?')}  |  {dur}  |  "
                  f"ELO {focus.get('elo', '?')} vs {opp.get('elo', '?') if opp else '?'}",
                  0, 1, "L")

        # Result badge
        self.set_font("Helvetica", "B", 10)
        badge_color = (39, 174, 96) if focus.get("winner") else (192, 57, 43)
        self.set_fill_color(*badge_color)
        self.set_text_color(255, 255, 255)
        badge_w = self.get_string_width(result) + 10
        self.rect(10, self.get_y() + 1, badge_w, 6, "F")
        self.set_xy(10, self.get_y() + 1)
        self.cell(badge_w, 6, result, 0, 1, "C")
        self.ln(5)

        # Separator
        self.set_draw_color(210, 210, 210)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def render_analysis(self, text):
        """Parse markdown-ish analysis text and render as styled PDF.

        Supports:
        - ## Headers → section titles with accent bar
        - **bold** → bold text
        - - bullet items → indented bullets
        - 1. numbered items → numbered list
        - Regular paragraphs → body text
        - Nota: X/10 → highlighted score box
        """
        self.add_page()
        self._match_header()

        lines = text.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                self.ln(2)
                i += 1
                continue

            # H1/H2 Headers
            if line.startswith("## ") or line.startswith("# "):
                title = re.sub(r"^#+\s*", "", line)
                self._render_section(title)
                i += 1
                continue

            # Score line (Nota: X/10)
            score_match = re.search(r"[Nn]ota[:\s]*(\d+(?:[.,]\d+)?)\s*/\s*10", line)
            if score_match:
                score = float(score_match.group(1).replace(",", "."))
                self._render_score(score, line)
                i += 1
                continue

            # Bullet list
            if line.startswith("- ") or line.startswith("• "):
                text_content = line[2:].strip()
                self._render_bullet(text_content)
                i += 1
                continue

            # Numbered list
            num_match = re.match(r"^(\d+)[.)]\s*(.*)", line)
            if num_match:
                num = num_match.group(1)
                text_content = num_match.group(2)
                self._render_numbered(num, text_content)
                i += 1
                continue

            # Regular paragraph
            self._render_paragraph(line)
            i += 1

    def _render_section(self, title):
        """Section header with accent bar."""
        if self.get_y() > 255:
            self.add_page()
        self.ln(3)
        self.set_fill_color(*self.accent)
        self.rect(10, self.get_y(), 3, 8, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.accent)
        self.set_x(16)
        self.cell(0, 8, self._sanitize(title), 0, 1, "L")
        self.ln(2)

    def _render_paragraph(self, text):
        """Body paragraph with bold support."""
        if self.get_y() > 270:
            self.add_page()
        self._write_rich_text(text, indent=10)
        self.ln(3)

    def _render_bullet(self, text):
        """Bullet item."""
        if self.get_y() > 270:
            self.add_page()
        self.set_x(14)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(4, 5, "-", 0, 0)  # bullet
        self._write_rich_text(text, indent=18, size=9)
        self.ln(1.5)

    def _render_numbered(self, num, text):
        """Numbered item."""
        if self.get_y() > 270:
            self.add_page()
        self.set_x(14)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.accent)
        self.cell(6, 5, f"{num}.", 0, 0)
        self._write_rich_text(text, indent=20, size=9)
        self.ln(1.5)

    def _render_score(self, score, full_line):
        """Render a score highlight box."""
        if self.get_y() > 250:
            self.add_page()
        self.ln(3)

        # Score color
        if score >= 8:
            color = (39, 174, 96)   # green
        elif score >= 6:
            color = (243, 156, 18)  # orange
        else:
            color = (192, 57, 43)   # red

        # Score box
        box_w = 50
        box_h = 20
        x = (210 - box_w) / 2
        y = self.get_y()
        self.set_fill_color(*color)
        self.rect(x, y, box_w, box_h, "F")

        self.set_font("Helvetica", "B", 22)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, y + 2)
        self.cell(box_w, 10, f"{score:.1f}/10", 0, 0, "C")

        self.set_font("Helvetica", "", 8)
        self.set_xy(x, y + 12)
        self.cell(box_w, 5, "Match Score", 0, 0, "C")

        self.set_y(y + box_h + 5)

        # Justification text (rest of line after score)
        justification = re.sub(r"[Nn]ota[:\s]*\d+(?:[.,]\d+)?\s*/\s*10\s*[-—]?\s*", "", full_line).strip()
        if justification:
            self._render_paragraph(justification)

    @staticmethod
    def _sanitize(text):
        """Replace non-latin1 chars for Helvetica compat."""
        replacements = {
            "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
            "\u2192": "->", "\u2190": "<-", "\u2715": "x",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Drop remaining non-latin1
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def _write_rich_text(self, text, indent=10, size=10):
        """Write text with **bold** support."""
        text = self._sanitize(text)
        self.set_x(indent)
        parts = re.split(r"(\*\*.*?\*\*)", text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                self.set_font("Helvetica", "B", size)
                self.set_text_color(44, 62, 80)
                self.write(5, part[2:-2])
            else:
                self.set_font("Helvetica", "", size)
                self.set_text_color(60, 60, 60)
                self.write(5, part)
        self.ln()

    def save(self, output_path):
        """Save the PDF."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self.output(output_path)
        return output_path


def generate_ai_analysis_pdf(match, analysis_text, output_path, player_name=None):
    """Convenience function for AI Analysis PDF."""
    pdf = AnalysisPDF(match, player_name=player_name, report_type="ai")
    pdf.render_analysis(analysis_text)
    return pdf.save(output_path)


def generate_deep_coach_pdf(match, analysis_text, output_path, player_name=None):
    """Convenience function for Deep Coach PDF."""
    pdf = AnalysisPDF(match, player_name=player_name, report_type="deep")
    pdf.render_analysis(analysis_text)
    return pdf.save(output_path)
