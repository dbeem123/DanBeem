"""Re-OCR one PDF page: remove table rules, OCR to TSV, rebuild a pdftotext -layout style text page."""
import sys, subprocess, tempfile, os, csv, io
import cv2, numpy as np

COLS = 200  # characters across the page width
import re
NUMLIKE = re.compile(r'^[\$(\-]?[\d,.]+\)?$')


def render(pdf, page, dpi=300):
    d = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-gray", pdf, f"{d}/p"], check=True)
    f = os.path.join(d, os.listdir(d)[0])
    img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    os.remove(f); os.rmdir(d)
    return img


def osd_rotate(img):
    ok, buf = cv2.imencode(".png", img)
    r = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "0"], input=buf.tobytes(), capture_output=True)
    rot = 0
    for ln in r.stdout.decode(errors="replace").splitlines():
        if ln.startswith("Rotate:"):
            rot = int(ln.split()[1])
    if rot == 90:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rot == 180:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rot == 270:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def clean(img):
    bw = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 15)
    h, w = bw.shape
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, w // 30), 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, h // 40)))
    lines = cv2.dilate(cv2.morphologyEx(bw, cv2.MORPH_OPEN, hk) | cv2.morphologyEx(bw, cv2.MORPH_OPEN, vk),
                       np.ones((3, 3), np.uint8))
    bw = bw & ~lines
    return 255 - bw


def ocr_layout(img):
    ok, buf = cv2.imencode(".png", img)
    r = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "6", "-c", "preserve_interword_spaces=1", "tsv"],
                       input=buf.tobytes(), capture_output=True, env=dict(os.environ, OMP_THREAD_LIMIT="1"))
    rows = list(csv.DictReader(io.StringIO(r.stdout.decode(errors="replace")), delimiter="\t", quoting=csv.QUOTE_NONE))
    W = img.shape[1]
    words = []
    for x in rows:
        t = (x.get("text") or "").strip()
        if x.get("level") != "5" or not t:
            continue
        words.append((int(x["block_num"]), int(x["par_num"]), int(x["line_num"]), int(x["left"]), int(x["top"]),
                      int(x["width"]), int(x["height"]), t))
    # group by tesseract line id, then order lines by vertical position
    lines = {}
    for b, p, l, left, top, wd, ht, t in words:
        lines.setdefault((b, p, l), []).append((left, top, wd, t))
    out = []
    for key, ws in sorted(lines.items(), key=lambda kv: min(w[1] for w in kv[1])):
        ws.sort()
        s, prev_end, cw = "", None, None
        for left, top, wd, t in ws:
            col = int(round(left / W * COLS))
            w_cw = wd / max(1, len(t))  # this word's pixel width per character
            gap = None if prev_end is None else left - prev_end
            if gap is not None and gap < 1.6 * max(cw or 0, w_cw) and not NUMLIKE.match(t):
                s += " "  # same phrase: words close together on the page
            elif len(s) >= col:
                s += " "
            else:
                s = s.ljust(col)
            s += t
            prev_end, cw = left + wd, w_cw
        out.append(s)
    return "\n".join(out)


if __name__ == "__main__":
    pdf, page = sys.argv[1], int(sys.argv[2])
    print(ocr_layout(clean(osd_rotate(render(pdf, page)))))
