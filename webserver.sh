#! /bin/bash
open http://127.0.0.1:8080 &
python -m http.server 8080 --bind 127.0.0.1 --directory "/Seagate Backup Plus Drive/OpenElective"
