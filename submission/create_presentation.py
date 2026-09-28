from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


OUT = Path(__file__).with_name("Phase3_Fraud_Platform_Presentation.pptx")

NAVY = RGBColor(8, 15, 31)
PANEL = RGBColor(17, 29, 53)
WHITE = RGBColor(244, 247, 252)
MUTED = RGBColor(166, 181, 207)
INDIGO = RGBColor(99, 102, 241)
CYAN = RGBColor(34, 211, 238)
GREEN = RGBColor(52, 211, 153)
AMBER = RGBColor(251, 191, 36)
RED = RGBColor(248, 113, 113)


def textbox(slide, text, x, y, w, h, size=20, color=WHITE, bold=False,
            align=PP_ALIGN.LEFT, font="Aptos", valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def panel(slide, x, y, w, h, fill=PANEL, line=None, radius=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    return shape


def base(slide, number, section="PHASE 3 CORNERSTONE PROJECT"):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = NAVY
    slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), Inches(7.5)).fill.solid()
    stripe = slide.shapes[-1]
    stripe.fill.fore_color.rgb = INDIGO
    stripe.line.fill.background()
    textbox(slide, section, 0.55, 0.25, 8, 0.25, 9, CYAN, True)
    textbox(slide, f"{number:02d}", 12.25, 7.05, 0.6, 0.25, 10, MUTED, True, PP_ALIGN.RIGHT)


def title(slide, heading, subheading=None):
    textbox(slide, heading, 0.65, 0.8, 11.8, 0.7, 29, WHITE, True)
    if subheading:
        textbox(slide, subheading, 0.68, 1.55, 11.4, 0.5, 15, MUTED)


def bullet_list(slide, items, x, y, w, h, size=17, color=WHITE, accent=CYAN):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(12)
        # The default PowerPoint bullet formatting is sufficient here; keeping
        # the text as a normal paragraph also avoids version-specific XML APIs.
    return box


def add_slide(prs, heading, subheading=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    base(slide, len(prs.slides))
    title(slide, heading, subheading)
    return slide


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# 1
s = prs.slides.add_slide(prs.slide_layouts[6])
base(s, 1, "IBM CAPSTONE • TEAM 8")
textbox(s, "Real-Time Financial Fraud\nDetection & Curtailment", 0.7, 1.25, 8.4, 1.6, 34, WHITE, True)
textbox(s, "A three-track fintech control center for scoring, investigation, and action", 0.75, 3.15, 8.4, 0.55, 18, MUTED)
panel(s, 9.55, 1.25, 2.7, 3.8, PANEL)
textbox(s, "LIVE DEMO", 9.9, 1.65, 2.0, 0.3, 11, CYAN, True, PP_ALIGN.CENTER)
textbox(s, "DS\n+\nBI\n+\nPRODUCT", 9.9, 2.15, 2.0, 2.2, 24, WHITE, True, PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
textbox(s, "Fintech / banking fraud prevention", 0.75, 6.35, 6.5, 0.3, 13, GREEN, True)

# 2
s = add_slide(prs, "The operational problem", "Fraud response must be fast, contextual, and auditable.")
for x, head, body, col in [(0.75, "SCORE", "Detect anomalous velocity, geography, spend, IP, and device patterns.", CYAN),
                           (4.5, "INVESTIGATE", "Connect a flagged transaction to KYC/SAR-style case evidence.", AMBER),
                           (8.25, "ACT", "Apply a policy decision, dispatch mitigations, and preserve evidence.", GREEN)]:
    panel(s, x, 2.4, 3.25, 2.6)
    textbox(s, head, x + 0.25, 2.75, 2.7, 0.3, 13, col, True)
    textbox(s, body, x + 0.25, 3.25, 2.75, 1.25, 17, WHITE)

# 3
s = add_slide(prs, "Sector and audience choices", "A focused build for internal fraud operations.")
panel(s, 0.75, 2.2, 5.7, 3.5)
textbox(s, "SECTOR", 1.1, 2.65, 2.0, 0.3, 12, CYAN, True)
textbox(s, "Fintech / banking fraud prevention", 1.1, 3.1, 4.8, 0.7, 25, WHITE, True)
textbox(s, "Audience features", 6.85, 2.65, 3.0, 0.3, 12, GREEN, True)
bullet_list(s, ["Internal risk and case investigation", "Automated transaction protection", "Human-in-the-loop override and audit"], 6.85, 3.1, 5.5, 2.3, 18)

# 4
s = add_slide(prs, "End-to-end architecture", "One reviewer-friendly URL, three cooperating tracks.")
steps = [("01", "Transaction", "Raw payment payload", CYAN), ("02", "Data Science", "Probability + flag", INDIGO), ("03", "BI", "Cases + signals", AMBER), ("04", "Product", "Decision + dispatch", GREEN), ("05", "Audit", "Evidence + override", RED)]
for i, (num, head, body, col) in enumerate(steps):
    x = 0.65 + i * 2.5
    panel(s, x, 2.45, 2.15, 2.25)
    textbox(s, num, x + 0.2, 2.75, 0.5, 0.3, 12, col, True)
    textbox(s, head, x + 0.2, 3.25, 1.75, 0.35, 17, WHITE, True)
    textbox(s, body, x + 0.2, 3.85, 1.75, 0.55, 13, MUTED)
    if i < 4:
        textbox(s, "→", x + 2.2, 3.35, 0.35, 0.4, 22, col, True, PP_ALIGN.CENTER)

# 5
s = add_slide(prs, "Data Science track", "Real-time feature engineering turns a stateless payload into context.")
panel(s, 0.75, 2.15, 5.2, 3.9)
textbox(s, "POST /predict", 1.1, 2.55, 3.0, 0.35, 15, CYAN, True)
bullet_list(s, ["Haversine distance and physical velocity", "Rolling 1-hour / 24-hour activity", "Spend ratio and country change", "Shared IP and device clustering", "HistGradientBoostingClassifier"], 1.1, 3.1, 4.3, 2.3, 16)
panel(s, 6.45, 2.15, 5.55, 3.9, RGBColor(24, 39, 72))
textbox(s, "OUTPUT", 6.85, 2.55, 2.0, 0.3, 12, GREEN, True)
textbox(s, "fraud_probability", 6.85, 3.1, 3.8, 0.45, 22, WHITE, True)
textbox(s, "flagged", 6.85, 3.85, 3.8, 0.45, 22, WHITE, True)
textbox(s, "Threshold: ≥ 90%", 6.85, 4.65, 3.8, 0.35, 16, AMBER, True)

# 6
s = add_slide(prs, "Business Intelligence track", "A flag becomes an investigation, not just a number.")
panel(s, 0.75, 2.2, 11.55, 3.7)
textbox(s, "POST /investigate", 1.1, 2.65, 3.0, 0.3, 15, AMBER, True)
for i, (head, body) in enumerate([("SEARCH", "Customer/device keyed case retrieval"), ("TAG", "Distress vs mule-ring language"), ("ENRICH", "Matched case evidence for review")]):
    x = 1.1 + i * 3.65
    textbox(s, head, x, 3.35, 2.4, 0.3, 13, AMBER, True)
    textbox(s, body, x, 3.85, 2.7, 0.9, 18, WHITE)
    if i < 2:
        textbox(s, "→", x + 2.85, 3.55, 0.4, 0.4, 22, MUTED, True, PP_ALIGN.CENTER)
textbox(s, "Sample cases: CUST1042 and CUST2077", 1.1, 5.2, 5.0, 0.3, 14, MUTED)

# 7
s = add_slide(prs, "Product decision and control", "Translate risk into a business action with an audit trail.")
rows = [("< 70%", "AUTO_APPROVE", GREEN), ("70–90%", "STEP_UP_MFA", AMBER), ("≥ 90% + distress", "BLOCK_TRANSACTION", RED), ("≥ 90% + mule signals", "FREEZE_ACCOUNT", INDIGO)]
for i, (risk, action, col) in enumerate(rows):
    y = 2.1 + i * 0.82
    panel(s, 0.9, y, 5.0, 0.6, RGBColor(20, 33, 60))
    textbox(s, risk, 1.15, y + 0.14, 1.3, 0.25, 14, MUTED, True)
    textbox(s, action, 2.65, y + 0.14, 2.9, 0.25, 15, col, True)
    textbox(s, "→", 6.25, y + 0.12, 0.35, 0.3, 18, col, True, PP_ALIGN.CENTER)
    textbox(s, ["Settlement", "Biometric / OTP", "Gateway decline + support", "Core banking freeze + SAR"][i], 6.8, y + 0.14, 4.7, 0.25, 15, WHITE)
panel(s, 0.9, 5.65, 10.7, 0.55, RGBColor(24, 39, 72))
textbox(s, "Every event is persisted; investigators can override with notes.", 1.2, 5.8, 9.8, 0.25, 15, WHITE, True)

# 8
s = add_slide(prs, "Live walkthrough", "Normal payment → suspicious case → investigator override.")
for i, (t, b, col) in enumerate([("1. Approve", "POST /curtail\nLow-risk transaction", GREEN), ("2. Investigate", "Open dashboard\nReview score + cases", AMBER), ("3. Override", "POST /override\nWrite audit note", CYAN)]):
    x = 0.85 + i * 4.05
    panel(s, x, 2.25, 3.45, 2.8)
    textbox(s, t, x + 0.3, 2.7, 2.8, 0.35, 20, col, True)
    textbox(s, b, x + 0.3, 3.45, 2.8, 1.0, 18, WHITE)

# 9
s = add_slide(prs, "Deployment and IBM integration", "OpenShift-ready with a Watson Orchestrate skill contract.")
panel(s, 0.8, 2.15, 5.35, 3.7)
textbox(s, "TECHZONE / OPENSHIFT", 1.15, 2.55, 4.0, 0.3, 12, CYAN, True)
bullet_list(s, ["Containerized single-port gateway", "Route + readiness/liveness probes", "Live control hub, dashboard, Swagger", "Health endpoint for operations"], 1.15, 3.05, 4.3, 2.1, 16)
panel(s, 6.55, 2.15, 5.35, 3.7)
textbox(s, "WATSON ORCHESTRATE", 6.9, 2.55, 4.0, 0.3, 12, GREEN, True)
textbox(s, "OpenAPI 3 skill", 6.9, 3.2, 4.2, 0.45, 23, WHITE, True)
textbox(s, "GET /orchestrate-skill.json", 6.9, 4.05, 4.4, 0.35, 15, CYAN, True)
textbox(s, "Catalog-ready contract for the action workflow", 6.9, 4.75, 4.4, 0.55, 15, MUTED)

# 10
s = add_slide(prs, "Results and next steps", "A working foundation for controlled fraud response.")
panel(s, 0.8, 2.15, 5.1, 3.8)
textbox(s, "VERIFIED", 1.15, 2.55, 2.0, 0.3, 12, GREEN, True)
bullet_list(s, ["Unified gateway suite passed", "All 8 integration checks passed", "Live TechZone control hub responding", "Submission pack mapped to rubric"], 1.15, 3.05, 4.2, 2.1, 17)
panel(s, 6.35, 2.15, 5.55, 3.8)
textbox(s, "NEXT", 6.7, 2.55, 2.0, 0.3, 12, AMBER, True)
bullet_list(s, ["Register the skill in Watson Orchestrate", "Connect approved banking webhooks", "Add role-based access control", "Move audit storage to managed persistence"], 6.7, 3.05, 4.6, 2.1, 17)
textbox(s, "Live demo: fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com", 0.85, 6.45, 11.2, 0.3, 10, MUTED)

prs.save(OUT)
print(OUT)
