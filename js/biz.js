/*!
 * @file biz.js
 * A biz.html-hez tartozó JavaScript (jQuery) függvények.
 */

/*!
 * 1-2-3. oldal valamelyikére ugrunk
 * @param n 1, 2, 3 valamelyike
 */

if (typeof(jQuery) == 'undefined') {
    alert("Kérlek, telepítsd a jQuery-t a js/ könyvtárba!");
} else {
    var page = 3
    // 1-2-3. oldal valamelyikére ugrunk
    var goPage = function(n) {
        /*!
         * 1-2-3. oldal valamelyikére ugrunk
         * @param n 1, 2, 3 valamelyike
         */
        $('.page').hide();
        $('#page'+n).show();

        $('.p').removeClass('pselect');
        $('#p'+n).addClass('pselect');
        $('#pp').val(n);
        page = n;
    }

    $(document).ready(function() {

        goPage(3);
        var jsonFile = 'biz-json.py';
        var verbose = false;

        var balMin = 3;
        var balMax = 9;
        var balDefault = 7;

        // Első az osztálylista betöltése
        $.ajax({
            type: 'GET',
            url: jsonFile,
            dataType: 'json',
            success: function(result) { $('#spanOsztaly').html(result); },
            data: { tip: 'oszt' },
            async: false
        });

        // majd az osztályhoz tartozó névsor
        var getNevsor = function() {
            $.ajax({
                type: 'GET',
                url: jsonFile,
                dataType: 'json',
                async: false,
                data: { tip: 'nevsor', oszt: $('#oszt').val() },
                success: function(result) {
                    $('#nevsor').html(result);
                },
            });
        };

        // a "bal" gombok generálása a korábban megadott értékekkel
        for (i=balMin; i<=balMax; i++) {
            $('#divBalGomb').append('<div class="bal-gomb"><p><input name="bal" type="radio" value="' + i + '"><br>' + i + '</p></div>');
        }
        $('#divBalGomb').append('<div style="clear: both"></div>');
        $('#divBalGomb').append('<p style="text-align: center; border-top: 1px solid;"><span class="alahuzott">b</span>al margó (mm)</p>');
        $('input[name="bal"][value="'+balDefault+'"]').attr('checked', 'checked');

        // egy diák adatainak betöltése
        var getData = function() {
            var send = $('#biz').serialize();
            send += '&tip=uid';
            if (verbose) $('#message').html(send); else $('#message').html('');
            $.getJSON(jsonFile, send, function(result){
                // 3 név van összesen, ezeket megkülönböztetjük
                result['nev1'] = result['nev'];
                result['nev2'] = result['nev'];
                result['nev3'] = result['nev'];
                for(i=1; i<=3; i++){
                    hatter = 'url(image/biz-' + i + '-' + result['sablon'] + '.png)';
                    $('#page' + i).css("background-image", hatter);
                }
                // a kapott key/val párokat bepakolja a megfelelő id-ekbe
                $.each(result, function(name, value){
                    $("#" + name).html(value);
                });
                $("#uid").val(result['uid']);
                // a "nyelv és" kihúzása, ha szükséges
                s = $('#t01').html();
                if (s.substr(-3, 3) == '---') $('#t01').html('<span style="padding-left: 10mm;">' + s + '</span>');

                // Taninform link: az aktuális link "=" előtti részéhez hozzárakjuk az om azonosítót
                url = $("#url").attr('href').split('=')[0] + '=' + result['om']
                $("#url").attr('href', url)
            });
        };

        // ha változott az osztály
        var changeOsztaly = function() {
            // felsőbb évfolyam más oldalra kerül, más háttér kell neki
            onev = $('#oszt option:selected').text();
            evf = parseInt(onev.substring(0, onev.indexOf('.')));
            getNevsor();
            $('#nevsor').focus();
            getData();
        };

        /*
         * Egérgörgetések
         */

        $('#spanGerinc').bind("mousewheel DOMMouseScroll", function(event) {
            var delta = event.wheelDelta ||  event.detail || -event.originalEvent.wheelDelta || event.originalEvent.detail;
            gerinc = parseInt($('#gerinc').val());
            $('#gerinc').val(delta > 0 ? gerinc-1 : gerinc+1);
            return false;
        });

        $('#divDiff').bind("mousewheel DOMMouseScroll", function(event) {
            var delta = event.wheelDelta ||  event.detail || -event.originalEvent.wheelDelta || event.originalEvent.detail;
            diff = parseFloat($('input[name=diff]:checked').val());
            diff = delta>0 ? diff-0.5 : diff+0.5;
            diff = 3-diff;
            if (diff<0) diff = 0;
            if (diff>6) diff = 6;
            $('input[name=diff]')[parseInt(diff*2)].checked = true;
            return false;
        });

        $('#divBalGomb').bind("mousewheel DOMMouseScroll", function(event) {
            var delta = event.wheelDelta ||  event.detail || -event.originalEvent.wheelDelta || event.originalEvent.detail;
            bal = parseInt($('input[name=bal]:checked').val());
            balUj = delta>0 ? bal-1 : bal+1;
            if (balMin<=balUj && balUj<=balMax) bal = balUj
            $('input[name=bal][value='+balUj+']').attr('checked', 'checked');
            return false;
        });

        // ezzel lehet elküldeni a nyomtatóra
        var nyomtat = function(){
            var send = $('#biz').serialize();
            send += '&tip=nyomtat';
            $.getJSON(jsonFile, send, function(result){
                $('#message').html(result['message']);
            });
    //    $('#tip').val('n');
        }

        var toggleDebug = function(){
            $('#debug').prop('checked', !$('#debug').prop('checked'));
            verbose = !verbose;
        };

        var toggleFrame = function(){
            $('#frame').prop('checked', !$('#frame').prop('checked'));
        }

        $('#spanOsztaly').change ( function(){ changeOsztaly(); });
        $('#nevsor').change( function(){ getData(); });
        $("#nyomtat").click( function(){ nyomtat(); });
        $('#biz').submit(function() { return false; });

        // hogy az egész sor értse a kattintást, ne csak a checkbox
        $("#spanDebug").click(function(){ toggleDebug(); });
        $("#spanFrame").click(function(){ toggleFrame(); });

        if(typeof(shortcut) == 'undefined') {
            alert("A gyorsbillentyűkhöz telepítsd a shortcut.js-t a js/ könyvtárba!\nhttp://www.openjs.com/scripts/events/keyboard_shortcuts/");
        } else {
            shortcut.add("Ctrl+P", function() { nyomtat(); });

            // Az operában sajnos nem működnek az Alt+x gyorsbillentyűk, Alt nélkül használjuk
            shortcut.add("1", function(){ goPage(1); });
            shortcut.add("2", function(){ goPage(2); });
            shortcut.add("3", function(){ goPage(3); });

            shortcut.add("B", function(){ $('[name="bal"]:checked').focus(); });
            shortcut.add("F", function(){ $('[name="diff"]:checked').focus(); });
            shortcut.add("G", function(){ $('#gerinc').focus(); });
            shortcut.add("N", function(){ $('#nevsor').focus(); });
            shortcut.add("O", function(){ $('#oszt').focus(); });
            shortcut.add("D", function(){ toggleDebug(); });
            shortcut.add("E", function(){ toggleFrame(); });

            shortcut.add("Up",   function(){ $('#gerinc').val(parseInt($('#gerinc').val())+1); }, {'target': document.biz.gerinc});
            shortcut.add("Down", function(){ $('#gerinc').val(parseInt($('#gerinc').val())-1); }, {'target': document.biz.gerinc});
        }

        changeOsztaly();

    });
}
