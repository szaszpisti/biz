
var page = 3
var goPage = function(n) {
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
  $('#divBalGomb').append('<p style="text-align: center; border-top: 1px solid;"><span class="alahuzott">b</span>al margó</p>');
  $('input:radio[name=bal]:[value='+balDefault+']').attr('checked', 'checked');

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
      // a kapott key/val párokat bepakolja a megfelelő id-ekbe
      $.each(result, function(name, value){
        $("#" + name).html(value);
      });
      $("#uid").val(result['uid']);
      // a "nyelv és" kihúzása, ha szükséges
      s = $('#t01').html();
      if (s.substr(-3, 3) == '---') $('#t01').html('<span style="padding-left: 10mm;">' + s + '</span>');
    });
  };

  // ha változott az osztály
  var changeOsztaly = function() {
    // felsőbb évfolyam más oldalra kerül, más háttér kell neki
    onev = $('#oszt option:selected').text();
    evf = parseInt(onev.substring(0, onev.indexOf('.')));
    hatter = "url(image/biz-3-" + (evf>8?"felso":"also") + ".png)";
    $('#page3').css("background-image", hatter);
    getNevsor();
    $('#nevsor').focus();
    getData();
  };

  /*
   * Egérgörgetések következnek
   */

  $('#spanGerinc').bind("mousewheel DOMMouseScroll", function(event) {
    var delta = event.wheelDelta ||  event.detail || -event.originalEvent.wheelDelta || event.originalEvent.detail;
    gerinc = parseInt($('#gerinc').val());
    $('#gerinc').val(delta > 0 ? gerinc-1 : gerinc+1);
    return false;
  });

  $('#divDiff').bind("mousewheel DOMMouseScroll", function(event) {
    var delta = event.wheelDelta ||  event.detail || -event.originalEvent.wheelDelta || event.originalEvent.detail;
    diff = parseInt($('input:radio[name=diff]:checked').val());
    diff = delta>0 ? diff-1 : diff+1;
    diff = 3-diff;
    if (diff<0) diff = 0;
    if (diff>6) diff = 6;
    $('input:radio[name=diff]')[diff].checked = true;
    return false;
  });

  $('#divBalGomb').bind("mousewheel DOMMouseScroll", function(event) {
    var delta = event.wheelDelta ||  event.detail || -event.originalEvent.wheelDelta || event.originalEvent.detail;
    bal = parseInt($('input:radio[name=bal]:checked').val());
    balUj = delta>0 ? bal-1 : bal+1;
    if (balMin<=balUj && balUj<=balMax) bal = balUj
    $('input:radio[name=bal]:[value='+balUj+']').attr('checked', 'checked');
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
    $('#debug').attr('checked', !$('#debug').attr('checked'));
    verbose = !verbose;
  };

  var toggleFrame = function(){
    $('#frame').attr('checked', !$('#frame').attr('checked'));
  }

  $('#spanOsztaly').change ( function(){ changeOsztaly(); });
  $('#nevsor').change( function(){ getData(); });
  $("#nyomtat").click( function(){ nyomtat(); });
  $('#biz').submit(function() { return false; });

  // hogy az egész sor értse a kattintást, ne csak a checkbox
  $("#spanDebug").click(function(){ toggleDebug(); });
  $("#spanFrame").click(function(){ toggleFrame(); });

  shortcut.add("Ctrl+P", function() { alert("Print..."); });
  // Az operában sajnos nem működnek az Alt+x gyorsbillentyűk.
  if ( !$.browser.opera && !$.browser.safari ) {
    $('.alahuzott').css('text-decoration', 'underline'); // csak akkor legyenek aláhúzva, ha kell
    shortcut.add("Alt+B",  function(){ $('[name="bal"]:checked').focus(); });
    shortcut.add("Alt+J",  function(){ $('[name="diff"]:checked').focus(); });
    shortcut.add("Alt+G",  function(){ $('#gerinc').focus(); });
    shortcut.add("Alt+N",  function(){ $('#nevsor').focus(); });
    shortcut.add("Alt+D",  function(){ toggleDebug(); });
    shortcut.add("Alt+K",  function(){ toggleFrame(); });

    shortcut.add("Up",   function(){ $('#gerinc').val(parseInt($('#gerinc').val())+1); }, {'target': document.biz.gerinc});
    shortcut.add("Down", function(){ $('#gerinc').val(parseInt($('#gerinc').val())-1); }, {'target': document.biz.gerinc});
  }

  changeOsztaly();

});

