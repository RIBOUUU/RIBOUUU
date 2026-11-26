#!/bin/sh
# Assemble frames/ + audio.wav + texte d'accroche -> ../spirale.mp4
set -e
cd "$(dirname "$0")"
FONT=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
TXT="fontfile=$FONT:fontsize=58:fontcolor=white:shadowcolor=black@0.55:shadowx=3:shadowy=3:x=(w-text_w)/2"
ffmpeg -y -framerate 30 -i frames/%04d.jpg -i audio.wav \
  -vf "drawtext=$TXT:textfile=texte1.txt:y=250,drawtext=$TXT:textfile=texte2.txt:y=325" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "${1:-../spirale.mp4}"
