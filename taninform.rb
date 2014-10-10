#!/usr/bin/ruby

require 'watir-webdriver'
require 'date'
require 'pry' # Bárhol a forrásban: "binding.pry" parancssorba vált
TIMEOUT = 500 # Ennyi ideig fogja figyelni a letöltés könyvtárat, hogy leérkezett-e a kért dokumentum
DEBUG = false
ORASZAM = [37, 32] # A normál ill. végzős (12-es) osztályok éves óraszáma

class Taninform
  def initialize(tip: 'firefox', tanev: '')
    getIni()
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

  def getIni()
    @ini = Hash[ *File.readlines('taninform.ini').map { |i| i.strip.split(': ') }.flatten ]
    @download_directory = File.expand_path(@ini['downloads'])
    @download_directory.gsub!("/", "\\") if Selenium::WebDriver::Platform.windows?
    unless File.directory? (@download_directory) and File.writable? (@download_directory)
      puts "#{@download_directory} könyvtárba nem tudok írni! (taninform.ini: downloads)"
      exit
    end
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
    #b.window.maximize
  end

  #============ Bejelentkezés ============
  def login()
    puts "LOGIN" if DEBUG

    @b.goto 'https://start.taninform.hu/application/start?intezmenyIndex=029752'

    @sid = @b.hidden(:name => 'service').value.split('/')[-1] # SESSION id

    @b.text_field(:name => 'loginName').set @ini['user']
    @b.text_field(:name => 'password').set @ini['password']
    @b.form(:name => 'Form0').submit

    if @b.td(:class => 'login_err_mess').exists?
      puts @b.td(:class => 'login_err_mess').text
      exit
    end

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

    # Ha nem kaptunk külön letöltendő osztályt, akkor az összeset kell
    if osztalyok.empty?
      osztalyok = @osztalyLista
    end

    osztalyok.each do |osztaly|
      # Az oszt legyen a "8b" felépítésű, akármi is volt
      oszt = osztaly.sub('.', '')
      new_filename = File.join(@download_directory, oszt + '.xls')

      if !@osztalyLista.include?(osztaly)
        puts "A #{@tanev} tanévben nincs #{osztaly} osztály!"
        next
      end
      downloads_before = Dir.entries(@download_directory).reject { |f| f =~ /(.part\z|^\.)/ }

      # űrlap kitöltése (a tanév már be van írva)
      @b.input(:xpath => '//*[@id="osztalyFieldLTFITextField"]').when_present.click
      @b.td(:text => osztaly).when_present.click
      @b.text_field(:name => 'hetekField').when_present.set ORASZAM[1] if oszt =~ /12/
      @b.link(:text => 'Eredmények készítése').when_present.click

      old_filename = File.join(@download_directory, waitForDownload(downloads_before))
      File.rename(old_filename, new_filename)
      puts "done: #{new_filename}"
      STDOUT.flush
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

if ARGV.empty?
  puts "Usage: #{$0} ..."
  puts "  7a 10c ...: az osztályok eredménye"
  puts "  a: az összes osztály évvégi eredménye"
  puts "  t: TanuloAlap1.xls"
  exit
end

b = Taninform.new()
#b = Taninform.new(tanev: '2013/2014')

osztalyok = ARGV.select { |arg| arg =~ /^[0-9]/ }

b.getEvvege(osztalyok) if osztalyok.any?
b.getEvvege() if ARGV.include?('a')

b.getTanuloAlap() if ARGV.include?('t')

