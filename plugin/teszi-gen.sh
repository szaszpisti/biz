#!/bin/bash

# A meglévő forras/*.xls-ekből gyártja a teszi-TANEV.xls-t, amit ki kell tölteni.
# Ezután kell futtatni a gen-pluginDiak.py-t, ami ezeket is hozzáveszi a záradékokhoz.

EXT=xls # xls legyen, azt lehet olvasni az xlrd-vel
YEAR=$(date -d '210 days ago' +%Y)
TANEV=$( printf "%04d-%02d" $YEAR $((YEAR-1999)) )

OUT=teszi-$TANEV.$EXT
TMP=$( tempfile -s '.csv' )

if [ -f "$OUT" ]; then
	echo "$OUT már létezik. Előbb töröld!"
	exit
fi

ls ../forras/[0-9]*.xls \
| sort -t'/' -k3 -n \
| while read FILE; do

	i=${FILE##*/} # levágjuk a bevezető könyvtárakat
	i=${i%.xls}   # és a .xls-t
	oszt="${i%%[a-z]*}. ${i##*[0-9]}" # 12a => 12. a
	xls2csv -q0 $FILE \
		| sed '1d;/^$/d;/\x0c/d' \
		| awk -v o="$oszt" -F, 'BEGIN{print "uid,osztaly,nev,ora"}{ OFS=","; print $2, o, $1}'

done > $TMP

unoconv -f $EXT -i FilterOptions=44,,UTF-8 -o $OUT $TMP

echo "A $OUT-t el kell küldeni Anikónak, beírja a TESZI óraszámokat!"

rm $TMP
