#!/usr/bin/env bash
# Starts one judge on a fresh copy of ~/package and returns. ~/judge.exit appears when it finishes.
# Usage: start-judge.sh <model> <timeout hours>
set -euo pipefail
rm -rf ~/review ~/judge.out ~/judge.err ~/judge.exit
cp -r ~/package ~/review
setsid nohup bash -c "sprocket run --prompt-file ~/.judge-prompt.md -C ~/review --model $1 --reasoning high --timeout $2h \
	> ~/judge.out 2> ~/judge.err; echo \$? > ~/judge.exit" < /dev/null > /dev/null 2>&1 &
