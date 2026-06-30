git checkout --orphan hf-deploy
git rm -rf .
@"
---
title: FineMargins
emoji: ⚽
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app/Home.py
pinned: false
---
"@ | Out-File -Encoding utf8 README.md
git add README.md
git checkout main -- app contracts.py data ibm_layer pipeline Dockerfile Procfile requirements.txt runtime.txt .env.example .gitignore .streamlit
git add -A
git commit -m "deploy: sync to HF"
git push hf hf-deploy:main --force
git checkout main
git branch -D hf-deploy
