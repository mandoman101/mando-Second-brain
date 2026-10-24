---
date: 2026-10-24
tags:
  - home
aliases:
  - Dashboard
---

# 🧠 Millie (ForgePoints AI Lab)'s Builder Vault

> Claude automatically saves everything important from every conversation.

---

## ⚡ Quick Navigation

[[Boards/Engineering|📋 Engineering]]

📁 Daily · 📁 Projects · 📁 People · 📁 Companies · 📁 Tools · 📁 Dev Logs · 📁 Architecture · 📁 Debugging · 📁 Knowledge · 📁 Tasks · 📁 Ideas

---

## 📅 Recent Daily Notes

```dataview
TABLE WITHOUT ID file.link AS "Day", mood AS "Mood", energy AS "Energy"
FROM "Daily"
SORT date DESC
LIMIT 7
```

---

## 📊 Vault Stats

```dataviewjs
const all = dv.pages("");
dv.paragraph(`📝 **${all.length}** total notes`);
```
