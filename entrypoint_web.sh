#!/bin/bash

sigterm_signal() {
  echo "SIGTERM signal!"
  kill -TERM "$child" 2>/dev/null
}

trap sigterm_signal SIGTERM

python -m src.main &

child=$!
wait "$child"
