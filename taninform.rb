#!/usr/bin/ruby

# browser.driver.save_screenshot("file_name.png")

#require 'rubygems'
require 'watir-webdriver'
require 'timeout'
require 'date'
require 'pry' # Bárhol a forrásban: "binding.pry" parancssorba vált
TIMEOUT = 500 # Ennyi ideig fogja figyelni a letöltés könyvtárat, hogy leérkezett-e a kért dokumentum
DEBUG = false
ORASZAM = [37, 32] # A normál ill. végzős (12-es) osztályok éves óraszáma

class Taninform
  def initialize(tip: 'firefox', tanev: '')
    @download_directory = "#{Dir.pwd}/downloads"
    @download_directory.gsub!("/", "\\") if Selenium::WebDriver::Platform.windows?
    @osztalyLista = []

    @tanev = tanev
    ev = (Date.today-210).year
    @aktualisTanev = "#{ev}/#{ev+1}"

    # Ha nem kaptunk paraméterben rendes tanévet, akkor az aktuálisat használjuk
    if @tanev !~ /^\d{4}\/\d{4}$/
      @tanev = @aktualisTanev
    end

    if tip == 'chrome'
      getBrowserChrome()
    else
      getBrowserFirefox()
    end
    at_exit { @b.close if @b }
  end

  def getBrowserChrome()
    # !!!!! FIGYELEM! A letöltést nem menti el! !!!!!
    prefs = {
      :download => {
        :default_directory => @download_directory,
        :prompt_for_download => false,
        :directory_upgrade => true,
        :extensions_to_open => '',
      },
    }
    caps = Selenium::WebDriver::Remote::Capabilities.chrome
    caps['chromeOptions'] = {'prefs' => prefs}
    @b = Watir::Browser.new :chrome, :desired_capabilities => caps, :switches => %w[--test-type]
    @b.driver.manage.timeouts.implicit_wait = TIMEOUT
    @b.driver.manage.timeouts.script_timeout = TIMEOUT
    @b.driver.manage.timeouts.page_load = TIMEOUT
  end

  def getBrowserFirefox()
    profile = Selenium::WebDriver::Firefox::Profile.new
    profile['browser.download.folderList'] = 2 # custom location
    profile['browser.download.dir'] = @download_directory
    profile['browser.helperApps.neverAsk.saveToDisk'] = "application/vnd.ms-excel, application/pdf"
    profile['app.update.auto'] = false
    profile['app.update.enabled'] = false
    profile['pdfjs.disabled'] = true
    profile['pdfjs.firstRun'] = false
    @b = Watir::Browser.new :firefox, :profile => profile

    Watir.default_timeout = TIMEOUT
  end

  #============ Bejelentkezés ============
  def login()
    #b.window.maximize
    puts "LOGIN" if DEBUG
    @b.goto 'https://start.taninform.hu/application/start?intezmenyIndex=029752'

    @sid = @b.hidden(:name => 'service').value.split('/')[-1] # SESSION id

    @b.text_field(:name => 'loginName').set 'szaszi'
    @b.text_field(:name => 'password').set 'xxxxxxxxx'
    @b.form(:name => 'Form0').submit
    sleep 2 # Különben azt írja, hogy "A kiválasztott intézmény... nem létezik"
  end

  #============ Várunk a letöltésre ============
  # vár, amíg a download_directory-ba bekerül egy új fájl (max. TIMEOUT másodpercig)
  #
  def waitForDownload(downloads_before)
    begin
      file_name = ""
      TIMEOUT.times do
        difference = Dir.entries(@download_directory).reject { |f| f =~ /(.part\z|^\.)/ } - downloads_before
        if difference.size == 1
          file_name = difference.first 
          break
          end 
        sleep 1
        end
      raise "Could not locate a new file in the directory '#{@download_directory}' within " + TIMEOUT + " seconds" if not file_name
      # puts "Downloaded file: " + file_name
    end
    return file_name
  end

  # ============ Évvégi eredmény letöltése ============
  # Firefoxban meg lehet nézni az URL-t: (jobb klikk) This Frame / View Frame Info / Address
  def getEvvege(osztalyok = [])

    osztalyok.map! { |oszt| oszt.sub(/(\d*)[\. ]*(\D*)/,'\1.\2') } # "8.b" legyen mindenből

    login() if !@sid
    evvegeURL = 'https://start.taninform.hu/application/app?service=pageNavigator/' + @sid + '&sp=Snaplo&sp=SEvvegiExcel&1412349577710'
    @b.goto evvegeURL if @b.url != evvegeURL

    @b.select_list(:name => 'tanevField').when_present.select @tanev

    if @osztalyLista.empty?
      @b.input(:xpath => '//*[@id="osztalyFieldLTFITextField"]').when_present.click
      @b.elements(:xpath => '/html/body/table/tbody/tr/td/table/tbody/tr/td/form/table/tbody/tr[4]/td[2]/div/table/tbody/tr/td[1]').each do |i|
        next if i.text !~ /\A\d/
        @osztalyLista.push(i.text)
      end
      @b.element(:xpath => '/html/body/table/tbody/tr/td/table/tbody/tr/td/form/table/tbody/tr[4]/td[2]/div/table/tbody/tr[1]/td/table/tbody/tr/td[2]').click # Bezár
    end

    p @osztalyLista
    p osztalyok
    # Ha nem kaptunk külön letöltendő osztályt, akkor az összeset kell
    if osztalyok.empty?
      osztalyok = @osztalyLista
    end

#binding.pry

    @osztalyok.each do |osztaly|
      # Az oszt maradjon a "8b", akármi is volt
      oszt = osztaly.sub('.', '')
      new_filename = File.join(@download_directory, oszt + '.xls')

      if !osztalyok.include?(osztaly)
        puts "A #{@tanev} tanévben nincs #{osztaly} osztály!"
        next
      end
      downloads_before = Dir.entries(@download_directory).reject { |f| f =~ /(.part\z|^\.)/ }

      # űrlap kitöltése (a tanév már be van írva)
      @b.input(:xpath => '//*[@id="osztalyFieldLTFITextField"]').when_present.click
      @b.td(:text => osztaly).when_present.click
      @b.text_field(:name => 'hetekField').when_present.set ORASZAM[1] if oszt =~ /12/
      @b.link(:text => 'Eredmények készítése').when_present.click

      puts "done: #{new_filename}"
      old_filename = File.join(@download_directory, waitForDownload(downloads_before))
      File.rename(old_filename, new_filename)
#      STDOUT.flush
    end
    puts
  end

  #============ Az adott tanév osztálylistája ============
  def getOsztalyLista()
    # Csak akkor kell valamit csinálni, ha még üres az "osztályok" tömb
    if @osztalyok.empty?
      login() if !@sid
      if @tanev == @aktualisTanev
        # A rövid megoldás csak akkor működik, ha az aktuális tanévet akarom nézni
        osztalyURL = 'https://start.taninform.hu/application/app?service=pageNavigator/' + @sid + '&sp=Soktatasszervezes&sp=SOsztalyEdit&1412659826947'
        @b.goto osztalyURL if @b.url != osztalyURL

      else
        # Egyébként végigkattintgatom
        @b.td(:id => 'mainMenu_fomenu').when_present.click
        @b.td(:id => 'gwt-uid-244').when_present.hover
        @b.td(:id => 'gwt-uid-188').when_present.hover
        @b.td(:id => 'gwt-uid-182').when_present.click
        sleep 2

        # Keresés menü, itt ki lehet választani a tanévet, hogy megnézzük az osztályokat
        @b.element(:xpath => '/html/body/table/tbody/tr[1]/td/table/tbody/tr/td[2]/table/tbody/tr/td[1]/img').when_present.click
        sleep 1

        # A listából kiválasztjuk a tanévet, majd "Mehet"
        @b.iframe(:index => 1).div(:id => 'listAndEditTableID_filtering').select(:name => 'tanevFilterCombo').when_present.select @tanev
        @b.iframe(:index => 1).div(:id => 'listAndEditTableID_filtering').input(:value => 'Mehet').click
        sleep 2
      end

      @b.elements(:xpath => '//table[@id="listAndEditTableID"]/tbody/tr/td[2]/a').each do |i|
        @osztalyok.push(i.text) if i.text =~ /\A\d/
        print "#{i.text} "
      end

    end
  end

  #============ TanuloAlap1 ============
  def getTanuloAlap()
    # Tanulói alapadatok, táblázatos felsorolás
    login() if !@sid
    tanuloAlapURL = 'https://start.taninform.hu/application/app?service=pageNavigator/' + @sid + '&sp=Stanuloiadat&sp=STanuloAlap1&1410959217198'

    filename = Time.now.strftime("TanuloAlap1-%Y-%m-%d.xls")
    new_filename = File.join(@download_directory, filename)
    downloads_before = Dir.entries(@download_directory).reject { |f| f =~ /(.part\z|^\.)/ }

    @b.goto tanuloAlapURL if @b.url != tanuloAlapURL

    # Itt most a többoldalas export választható lista lesz a képen:
    @b.link(:text => 'Export').click

    # Letölti a TanuloAlap1.xls fájlt, csak a timeout nem működik
    # puts Time.now
    begin
      @b.input(:name => 'export').when_present.click
    rescue Net::ReadTimeout
      p "TIMEOUT"
    end
    old_filename = File.join(@download_directory, waitForDownload(downloads_before))
    File.rename(old_filename, new_filename)
    puts filename
  end
end

#b = Taninform.new()
b = Taninform.new(tanev: '2013/2014')

b.getEvvege(['7a', '8a'])
#b.getEvvege()
#b.getTanuloAlap()

