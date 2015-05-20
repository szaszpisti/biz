#!/bin/bash

EXT=xls # xls legyen, azt lehet olvasni az xlrd-vel
YEAR=$(date -d '210 days ago' +%Y)
TANEV=$( printf "%04d-%02d" $YEAR $((YEAR-1999)) )

case $0 in
	*-gen*)
		ls ../forras/*.csv \
			| sort -t'/' -k3 -n \
			| while read i; do
		  			cut -f2-4 $i \
					| sed 's/^uid.*/&\tora/'
			done > teszi-$TANEV.csv

		unoconv -f $EXT -i FilterOptions=9,, teszi-$TANEV.csv

		echo "A teszi-$TANEV.$EXT-t el kell küldeni Anikónak, beírja a TESZI óraszámokat!"
		;;
	*-extract*)
		# A kapott táblázatot vissza kell rakni csv-be:
		unoconv -f csv -o teszi.csv -e FilterOptions=9,, teszi-$TANEV.$EXT
		;;
esac

