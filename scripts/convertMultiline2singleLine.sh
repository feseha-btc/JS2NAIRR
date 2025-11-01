 awk '/^>/ {print (NR>1?"\n":"") $0; next} {printf "%s", $0;} END{print "";}' $1 >  $2
