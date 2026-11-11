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
    {"kind": "bullets", "title": "Why hypergraphs",
     "bullets": [
         "A graph edge joins two nodes; a hyperedge joins any number of nodes.",
         "A class of 8 children in contact is one hyperedge of size 8, not 28 pairs.",
         "Flattening to pairs loses the fact that the pairs came from one event.",
         "It also over-counts big groups: size s becomes s(s-1)/2 pairs."]},
    {"kind": "bullets", "title": "Communities, partitions and covers",
     "bullets": [
         "A community is a set of nodes with many connections inside and few outside.",
         "A partition puts every node in exactly one community.",
         "A cover lets communities overlap and lets some nodes be in none.",
         "Percolation methods return covers."]},
    {"kind": "bullets", "title": "Clique percolation (Palla et al. 2005)",
     "bullets": [
         "A k-clique is k nodes that are all connected to each other.",
         "Two k-cliques are adjacent if they share k-1 nodes.",
         "A community is a chain of adjacent k-cliques.",
         "Communities can overlap.",
         "Nodes in no k-clique are left out."]},
    {"kind": "bullets", "title": "The paper's idea",
     "bullets": [
         "Run percolation directly on hyperedges, not on cliques of the flattened graph.",
         "Two hyperedges are adjacent if they share enough nodes.",
         "A community is everything reachable through a chain of adjacent hyperedges."]},
    {"kind": "bullets", "title": "Variant 1: large hyperedges carry the structure",
     "bullets": [
         "Keep only hyperedges with at least k nodes.",
         "Two are adjacent if they share at least I_abs nodes, with I_abs from 1 to k-1.",
         "I_abs = k-1 is the classical clique percolation rule.",
         "Suits data with many tiny, noisy edges."]},
    {"kind": "bullets", "title": "Variant 2: small hyperedges carry the structure",
     "bullets": [
         "Keep only hyperedges with at most K nodes.",
         "A hyperedge of size S joins a community if at least floor(I_rel * S) of its nodes are already in it.",
         "I_rel lies between 0.5 and 1.",
         "Suits data where huge hyperedges are weak ties, like an assembly."]},
    {"kind": "bullets", "title": "How the paper tests it",
     "bullets": [
         "Random modular hypergraphs: 500 nodes in 10 planted communities.",
         "Community hyperedges have sizes 6-8 (or 3-5); noise hyperedges have the other sizes, drawn from all nodes, at 0 to 40 percent.",
         "Score is element-centric similarity (ECS) to the planted communities.",
         "The paper averages 100 realisations per cell; we use 30 for percolation and 5 for the clique baseline.",
         "Also a hyperbolic hypergraph model and two real datasets with no ground truth."]},
    {"kind": "bullets", "title": "Element-centric similarity",
     "bullets": [
         "Compares two clusterings node by node.",
         "Works for overlapping communities and unassigned nodes.",
         "1 means the two clusterings are identical.",
         "Unassigned nodes count as their own singleton communities."]},
    {"kind": "bullets", "title": "What the paper leaves open",
     "bullets": [
         "The parameters k, I_abs, K and I_rel are set by hand.",
         "The synthetic test has a clean size cut between community and noise hyperedges, so the right filter is obvious.",
         "The comparison to clique percolation on the projection is shown by example, not measured."]},
    {"kind": "bullets", "title": "What we did",
     "bullets": [
         "Re-implemented both variants and the generator in our own Python package, with tests.",
         "E1: checked against the paper's Figure 1 setting.",
         "E2: measured hyperedge percolation against clique percolation when the size cut is not clean.",
         "E3: proposed a simple label-free rule to pick the parameters.",
         "E4: tried it on real committee data with party labels."]},
    {"kind": "bullets", "title": "Our rule for picking parameters without labels", "pt": 20,
     "bullets": [
         "Sweep the parameters.",
         "Reject settings with fewer than two communities, or where the largest is more than twice the second largest (the clique percolation giant-community rule).",
         "Among the rest, pick the highest concentration score: split each node equally over its communities, sum each community's effective size, then take the sum of squared effective sizes over n squared.",
         "Large but not giant communities score high; many tiny overlapping fragments score low. Ties go to the stricter setting.",
         "If nothing survives, use the paper's default: I_abs = k-1 with k the smallest size of at least 3, or K the largest size with I_rel 0.5.",
         "Our first version picked the highest coverage. It failed because fragmented overlapping covers reach coverage near 1."]},
    {"kind": "figure", "title": "E1 check in the paper's Figure 1 setting",
     "caption": "Large-edge communities (sizes 6-8, noise 3-5). The large-edge variant (left) holds ECS 1.000 up to noise 0.4. The small-edge variant (right) falls to 0.711 at noise 0.1 and 0.424 at 0.4. Noise 0 (top) and 0.4 (bottom). 30 realisations per cell.",
     "file": "e1_check_large.png"},
    {"kind": "figure", "title": "E1 check, continued",
     "caption": "Small-edge communities (sizes 3-5, noise 6-8). The small-edge variant (right) holds ECS 1.000 at every noise level. The large-edge variant (left) falls to 0.400 at noise 0.1 and 0.206 at 0.4. Noise 0 (top) and 0.4 (bottom).",
     "file": "e1_check_small.png"},
    {"kind": "figure", "title": "E2: hyperedge versus clique percolation",
     "caption": "Full size overlap: ECS 0.601 at noise 0.1 for both variants, then 0.238 (large) and 0.248 (small) at noise 0.8. Clique percolation scores 0.101 at noise 0.1 even on the small-community type.",
     "file": "e2_map.png"},
    {"kind": "figure", "title": "E2 coverage",
     "caption": "Coverage stays at 0.983 to 1.000 where ECS collapses. Clique percolation timed out on 1.000 of runs for intra sizes 5-7 and 6-8, and on 0.829 to 0.971 for intra sizes 4-6. In all, 278 of 350 runs timed out.",
     "file": "e2_coverage.png"},
    {"kind": "figure", "title": "Label-free pick versus oracle versus default",
     "caption": "Mean ECS over 1050 hypergraphs per variant. Large: rule 0.555, oracle 0.644, default 0.292. Small: rule 0.586, oracle 0.698, default 0.229.",
     "file": "e3_tuning.png"},
    {"kind": "bullets", "title": "E4: real committee data", "pt": 20,
     "bullets": [
         "House, large variant: no setting passes the giant-community test (each gives one community or a giant one), so the rule falls back to the default. Rule, oracle and default all give ECS 0.501, coverage 1.000.",
         "House, small variant: the rule picks K=12, I_rel 0.5 with 6 communities, coverage 0.156, ECS 0.026. Oracle and default (K=81, 0.5) give one community, ECS 0.501.",
         "Senate, large variant: rule picks k=14, I_abs=10 with 18 communities, ECS 0.488, coverage 1.000. Oracle is one community at ECS 0.500; default gives 2 communities at 0.485.",
         "Senate, small variant: rule ECS 0.194, coverage 0.525, 13 communities. Oracle and default give ECS 0.485, 2 communities, coverage 1.000.",
         "The best ECS comes from one or two communities covering everything. So party labels are a weak test here, and the rule gives no gain."]},
    {"kind": "bullets", "title": "What we found", "pt": 20,
     "bullets": [
         "E1: the matching variant reaches ECS 1.000 at every noise level up to 0.4; the mismatched one falls to 0.206 (large) and 0.424 (small) at noise 0.4.",
         "E2: percolation recovers the planted communities (ECS 0.968 to 1.000) while one hyperedge size is pure. Under full overlap it collapses: ECS 0.601 at noise 0.1, 0.238 (large) and 0.248 (small) at 0.8.",
         "Clique percolation timed out in 278 of 350 runs, on 1.000 of runs for intra sizes 5-7 and 6-8. Where it finishes it scores 1.000 at noise 0 and 0.100 to 0.105 at higher noise.",
         "E3: the rule averages ECS 0.555 (large) and 0.586 (small), against oracle 0.644 and 0.698 and default 0.292 and 0.229. It hits the oracle on 0.466 and 0.554 of hypergraphs."]},
    {"kind": "bullets", "title": "Limits",
     "bullets": [
         "Synthetic communities are disjoint, so overlap is never tested.",
         "Real labels are two parties only.",
         "Percolation leaves nodes unassigned.",
         "Our rule is a heuristic."]},
    {"kind": "bullets", "title": "Conclusion",
     "pt": 20,
     "bullets": [
         "The re-implementation behaves as the paper describes in its Figure 1 setting: each variant reaches ECS 1.000 up to noise 0.4 when its size assumption fits. We did not reproduce the paper's figures.",
         "Identical size ranges break both variants (ECS 0.601 at noise 0.1, 0.238 to 0.248 at 0.8), and clique percolation timed out in 278 of 350 runs.",
         "The rule beats the default (0.555 and 0.586 against 0.292 and 0.229) but trails the oracle (0.644 and 0.698), and on real committees it picks fragmented covers in the small variant."]},
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
