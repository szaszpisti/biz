#!/bin/bash

# MaYoR:
# cd ~/bin/teszi; teszi.sql ==> teszi.csv; put teszi.csv - ebben vannak az osztálynévsorok fejlécestül
# fules:
# $ mv ~/p/mayor/teszi.csv .; ./teszi-gen.sh

## echo 'SELECT oId, osztalyJel, viseltNev FROM local.diak' | mysql -N | ssh szaszi@10.0.0.2 dd of=mayor/nevsor-`date +%F`.csv

EXT=xls # xls legyen, azt lehet olvasni az xlrd-vel
YEAR=$(date -d '210 days ago' +%Y)
TANEV=$( printf "%04d-%02d" $YEAR $((YEAR-1999)) )

OUT=teszi-$TANEV.$EXT
NEVSOR=teszi.csv

if [ -f "$OUT" ]; then
	echo "$OUT már létezik. Előbb töröld!"
	echo "unoconv -f csv -e FilterOptions=9,,UTF-8 teszi-$TANEV.xls"
	exit
fi

unoconv -f $EXT -i FilterOptions=9,,UTF-8 -o $OUT $NEVSOR

echo "A $OUT-t el kell küldeni a teszisnek, aki beírja a TESZI óraszámokat!"

