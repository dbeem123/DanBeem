"""Re-OCR the form pages the parser needs, for every scanned report. Worker W of N. Resumable per report.
Output: reocr_out/<name>.txt, pages separated by \f; a page that fails re-OCR keeps its first-pass OCR text."""
import sys, os, re, glob, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reocr

ROOT = os.environ.get("COST_REPORT_OCR_ROOT", "/home/claude/cr")  # holds img/ (scanned PDFs) and ocr_full/
NEED = {"2", "3", "3A", "4", "8", "10", "13", "15", "16", "17", "18", "19", "20", "22", "27", "30",
        "31", "32", "33", "34", "35", "36"}
CODE = re.compile(r"\bCSP\s?-\s?(\d{1,2}[A-Za-z]?)\b")
W, N = int(sys.argv[1]), int(sys.argv[2])
os.makedirs(f"{ROOT}/reocr_out", exist_ok=True)
pdfs = sorted(p for p in glob.glob(f"{ROOT}/img/*") if p.lower().endswith(".pdf"))
for k, pdf in enumerate(pdfs):
    if k % N != W:
        continue
    name = os.path.splitext(os.path.basename(pdf))[0]
    out = f"{ROOT}/reocr_out/{name}.txt"
    if os.path.exists(out):
        continue
    src = f"{ROOT}/ocr_full/{name}.txt"
    if not os.path.exists(src):
        continue
    pages = open(src, encoding="utf-8", errors="replace").read().split("\f")
    res, t0, redone = [], time.time(), 0
    for i, p in enumerate(pages):
        m = CODE.search(p[:600])
        if not m or m.group(1).upper() not in NEED:
            continue
        try:
            img = reocr.render(pdf, i + 1)
            txt = reocr.ocr_layout(reocr.clean(img))
            if not CODE.search(txt[:800]):
                txt = reocr.ocr_layout(reocr.clean(reocr.osd_rotate(img)))
            res.append(txt if CODE.search(txt[:800]) else p)
            redone += 1
        except Exception as e:
            res.append(p)
    open(out + ".part", "w", encoding="utf-8").write("\f".join(res))
    os.replace(out + ".part", out)
    with open(f"{ROOT}/reocr_out/_log.txt", "a", encoding="utf-8") as lg:
        lg.write(f"{time.strftime('%T')} w{W} {name} {redone} pages {time.time()-t0:.0f}s\n")
with open(f"{ROOT}/reocr_out/_log.txt", "a", encoding="utf-8") as lg:
    lg.write(f"worker {W} done {time.ctime()}\n")
