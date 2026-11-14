#!/usr/bin/env bash
# Starts one judge on a fresh copy of the package and returns. ~/judge.exit appears when it finishes.
# Usage: start-judge.sh <model> <timeout hours>
set -euo pipefail
rm -rf ~/review ~/judge.out ~/judge.err ~/judge.exit
sudo cp -r /root/package ~/review
sudo chown -R ubuntu: ~/review
setsid nohup bash -c "sed 's/{{MODEL}}/$1/g' ~/.judge-prompt.md | sprocket run --prompt-file - -C ~/review --model $1 --reasoning high --timeout $2h \
	> ~/judge.out 2> ~/judge.err; echo \$? > ~/judge.exit" < /dev/null > /dev/null 2>&1 &
