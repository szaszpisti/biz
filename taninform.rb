#!/usr/bin/ruby

# browser.driver.save_screenshot("file_name.png")

require 'rubygems'
require 'watir-webdriver'
require 'timeout'
require 'date'
require 'pry' # goto irb
TIMEOUT = 500 # Ennyi ideig fogja figyelni a letöltés könyvtárat, hogy leérkezett-e a kért dokumentum

class Taninform
  def initialize(tip='firefox')
    @tip = tip
    @download_directory = "#{Dir.pwd}/downloads"
    @download_directory.gsub!("/", "\\") if Selenium::WebDriver::Platform.windows?
    @osztalyok = nil

    ev = (Date.today-210).year
    @tanev = "#{ev}/#{ev+1}"

    if tip == 'chrome'
      getBrowserChrome()
    else
      getBrowserFirefox()
    end
    at_exit { @b.close if @b }
  end

  def getBrowserChrome()
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
    @b.goto 'https://start.taninform.hu/application/start?intezmenyIndex=029752'

    @sid = @b.hidden(:name => 'service').value.split('/')[-1] # SESSION id

    @b.text_field(:name => 'loginName').set 'szaszi'
    @b.text_field(:name => 'password').set 'xxxxxxxxx'
    @b.form(:name => 'Form0').submit
  end

  #============ Várunk a letöltésre ============
  # vár, amíg a download_directory-ba bekerül egy új fájl (max. TIMEOUT másodpercig)
  #
  def waitForDownload(downloads_before)
    begin
      file_name = ""
      TIMEOUT.times do
        p Dir.entries(@download_directory).reject { |f| f =~ /(.part\z|^\.)/ }
        difference = Dir.entries(@download_directory).reject { |f| f =~ /.part\z/ } - downloads_before
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
  def getEvvege(oszt, tanev=@tanev)
    login() if !@sid
    evvegeURL = 'https://start.taninform.hu/application/app?service=pageNavigator/' + @sid + '&sp=Snaplo&sp=SEvvegiExcel&1412349577710'

    @b.goto evvegeURL if @b.url != evvegeURL
    new_filename = File.join(@download_directory, oszt + '.xls')
    osztaly = oszt.sub(/(\d*)(\D*)/,'\1.\2')

    downloads_before = Dir.entries(@download_directory).reject { |f| f =~ /.part\z/ }
    p downloads_before

    # űrlap kitöltése
    @b.select_list(:name => 'tanevField').when_present.select tanev
    @b.text_field(:name => 'hetekField').when_present.set '32' if oszt =~ /12/
    @b.input(:id => 'osztalyFieldLTFITextField').when_present.click
    @b.td(:text => osztaly).when_present.click

    sleep 2

    # Ha még üres az "osztályok" tömb, akkor feltöltjük
    # if !@osztalyok
    #   t = @b.elements(:xpath => '//table[@id="LTFIResultTable1"]/tbody/tr/td[1]').when_present
    #   t.each do |i|
    #     @osztalyok.push(i.text) if i.text =~ /\A\d/
    #   end
    # end

binding.pry
    @b.link(:text => 'Eredmények készítése').when_present.click

    old_filename = File.join(@download_directory, waitForDownload(downloads_before))
    File.rename(old_filename, new_filename)
    puts oszt
  end

  #============ TanuloAlap1 ============
  def getTanuloAlap()
    # Tanulói alapadatok, táblázatos felsorolás
    login() if !@sid
    tanuloAlapURL = 'https://start.taninform.hu/application/app?service=pageNavigator/' + @sid + '&sp=Stanuloiadat&sp=STanuloAlap1&1410959217198'

    filename = Time.now.strftime("TanuloAlap1-%Y-%m-%d.xls")
    new_filename = File.join(@download_directory, filename)
    downloads_before = Dir.entries(@download_directory).reject { |f| f =~ /.part\z/ }

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

b = Taninform.new('chrome')

# ['7a', '8a', '9a', '9b', '9c', '10a', '10b', '10c', '11a', '11b', '12a', '12b'].each do |oszt|
['7a', '8a', '9a', '9b', '9c', '10a', '10b', '11a', '11b', '12a', '12b'].each do |oszt|
  b.getEvvege(oszt, tanev='2013/2014')
end

b.getTanuloAlap()

