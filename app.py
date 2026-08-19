import streamlit as st
from PIL import Image
import numpy as np
import cv2
import gnubg_nn

# This app is calibrated for the Adikus Backgammon screenshot layout.
# Every uploaded screenshot is analyzed afresh.

X_NORM = [0.055, 0.132, 0.207, 0.280, 0.360, 0.433,
          0.560, 0.637, 0.715, 0.789, 0.865, 0.939]
TOP_Y0 = 0.254
BOTTOM_Y0 = 0.800
STACK_DY = 0.034

TL = [24, 23, 22, 21, 20, 19]
TR = [13, 14, 15, 16, 17, 18]
BL = [12, 11, 10, 9, 8, 7]
BR = [6, 5, 4, 3, 2, 1]

def classify(bgr):
    b, g, r = map(float, bgr)
    mean = (b + g + r) / 3
    spread = max(b, g, r) - min(b, g, r)
    if mean > 180 and spread < 22:
        return "W"
    if mean < 45 and spread < 22:
        return "B"
    return "."

def stack(img, x, y0, direction, max_n=15):
    h, w = img.shape[:2]
    step = STACK_DY * h
    vals = []
    for i in range(max_n):
        y = int(round(y0 + direction * i * step))
        if y < 0 or y >= h:
            break
        vals.append(classify(img[y, x]))
    color = None
    n = 0
    for v in vals:
        if v == ".":
            break
        if color is None:
            color = v
        if v != color:
            break
        n += 1
    return color or ".", n

def detect_board(image):
    rgb = np.asarray(image.convert("RGB"))
    img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    xs = [int(round(x*w)) for x in X_NORM]
    white = [0]*25
    black = [0]*25

    def put(p, c, n):
        if c == "W": white[p] = n
        if c == "B": black[p] = n

    for i, x in enumerate(xs[:6]):
        c,n = stack(img,x,TOP_Y0*h,+1); put(TL[i],c,n)
    for i, x in enumerate(xs[6:]):
        c,n = stack(img,x,TOP_Y0*h,+1); put(TR[i],c,n)
    for i, x in enumerate(xs[:6]):
        c,n = stack(img,x,BOTTOM_Y0*h,-1); put(BL[i],c,n)
    for i, x in enumerate(xs[6:]):
        c,n = stack(img,x,BOTTOM_Y0*h,-1); put(BR[i],c,n)

    return white, black, img

def detect_die(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 105, 255, cv2.THRESH_BINARY_INV)
    n, lab, stats, centers = cv2.connectedComponentsWithStats(th, 8)
    count = 0
    for i in range(1,n):
        area = stats[i, cv2.CC_STAT_AREA]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]
        if 80 <= area <= 500 and 5 <= bw <= 25 and 5 <= bh <= 25:
            count += 1
    return count

def detect_dice(img):
    h,w = img.shape[:2]
    boxes = [(0.615,0.505,0.730,0.565),(0.770,0.505,0.885,0.565)]
    vals=[]
    for x0,y0,x1,y1 in boxes:
        vals.append(detect_die(img[int(y0*h):int(y1*h), int(x0*w):int(x1*w)]))
    return tuple(vals) if all(1 <= v <= 6 for v in vals) else None

def validate(w,b):
    errors=[]
    if sum(w) > 15: errors.append("White checker count exceeds 15.")
    if sum(b) > 15: errors.append("Black checker count exceeds 15.")
    for p in range(1,25):
        if w[p] and b[p]:
            errors.append(f"Point {p} was detected with both colors.")
    return errors

def move_text(m):
    if not m: return "No legal move found."
    out=[]
    for a,z in m:
        out.append(f"{'bar' if a==0 else a}/{'off' if z==0 else z}")
    return ", ".join(out)

st.set_page_config(page_title="Backgammon Analyzer", layout="centered")
st.title("🎲 Backgammon Analyzer")
st.caption("Adikus screenshot → verified position → GNU Backgammon")

file = st.file_uploader("Upload your latest Adikus screenshot", type=["png","jpg","jpeg"])

if file:
    image=Image.open(file).convert("RGB")
    w,b,img=detect_board(image)
    dice=detect_dice(img)
    errors=validate(w,b)

    st.image(image, width="stretch")

    if errors:
        st.error("Position could not be verified.")
        for e in errors: st.write("• "+e)
        st.stop()

    st.success("✓ Position verified")
    st.write(f"Dice: **{dice if dice else 'not detected'}**")

    if not dice:
        c1,c2=st.columns(2)
        with c1: d1=st.number_input("Die 1",1,6,1)
        with c2: d2=st.number_input("Die 2",1,6,1)
        dice=(int(d1),int(d2))

    if st.button("Find strongest move", type="primary", use_container_width=True):
        # X is White/bottom in this app.
        board=[w,b]
        move=gnubg_nn.best_move(board,dice[0],dice[1],n=2,s="X")
        st.success("BEST MOVE")
        st.markdown(f"## {move_text(move)}")
