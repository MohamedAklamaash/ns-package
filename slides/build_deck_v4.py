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
OUT = os.path.join(HERE, "hyperedge_percolation_v4.pptx")

# Text inside <<double angle brackets>> is drawn in grey (use it for "to be filled").
# kind: "title" | "bullets" | "figure"
SLIDES = [
    {"kind": "title",
     "title": "Community detection in hypergraphs through hyperedge percolation: a re-implementation and a parameter rule that needs no ground truth",
     "subtitle": "Course project, based on Kovács, Benedek and Palla, Scientific Reports 2025, arXiv:2504.15213",
     "authors": "Mohamed Aklamaash and Luqmaan"},
    {"kind": "bullets", "title": "Hyperedges, not pairs",
     "bullets": [
         "A hyperedge joins any number of nodes at once.",
         "A graph edge joins two nodes.",
         "A size-8 hyperedge, flattened into pairs, becomes 28 pairs.",
         "That over-counts large hyperedges.",
         "It also forgets that the pairs came from one hyperedge."]},
    {"kind": "bullets", "title": "Communities, partitions and covers",
     "bullets": [
         "A community is a set of nodes with many hyperedges inside it and few crossing it.",
         "A partition assigns every node to exactly one community.",
         "A cover allows communities to overlap, and leaves some nodes unassigned.",
         "Percolation returns a cover."]},
    {"kind": "bullets", "title": "Clique percolation in ordinary graphs (Palla 2005)",
     "bullets": [
         "A k-clique is a set of k nodes that are all linked to each other.",
         "Two k-cliques are adjacent if they share k-1 nodes.",
         "Chain adjacent k-cliques: one chain is one community.",
         "Communities may overlap.",
         "Nodes in no k-clique are left unassigned."]},
    {"kind": "bullets", "title": "The paper's idea: chain overlapping hyperedges",
     "bullets": [
         "Start from one hyperedge.",
         "Add any hyperedge that shares enough nodes with the current community.",
         "Repeat until no hyperedge can be added.",
         "The union of their nodes is one community.",
         "Start again from a hyperedge not yet used."]},
    {"kind": "bullets", "title": "Two versions of adjacency",
     "bullets": [
         "Large-edge variant: keep only hyperedges of size at least k.",
         "Two hyperedges are adjacent if they share at least I_abs nodes.",
         "It suits data where large hyperedges carry the community structure.",
         "Small-edge variant: keep only hyperedges of size at most K.",
         "A hyperedge of size S joins if at least floor(I_rel times S) of its nodes are already in the community.",
         "It suits data where very large hyperedges are weak ties."]},
    {"kind": "bullets", "title": "What the paper leaves open",
     "bullets": [
         "Four parameters, k, I_abs, K and I_rel, are set by hand.",
         "Its test has a clean size cut, so the right size filter is obvious."]},
    {"kind": "bullets", "title": "The test bed",
     "bullets": [
         "N = 500 nodes in C = 10 planted communities of 50 nodes.",
         "Intra-community hyperedges: 50 per size per community, nodes drawn from one community.",
         "Random hyperedges: p times 500 per size, nodes drawn from all 500 nodes.",
         "Intra-community sizes 6 to 8 with random sizes 3 to 5, or the mirror; p from 0 to 0.4.",
         "30 realisations per cell (paper: 100)."]},
    {"kind": "bullets", "title": "How we score a result",
     "pt": 20,
     "bullets": [
         "ECS (element-centric similarity) compares the detected cover with the ground-truth partition. 1 means identical; near 0 means unrelated.",
         "For node i in a community of size s, build a vector p_i: alpha/s on each other member, (1 - alpha) + alpha/s on i itself, 0 elsewhere. alpha = 0.9 as in the paper.",
         "ECS = 1 - (1 / (2 alpha n)) times the sum over nodes i of |p_i(truth) - p_i(detected)|, the L1 distance.",
         "So each node asks: are my co-members the same in both? Perfect agreement gives 1; a node left alone scores lowest.",
         "It handles overlap and unassigned nodes, which are scored as singleton communities."]},
    {"kind": "bullets", "title": "What we did",
     "bullets": [
         "Re-implemented both variants and the generator, with tests.",
         "Checked them in the paper's own setting.",
         "Added a rule that picks the parameters without ground truth, and compared it with the oracle and the paper default."]},
    {"kind": "figure", "title": "Check: it works as the paper says",
     "caption": "Intra-community hyperedges size 6 to 8, random size 3 to 5; two of five rows shown. Top row p = 0: both variants 1.000. Bottom row p = 0.4: large-edge variant 1.000, small-edge variant 0.424.",
     "file": "e1_check_large.png"},
    {"kind": "figure", "title": "Check: the mirror case",
     "caption": "Intra-community hyperedges size 3 to 5, random size 6 to 8; two of five rows shown. Top row p = 0: both variants 1.000. Bottom row p = 0.4: small-edge variant 1.000, large-edge variant 0.206.",
     "file": "e1_check_small.png"},
    {"kind": "bullets", "title": "Our rule for picking parameters without ground truth", "pt": 20,
     "bullets": [
         "Sweep the parameters.",
         "Discard settings with fewer than two communities, or where the largest community is more than twice the second (one community absorbs the rest).",
         "Among the rest, pick the setting whose communities are large but not giant.",
         "Concentration score: split each node equally across its communities, sum the squared community sizes, divide by n squared.",
         "Ties go to the stricter setting. If nothing survives, use the paper default.",
         "Oracle: parameters chosen using the ground truth, an upper bound. Default: the paper's fixed recipe. Rule: chosen from the detected cover alone."]},
    {"kind": "figure", "title": "The rule against the oracle and the default",
     "caption": "Mean ECS over 1050 hypergraphs per variant. Large-edge: rule 0.555, oracle 0.644, default 0.292. Small-edge: rule 0.586, oracle 0.698, default 0.229. The rule reaches the oracle on 46.6 and 55.4 percent of hypergraphs.",
     "file": os.path.join(HERE, "figures", "rule_slide.png")},
    {"kind": "bullets", "title": "What we found", "pt": 20,
     "bullets": [
         "In the paper's setting, the matching variant scores 1.000 at every p up to 0.4; the wrong variant falls to 0.206 or 0.424.",
         "The parameter rule beats the paper default by a wide margin but stays below the oracle."]},
    {"kind": "bullets", "title": "Limits",
     "bullets": [
         "Planted communities do not overlap, so overlap is never tested.",
         "Percolation leaves nodes unassigned.",
         "The rule is a heuristic, and its giant-community test assumes communities of similar size.",
         "The rule trails the oracle."]},
    {"kind": "bullets", "title": "Conclusion",
     "pt": 20,
     "bullets": [
         "Our code does what the paper says: each variant scores 1.000 up to p = 0.4 when its size assumption fits.",
         "Our rule needs no ground truth and beats the paper default (0.555 and 0.586 against 0.292 and 0.229), but stays below the oracle (0.644 and 0.698)."]},
    {"kind": "bullets", "title": "References",
     "pt": 18,
     "bullets": [
         "B. Kovacs, B. Benedek, G. Palla. Community detection in hypergraphs through hyperedge percolation. Scientific Reports 15, 36032 (2025). arXiv:2504.15213.",
         "G. Palla, I. Derenyi, I. Farkas, T. Vicsek. Uncovering the overlapping community structure of complex networks in nature and society. Nature 435, 814 (2005).",
         "A. J. Gates, I. B. Wood, W. P. Hetrick, Y.-Y. Ahn. Element-centric clustering comparison unifies overlaps and hierarchy. Scientific Reports 9, 8574 (2019).",
         "F. Battiston et al. Networks beyond pairwise interactions: structure and dynamics. Physics Reports 874, 1 (2020).",
         "Code and results: the hypernet package, Mohamed Aklamaash and Luqmaan, 2026."]},
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
