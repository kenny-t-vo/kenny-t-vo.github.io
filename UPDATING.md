# updating the site

Live at <https://kenny-t-vo.github.io/>. Repo `kenny-t-vo/kenny-t-vo.github.io`;
the name is the hostname, so it cannot be renamed. Local folder
`/Users/kenny/dev/kenny-vo-website`.

Every command below is one paste. Each ends with `git pull --rebase` before the
push, so edits made on github.com do not block it. The rebase has to come after
the commit: git refuses to rebase when the working tree has uncommitted changes,
which it always does once you have edited a source file.

## the books

Re-render a PDF, commit, push. The CV command picks the newest `Vo_Kenny_CV_*.pdf`
on its own, so it survives the monthly rename.

**everything**

```
cd /Users/kenny/dev/kenny-vo-website && ./build.sh "/Volumes/mirai/00ARCHITECTURE/Port/Current Port/Photography/Photography Portfolio Aug 2026.pdf" photography && ./build.sh "/Volumes/mirai/00ARCHITECTURE/Port/Current Port/2026 Aug Work Samples.pdf" work && ./build.sh "$(ls -t /Volumes/mirai/00ARCHITECTURE/Resume/Vo_Kenny_CV_*.pdf | head -1)" cv && git add -A && git commit -m "update books" && git pull --rebase && git push
```

**photography**

```
cd /Users/kenny/dev/kenny-vo-website && ./build.sh "/Volumes/mirai/00ARCHITECTURE/Port/Current Port/Photography/Photography Portfolio Aug 2026.pdf" photography && git add -A && git commit -m "update photography" && git pull --rebase && git push
```

**work samples**

```
cd /Users/kenny/dev/kenny-vo-website && ./build.sh "/Volumes/mirai/00ARCHITECTURE/Port/Current Port/2026 Aug Work Samples.pdf" work && git add -A && git commit -m "update work samples" && git pull --rebase && git push
```

**cv**

```
cd /Users/kenny/dev/kenny-vo-website && ./build.sh "$(ls -t /Volumes/mirai/00ARCHITECTURE/Resume/Vo_Kenny_CV_*.pdf | head -1)" cv && git add -A && git commit -m "update cv" && git pull --rebase && git push
```

If a portfolio's filename changes, edit the path in its command here.

## writing

Drop a `.md` or `.docx` in `writings/src/`, then:

```
cd /Users/kenny/dev/kenny-vo-website && ./writings.py && git add -A && git commit -m "new writing" && git pull --rebase && git push
```

Front matter goes at the very top of the file:

```
---
title: nothing fails loudly.
date: 2026-09-09
standfirst: one line under the title.
---
```

A filename starting with `_` is a draft and will not publish. Deleting the
source removes the published piece on the next run. Links are
`[the words](https://the-url.com)`. Footnotes are `[^1]` in the text and
`[^1]: the note` on its own line. Images go in `writings/src/images/` and are
written `![](images/name.jpg "caption")`.

## after editing css or js

Browsers cache assets for ten minutes, so a style change needs a new version
stamp or you will not see it:

```
cd /Users/kenny/dev/kenny-vo-website && n=$(($(grep -o 'v=[0-9]*' index.html | head -1 | cut -dv -f2 | tr -d '=')+1)) && grep -rlI "v=$((n-1))" . --exclude-dir=.git --exclude-dir=__pycache__ | xargs sed -i '' "s/v=$((n-1))/v=$n/g" && ./writings.py && git add -A && git commit -m "bump assets to v$n" && git pull --rebase && git push && echo "now at v$n"
```

## looking before pushing

```
cd /Users/kenny/dev/kenny-vo-website && python3 -m http.server 8765
```

Then open <http://localhost:8765>. Ctrl-C to stop.

## checking a deploy

Pages takes a minute or two, and the CDN holds HTML for ten.

```
gh api repos/kenny-t-vo/kenny-t-vo.github.io/actions/runs --jq '.workflow_runs[0] | "\(.status) \(.conclusion // "")"'
```

## when a command stops

`nothing to commit, working tree clean`: the build produced identical files. The
`&&` chain stops before the push, so an earlier local commit stays unpushed.

`your branch and 'origin/main' have diverged`: there is a commit on github.com and
a different one here. `git pull --rebase`, then `git push`.
