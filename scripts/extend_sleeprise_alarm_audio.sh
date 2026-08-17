#!/usr/bin/env bash
set -euo pipefail
REPO=/home/ubuntu/sleepify-apk-github
RAW="$REPO/android/app/src/main/res/raw"
TMP=/home/ubuntu/sleeprise-alarm-extended-tmp
mkdir -p "$TMP"
# Native Android channel sounds must be named without an extension and are played from res/raw.
for src in "$RAW"/*.mp3; do
  base=$(basename "$src")
  case "$base" in
    phone_alarm.mp3|electronic_buzzer_1.mp3|electronic_buzzer_2.mp3|electronic_buzzer_3.mp3|piezo_alarm_1.mp3|piezo_alarm_3.mp3|buzzer_4.mp3|digital_pager.mp3|alphanumeric_pager.mp3|digital_watch_alarm.mp3|two_tone_siren.mp3|three_tone_siren.mp3|vehicle_siren.mp3|evacuation_alarm_1.mp3|evacuation_alarm_3.mp3|mechanical_clock.mp3|mechanical_clock_tick_5.mp3|mechanical_clock_tick_3.mp3|mechanical_short_ring.mp3|mechanical_doorbell.mp3|industrial_doorbell.mp3|rooster.mp3|barking_dogs.mp3|crow.mp3)
      out="$TMP/$base"
      ffmpeg -hide_banner -loglevel error -y -stream_loop -1 -i "$src" -t 30 -c:a libmp3lame -b:a 128k -ar 44100 "$out"
      mv "$out" "$src"
      ;;
  esac
done
rm -rf "$TMP"
printf 'Extended native alarm audio files:\n'
for f in phone_alarm electronic_buzzer_1 electronic_buzzer_2 electronic_buzzer_3 piezo_alarm_1 piezo_alarm_3 buzzer_4 digital_pager alphanumeric_pager digital_watch_alarm two_tone_siren three_tone_siren vehicle_siren evacuation_alarm_1 evacuation_alarm_3 mechanical_clock mechanical_clock_tick_5 mechanical_clock_tick_3 mechanical_short_ring mechanical_doorbell industrial_doorbell rooster barking_dogs crow; do
  file="$RAW/$f.mp3"
  [ -f "$file" ] && printf '%s ' "$f" && ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$file" | head -n 1
done
