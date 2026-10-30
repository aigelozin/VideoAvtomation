#!/bin/bash
# Превью 1280x720 с названием. Аргументы: STEM VIDEO "НАЗВАНИЕ"
BASE="$HOME/VideoAutomation"; STEM="$1"; VIDEO="$2"; TITLE="$3"
FONT=$(fc-match -f '%{file}' 'DejaVu Sans:bold' 2>/dev/null); [ -f "$FONT" ] || FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$VIDEO" 2>/dev/null | cut -d. -f1)
[ -z "$DUR" ] && DUR=60
TS=$(( DUR / 10 )); [ "$TS" -lt 5 ] && TS=5; [ "$TS" -gt 60 ] && TS=60
TXT="$BASE/descriptions/$STEM.title.txt"
python3 -c "import textwrap,sys; print(chr(10).join(textwrap.wrap(sys.argv[1].strip(), width=24)))" "$TITLE" > "$TXT"
ffmpeg -ss "$TS" -i "$VIDEO" -frames:v 1 -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,drawbox=x=0:y=470:w=1280:h=250:color=black@0.55:t=fill,drawtext=fontfile=$FONT:textfile=$TXT:fontcolor=white:fontsize=56:line_spacing=8:x=(w-text_w)/2:y=720-text_h-36:shadowcolor=black@0.8:shadowx=3:shadowy=3" -q:v 2 "$BASE/thumbnails/$STEM.jpg" -y -loglevel error
