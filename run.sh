# !/bin/sh

python3 -c 'print("="*32, "python pip requirements install", "="*32)'
pip install -r requirements.txt
python3 -c 'print("="*32, "Done", "="*32)'
python3 -c 'print("="*32, "Docker Image Install", "="*32)'
docker pull handsonsecurity/seed-ubuntu:large
python3 -c 'print("="*32, "Done", "="*32)'
python3 -c 'print("="*32, "Server Start", "="*32)'
python3 app.py