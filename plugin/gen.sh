
# Letöltjük a záradékokat:
#
#    Főmenü / Napló / Értékelés / Záradék -> Export -> TanEvvzaradekEdit.xls

# field-seperator(s),text-delimiter,encoding (ASCII 9: <TAB>)
# unoconv -f csv -e FilterOptions=9,, TanEvvzaradekEdit.xls
./gen-pluginDiak.py

#=================================================================================

# A záradékokban nincs benne az értékelés, azt is külön kell letölteni.
#
#    Főmenü / Napló / Értékelés / Vizsgák -> Export -> TanVizsgaEditPeda.xls
#    # Itt be kell jelölni a Közoktatási azonosítót is (kb. a 20. name="exportCheckbox$29")
#
# unoconv -f csv -e FilterOptions=9,, TanVizsgaEditPeda.xls
./gen-pluginTantargy.py

echo "a TESZI adatok kitöltése után (ha kell) le kell futtatni
./gen-pluginDiak.py
jegy.py"

