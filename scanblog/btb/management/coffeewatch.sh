while true ; do sleep 1 ; inotifywait static/js/moderation/*.coffee static/js/*.coffee ; coffee -c static/js/ ; done
