import os
import re
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.normpath(os.path.join(HERE, "..", "results", "figures"))
OUT = os.path.join(HERE, "hyperedge_percolation.pptx")

# Text inside <<double angle brackets>> is drawn in grey (use it for "to be filled").
# kind: "title" | "bullets" | "figure"
SLIDES = [
    {"kind": "title",
     "title": "Community detection in hypergraphs through hyperedge percolation: a re-implementation and a label-free parameter rule",
     "subtitle": "Course project, based on Kovács, Benedek and Palla, Scientific Reports 2025, arXiv:2504.15213",
     "authors": "Mohamed Aklamaash and Luqmaan"},
    {"kind": "bullets", "title": "Groups are meetings, not pairs",
     "bullets": [
         "A hyperedge is one meeting, with everyone who was in it.",
         "A graph edge joins only two people.",
         "A meeting of 8 people, flattened into pairs, becomes 28 pairs.",
         "That over-counts big meetings.",
         "It also forgets the pairs came from one event."]},
    {"kind": "bullets", "title": "Communities, and two ways to assign them",
     "bullets": [
         "A community is a set of people who meet each other a lot.",
         "A partition puts everyone in exactly one community.",
         "A cover lets communities overlap, and lets some people be in none.",
         "Percolation gives a cover."]},
    {"kind": "bullets", "title": "Clique percolation in ordinary graphs (Palla 2005)",
     "bullets": [
         "A k-clique is k people who all know each other.",
         "Two k-cliques are adjacent if they share k-1 people.",
         "Chain adjacent k-cliques: one chain is one community.",
         "Communities may overlap.",
         "People in no k-clique are left out."]},
    {"kind": "bullets", "title": "The paper's idea: chain meetings that overlap",
     "bullets": [
         "Start from one meeting.",
         "Add any other meeting that overlaps it enough.",
         "Keep adding any meeting that overlaps the growing pile enough.",
         "When nothing more can join, the people in the pile are one community.",
         "Start again from a meeting not yet used."]},
    {"kind": "bullets", "title": "Two versions of \"overlaps enough\"",
     "bullets": [
         "Large-edge variant: count only meetings with at least k people.",
         "Two meetings connect if they share at least I_abs people.",
         "Use it when big meetings are the real groups and tiny ones are chatter.",
         "Small-edge variant: count only meetings with at most K people.",
         "A meeting joins the pile if at least a fraction I_rel of its people are already in it.",
         "Use it when huge meetings, like an assembly, mean nothing."]},
    {"kind": "bullets", "title": "What the paper leaves open",
     "bullets": [
         "Four parameters, k, I_abs, K and I_rel, are set by hand.",
         "Its test has a clean size cut, so the right filter is obvious.",
         "The comparison with clique percolation is by picture only."]},
    {"kind": "bullets", "title": "The test bed",
     "bullets": [
         "500 people in 10 planted groups of 50.",
         "Community meetings draw from one group: 50 per size per group.",
         "Noise meetings draw from all 500 people: p times 500 per size.",
         "Community sizes 6 to 8 with noise 3 to 5, or the mirror.",
         "Noise p runs from 0 to 0.4.",
         "The paper averages 100 runs; we use 30."]},
    {"kind": "bullets", "title": "How we score a result",
     "bullets": [
         "ECS compares the found grouping with the planted one.",
         "1 means identical; near 0 means unrelated.",
         "For each person, compare who they are grouped with in both.",
         "It works with overlap and left-out people, who count as a group of one.",
         "Coverage is the share of people placed in any group."]},
    {"kind": "bullets", "title": "What we did",
     "bullets": [
         "Re-implemented both variants and the generator, with tests.",
         "E1: checked them in the paper's setting.",
         "E3: added a rule that picks the parameters without labels, and compared it with the oracle and the default.",
         "Two more studies are in the backup slides: unclean size cuts (E2) and real committee data (E4)."]},
    {"kind": "figure", "title": "E1: it works exactly as the paper says",
     "caption": "Large-edge communities (sizes 6 to 8, noise 3 to 5). The large-edge variant holds ECS 1.000 up to noise 0.4. The small-edge variant falls to 0.711 at noise 0.1 and 0.424 at 0.4. Top row noise 0, bottom row noise 0.4.",
     "file": "e1_check_large.png"},
    {"kind": "figure", "title": "E1, the mirror case",
     "caption": "Small-edge communities (sizes 3 to 5, noise 6 to 8). The small-edge variant stays at 1.000. The large-edge variant falls to 0.400 at noise 0.1 and 0.206 at 0.4. Top row noise 0, bottom row noise 0.4.",
     "file": "e1_check_small.png"},
    {"kind": "bullets", "title": "Our rule for picking parameters without labels", "pt": 20,
     "bullets": [
         "Sweep the parameters.",
         "Throw out settings with fewer than two groups, or where the largest group is more than twice the second (one group swallows the rest).",
         "Among the rest, pick the setting whose groups are large but not giant.",
         "Concentration score: split each person equally across their groups, sum the squared group sizes, divide by n squared.",
         "Ties go to the stricter setting. If nothing survives, use the paper default.",
         "Our first version picked highest coverage and failed: many tiny overlapping fragments reach coverage near 1."]},
    {"kind": "figure", "title": "E3: the rule against the oracle and the default",
     "caption": "Mean ECS over 1050 hypergraphs per variant. Large-edge: rule 0.555, oracle 0.644, default 0.292. Small-edge: rule 0.586, oracle 0.698, default 0.229. The rule reaches the oracle on 46.6 and 55.4 percent of hypergraphs.",
     "file": "e3_tuning.png"},
    {"kind": "bullets", "title": "What we found", "pt": 20,
     "bullets": [
         "E1: the matching variant scores 1.000 at every noise level up to 0.4; the wrong variant falls to 0.206 or 0.424.",
         "E3: the rule beats the default by a wide margin but stays below the oracle.",
         "Backup: percolation needs at least one pure meeting size. With identical size ranges both variants collapse (0.601 at noise 0.1, about 0.24 at 0.8).",
         "Backup: on committee data the rule gives no gain, and party labels are a weak test."]},
    {"kind": "bullets", "title": "Limits",
     "bullets": [
         "Planted groups do not overlap, so overlap is never tested.",
         "Two-party labels are weak truth.",
         "Percolation leaves people out.",
         "The rule is a heuristic and assumes groups of similar size.",
         "The clique baseline mostly timed out (278 of 350 runs), so it is limited by time, not accuracy."]},
    {"kind": "bullets", "title": "Conclusion",
     "pt": 20,
     "bullets": [
         "Our code does what the paper says: each variant scores 1.000 up to noise 0.4 when its size assumption fits. We did not reproduce the paper's figures.",
         "Our label-free rule beats the paper's default (0.555 and 0.586 against 0.292 and 0.229) but stays below the oracle (0.644 and 0.698).",
         "When community and noise meetings have the same sizes, both variants break; on real committee data the rule does not help."]},
    {"kind": "bullets", "title": "Backup, E2: when the size cut is not clean", "pt": 20,
     "bullets": [
         "Clean cut: community and noise meetings have different sizes, so a size filter removes all noise.",
         "Partial overlap (community 5 to 7, noise 4 to 6): still works, because one pure size remains to filter on. ECS 0.968 to 1.000.",
         "Full overlap (4 to 6 against 4 to 6): size tells nothing, and both variants break.",
         "ECS is 0.601 at noise 0.1, and 0.238 (large-edge) and 0.248 (small-edge) at noise 0.8.",
         "Clique percolation scores 0.101 at noise 0.1, even on the small-community type."]},
    {"kind": "figure", "title": "Backup, E2: hyperedge versus clique percolation",
     "caption": "Full size overlap: ECS 0.601 at noise 0.1 for both variants, then 0.238 (large) and 0.248 (small) at noise 0.8. Clique percolation scores 0.101 at noise 0.1 even on the small-community type. It timed out in 278 of 350 runs.",
     "file": "e2_map.png"},
    {"kind": "bullets", "title": "Backup, E4: real committee data", "pt": 20,
     "bullets": [
         "House, large variant: no setting passes the giant-community test (each gives one community or a giant one), so the rule falls back to the default. Rule, oracle and default all give ECS 0.501, coverage 1.000.",
         "House, small variant: the rule picks K=12, I_rel 0.5 with 6 communities, coverage 0.156, ECS 0.026. Oracle and default (K=81, 0.5) give one community, ECS 0.501.",
         "Senate, large variant: rule picks k=14, I_abs=10 with 18 communities, ECS 0.488, coverage 1.000. Oracle is one community at ECS 0.500; default gives 2 communities at 0.485.",
         "Senate, small variant: rule ECS 0.194, coverage 0.525, 13 communities. Oracle and default give ECS 0.485, 2 communities, coverage 1.000.",
         "The best ECS comes from one or two communities covering everything. So party labels are a weak test here, and the rule gives no gain."]},
]

FONT = "Calibri"
BLACK = RGBColor(0, 0, 0)
GREY = RGBColor(0x80, 0x80, 0x80)
SW, SH = Inches(13.333), Inches(7.5)
MX = Inches(0.8)
BODY_PT, TITLE_PT, NUM_PT = 22, 32, 12


SLIDE_FIG_DIR = os.path.join(HERE, "figures")
E1_FILES = ["e1_check_large.png", "e1_check_small.png"]
GAP_PX = 40


def row_blocks(arr):
    blank = (arr >= 250).all(axis=(1, 2))
    runs, start = [], None
    for i, b in enumerate(blank):
        if not b and start is None:
            start = i
        if b and start is not None:
            runs.append([start, i])
            start = None
    if start is not None:
        runs.append([start, len(blank)])
    runs = [r for r in runs if r[1] - r[0] > 5]
    blocks = [runs[0][:]]
    for r in runs[1:]:
        if r[0] - blocks[-1][1] < 30:
            blocks[-1][1] = r[1]
        else:
            blocks.append(r[:])
    blocks[0][0] = runs[1][0]
    return blocks


def make_e1_slide_images():
    import numpy as np
    from PIL import Image
    os.makedirs(SLIDE_FIG_DIR, exist_ok=True)
    for name in E1_FILES:
        src = os.path.join(FIG_DIR, name)
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert("RGB")
        blocks = row_blocks(np.array(im))
        pad = 8
        rows = [im.crop((0, max(b[0] - pad, 0), im.width, min(b[1] + pad, im.height)))
                for b in (blocks[0], blocks[-1])]
        out = Image.new("RGB", (im.width, rows[0].height + rows[1].height + GAP_PX), "white")
        out.paste(rows[0], (0, 0))
        out.paste(rows[1], (0, rows[0].height + GAP_PX))
        out.save(os.path.join(SLIDE_FIG_DIR, name.replace(".png", "_slide.png")))


def style_run(run, size, color=BLACK, bold=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def add_runs(par, text, size):
    for part in re.split(r"(<<.*?>>)", text):
        if not part:
            continue
        grey = part.startswith("<<")
        run = par.add_run()
        run.text = part[2:-2] if grey else part
        style_run(run, size, GREY if grey else BLACK)


def set_bullet(par):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.35)))
    pPr.set("indent", str(-Inches(0.35)))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", "-")


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    return tb, tf


def add_title(slide, text, x=MX, y=Inches(0.5), w=None, h=Inches(1.2), size=TITLE_PT):
    ph = slide.shapes.title
    ph.left, ph.top, ph.width, ph.height = x, y, w or (SW - 2 * MX), h
    tf = ph.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    style_run(r, size, bold=True)


def add_slide_number(slide):
    tb, tf = textbox(slide, SW - Inches(1.3), SH - Inches(0.6), Inches(0.8), Inches(0.4))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    fld = etree.SubElement(p._p, qn("a:fld"))
    fld.set("id", "{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}")
    fld.set("type", "slidenum")
    rPr = etree.SubElement(fld, qn("a:rPr"))
    rPr.set("lang", "en-US")
    rPr.set("sz", str(NUM_PT * 100))
    fill = etree.SubElement(rPr, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr")).set("val", "808080")
    etree.SubElement(rPr, qn("a:latin")).set("typeface", FONT)
    etree.SubElement(fld, qn("a:t")).text = "‹#›"


def build_title(prs, spec):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    add_title(s, spec["title"], y=Inches(1.3), h=Inches(2.6), size=36)
    tb, tf = textbox(s, MX, Inches(4.2), SW - 2 * MX, Inches(1.0))
    r = tf.paragraphs[0].add_run()
    r.text = spec["subtitle"]
    style_run(r, 20)
    tb, tf = textbox(s, MX, Inches(5.4), SW - 2 * MX, Inches(0.6))
    r = tf.paragraphs[0].add_run()
    r.text = spec["authors"]
    style_run(r, 20)
    add_slide_number(s)


def build_bullets(prs, spec):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    add_title(s, spec["title"])
    size = spec.get("pt", BODY_PT)
    tb, tf = textbox(s, MX, Inches(1.9), SW - 2 * MX, Inches(4.8))
    for i, text in enumerate(spec["bullets"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(12)
        set_bullet(p)
        add_runs(p, text, size)
    add_slide_number(s)


def build_figure(prs, spec):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    add_title(s, spec["title"], y=Inches(0.35), h=Inches(0.6), size=28)
    tb, tf = textbox(s, MX, Inches(1.0), SW - 2 * MX, Inches(0.7))
    add_runs(tf.paragraphs[0], spec["caption"], 18)
    path = os.path.join(FIG_DIR, spec["file"])
    if spec["file"] in E1_FILES:
        alt = os.path.join(SLIDE_FIG_DIR, spec["file"].replace(".png", "_slide.png"))
        if os.path.exists(alt):
            path = alt
    top, bottom = Inches(1.75), SH - Inches(0.6)
    if os.path.exists(path):
        from PIL import Image
        with Image.open(path) as im:
            ratio = im.height / im.width
        w = SW - 2 * MX
        h = int(w * ratio)
        if h > bottom - top:
            h = bottom - top
            w = int(h / ratio)
        s.shapes.add_picture(path, int((SW - w) / 2), top, w, h)
    else:
        tb, tf = textbox(s, MX, Inches(3.2), SW - 2 * MX, Inches(0.6))
        r = tf.paragraphs[0].add_run()
        r.text = "figure pending: " + spec["file"]
        style_run(r, 20, GREY)
    add_slide_number(s)


def main():
    make_e1_slide_images()
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    builders = {"title": build_title, "bullets": build_bullets, "figure": build_figure}
    for spec in SLIDES:
        builders[spec["kind"]](prs, spec)
    prs.save(OUT)
    print("wrote", OUT, len(SLIDES), "slides")


if __name__ == "__main__":
    main()
