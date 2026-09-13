# DEVLOG — Belgeİz

## 1. Kapsamı parçalama (2 saat)

İşi beş dikey dilime ayırdım: (1) dosya kabulü/güvenlik sınırları, (2) PDF ve görüntüden metin çıkarımı, (3) kaynak konumunu kaybetmeyen parçalama/arama, (4) kanıta bağlı yanıt üretimi, (5) arayüz/kurulum/test/dokümantasyon.

İlk risk listesi:

- Halüsinasyon engellenmesi için dosya kabul ve güvenlik sınırları net belirlenmelidir.
- Taranmış PDF ile metin PDF aynı dosya uzantısına sahip; sayfa bazlı fallback gerekir.
- Türkçe eklemeli yapı salt exact token aramasını zayıflatır.
- OCR native bağımlılıkları kolay kurulumu bozabilir.
- Kaynağın sayfa numarası parçalama sırasında kaybedilirse sonradan güvenilir atıf üretilemez.

Başarı ölçütünü “her soruya cevap” değil, “kanıt varsa kaynaklı cevap; yoksa güvenli ret” olarak belirledim.

## 2. Alternatif mimariler (2 saat)

Üç yaklaşımı karşılaştırdım:

1. Tam bulut: OpenAI dosya yükleme + File Search + cevap modeli.
2. Klasik RAG: embedding + FAISS/Chroma + cevap modeli.
3. Yerel çıkarım/lexical retrieval + yalnızca cevap aşamasında model.

Tam bulut yaklaşımı MVP kodunu kısaltıyordu fakat belge yaşam döngüsü, uzak depolama ve ek maliyet getiriyordu. Embedding yaklaşımı semantik recall avantajlıydı; ancak binary indeks/servis, embedding maliyeti ve skor kalibrasyonu teslimatı ağırlaştırıyordu. Üçüncü yaklaşım denetlenebilir, küçük koleksiyonlarda yeterli ve çevrimdışı test edilebilir olduğu için seçildi.

Bu kararın bilinçli bedeli: eş anlamlı/dolaylı sorularda daha fazla yanlış ret. Güvenilirlik şartında yanlış olumlu cevaptan daha kabul edilebilir.

## 3. OCR teknoloji seçimi (2 saat)

Tesseract, EasyOCR ve model tabanlı vision OCR değerlendirildi.

- Tesseract’ın Türkçe dil paketi başarılı; fakat Windows/Linux/macOS native binary ve `tessdata` kurulumu farklı.
- Vision OCR kaliteli olabilir; her sayfa için API maliyeti/veri aktarımı getirir.
- EasyOCR pip/Torch üzerinden `tr` + `en` okuyabilir ve native Tesseract gerektirmez.

EasyOCR seçildi. Modelin ilk kullanımda indirilmesi başlangıçta gözden kaçabilecek bir bağımlılıktı; bu nedenle daha sonra `scripts/prepare_ocr.py` kurulum adımına eklenerek otomatik önbellekleme yapıldı.

## 4. PDF ve sayfa kökeni (2 saat)

PyMuPDF ile her sayfada sıralı düz metin çıkarımı uygulandı. Karakter sayısı çok azsa veya alfanümerik oran düşükse sayfa render edilip OCR’a gönderiliyor. Böylece bütün PDF’yi gereksiz OCR etmek yerine sayfa bazlı hibrit yol kullanılıyor. İlk sürümde eşik ve render çözünürlüğü fazla muhafazakârdı; aşağıdaki bakım turunda ölçümle yeniden ayarlandı.

Parçalar şu bilgileri zorunlu taşıyor: benzersiz id, dosya adı, 1 tabanlı sayfa, metin ve çıkarım yöntemi. Parça id’si dosya/sayfa/sıra/içerik hash’inden üretiliyor; modelin uydurduğu id ile gerçek id ayrıştırılabiliyor.

## 5. Parçalama denemeleri (2 saat)

Önce sabit karakter uzunluğu düşünüldü. Türkçe kelimeyi ortadan kesmesi, tablolu satırları anlamsızlaştırması ve atıf gösteriminde kötü okunması nedeniyle vazgeçildi.

Paragraf öncelikli, en fazla 180 kelimelik ve 30 kelime örtüşmeli yöntem uygulandı. Sayfa sınırı asla aşılmıyor. Uzun tek paragraf pencereyle bölünüyor; kısa paragraflar bütçeye kadar birleştiriliyor. Temizleme, satır sonlarını tümüyle silmeyerek tablo-benzeri yapıyı koruyor.

## 6. Retrieval prototipi (2.5 saat)

İlk salt token-overlap denemesi, sık geçen kelimelerin alakasız parçaları öne taşıması nedeniyle yetersizdi. BM25 eklendi. Ham BM25 skorunun belge setine göre değişmesi tek başına güvenli eşik vermediği için üç sinyal birleştirildi:

- %40 doygunlaştırılmış BM25
- %40 anlamlı sorgu kelimesi kapsaması
- %20 aynı kök/prefix çevresinde yazım-çekim toleranslı benzerlik

Türkçe `İ/I/ı/i` normalizasyonu özel ele alındı. Soru kelimeleri listesindeki Türkçe ve İngilizce işlev sözcükleri retrieval sinyalinden çıkarıldı. Eşik başlangıç değeri `0.18` seçildi; veri kümesi kalibrasyonu gerektirdiği yapılandırmada açıkça belirtildi.

## 7. Halüsinasyon koruma tasarımı (2.5 saat)

Tek koruma yerine savunma katmanları kuruldu:

1. Retrieval skoru düşükse LLM hiç çağrılmıyor.
2. Seçilen bağlam karakter bütçesiyle sınırlanıyor.
3. Her parça açık `<SOURCE id file page>` bloğunda taşınıyor.
4. Belge içi talimatların uygulanmaması geliştirici talimatında yazıyor.
5. Yanıt `grounded/answer/citation_ids` strict JSON Schema ile isteniyor.
6. Atıf id’leri uygulama tarafında whitelist ile doğrulanıyor.
7. Atıf yoksa veya hayaliyse üretilen metin gösterilmiyor, ret dönüyor.

Model olarak `gpt-5.4-mini`, resmî OpenAI belgelerinde Responses API ve Structured Outputs desteği bulunan güncel, yüksek hacimli mini seçenek olarak seçildi. Model ortam değişkeni/arayüzden değiştirilebilir bırakıldı. İsteklerde veri saklamayı azaltmak için `store=False` kullanıldı.

## 8. Arayüz ve kullanılabilirlik (2 saat)

Streamlit ile çoklu dosya yükleme, API anahtarı/model/eşik ayarı, işlem ilerlemesi, uyarılar, belge/sayfa/OCR metrikleri ve sohbet akışı geliştirildi.

Yanıt kaynakları kapalı detay panellerinde dosya adı, sayfa ve ham metin olarak gösteriliyor. Bu tasarım, kullanıcıya yalnızca “kaynak var” rozeti göstermek yerine kanıtı doğrudan doğrulama olanağı veriyor. API anahtarı yokken belge işleme çalışıyor; soru sorulduğunda açık kurulum mesajı veriliyor.

## 9. Kurulum ve taşınabilirlik (2 saat)

Yerel makinede PATH üzerinde Python bulunmadığı saptandı. Windows betiğine Python tespiti, `py` launcher fallback’i ve gerekirse `winget` ile Python 3.12 kurulumu eklendi. macOS/Linux betiği Homebrew/apt/dnf yollarını kapsıyor.

`.venv`, paket kurulumu ve OCR model önbellekleme tek komuta bağlandı. Dockerfile da aynı bağımlılıkları ve OCR modellerini image build sırasında hazırlıyor. `.env` ve model önbelleği git dışında tutuldu.

## 10. İlk test turu ve bulunan hatalar (2 saat)

İlk otomatik turda 15 test geçti. Kapsama %77 idi. İki uygulama kusuru inceleme sırasında yakalandı:

- `@dataclass(slots=True)` sınıfındaki varsayılanlara `cls.model` gibi erişim descriptor döndürüyordu. `defaults = cls()` üzerinden okunacak şekilde düzeltildi.
- PDF kapatıldıktan sonra `document.page_count` okunuyordu. Sayfa sayısı kapanmadan önce yerel değişkende tutuldu.

PyMuPDF 1.28.2, eski `fitz` import adının kaldırılacağını uyardı. Kod ve test `import pymupdf` biçimine geçirildi. Bu, test geçse bile gelecekte kırılabilecek bir bağımlılık uyarısını erkenden temizledi.

## 11. Test kapsamını genişletme (2 saat)

Otomatik senaryolar şunları kapsayacak şekilde tamamlandı:

- metin temizleme ve örtüşmeli parçalama
- Türkçe harf normalizasyonu
- Türkçe tutar ve İngilizce tarih retrieval’ı
- kapsam dışı soruda model fonksiyonunun hiç çağrılmaması
- hayali atıf id’sinin reddi
- belge içi prompt injection metninin SOURCE verisi kalması
- JPG/PNG OCR yönlendirmesi ve düşük güven uyarısı
- metin PDF/table-like satır çıkarımı
- boyut/uzantı güvenlik sınırları
- OpenAI Responses parametrelerinde strict schema ve `store=False`

Sonuç: 20/20 test, %85 toplam kapsam. Boş görüntü sayfalı PDF'nin gerçekten OCR fallback yoluna girdiği ve servis orkestrasyonunun doğru kurulduğu ayrı testlerle doğrulandı.

## 12. Gerçek bağımlılık ve sunucu doğrulaması (2 saat)

Temiz `.venv` içine tüm paketler kuruldu. Kurulan ana sürümler: Streamlit 1.63.0, PyMuPDF 1.28.2, EasyOCR 1.7.2, OpenAI 2.54.0, Torch 2.14.0.

Streamlit headless olarak 8517 portunda başlatıldı. `/_stcore/health` ve ana sayfa HTTP 200 döndürdü. Süreç kontrollü biçimde kapatıldı. Bu test yalnızca import değil, gerçek ASGI/Streamlit sunucu başlangıcını doğruladı.

## 13. Gerçek OCR testi ve ikinci sorun (2 saat)

Sentetik TR/EN görüntüyle ilk EasyOCR çalıştırması model dizinini kullanıcı profilindeki `~/.EasyOCR` altında açmaya çalıştı. Kısıtlı/kurumsal ortamlarda bu konum yazılamıyordu. Bu hata yalnızca stub testte görünmedi.

Çözüm: hem `model_storage_directory` hem `user_network_directory` proje içindeki `.easyocr` yoluna yönlendirildi; `BELGEIZ_OCR_MODEL_DIR` ile değiştirilebilir yapıldı. Sonraki çalışmada detection ve Türkçe tanıma modelleri indirildi. Sentetik iki satırda ortalama güven `0.887` ölçüldü; İngilizce satır ile tutar doğru okundu. Terminal kod sayfası Türkçe `ı` gösterimini bozduğu için bu karakter üzerinde başarı iddiası yapılmadı.

## 14. Dokümantasyon ve teslimat sertleştirme (2 saat)

README’e hızlı başlangıç, Docker yolu, mimari, alternatifler, yapılandırma, güvenlik ve dosya haritası eklendi. TESTING dosyasına otomatik sonuçlar, kabul senaryoları, cevaplanamaz soru davranışı, sınırlar ve üretim kalite kapısı yazıldı.

Hız/kolaylık uğruna atlanmayan noktalar: API anahtarı `.env` örneğinde sahte değer; gerçek anahtar dosyaya yazılmıyor. Dosyalar kalıcı diske alınmıyor. Model yanıtı kaynak göstermezse arayüzde gösterilmiyor.

## 15. Son değerlendirme (1 saat)

Gereksinim eşleştirmesi:

- PDF/JPG/PNG: var
- TR/EN OCR: var, gerçek model smoke testi yapıldı
- doğal dil soru-cevap: ilk teslimatta API anahtarıyla Responses API; sonraki bakım turunda yerel Ollama eklendi
- halüsinasyon azaltma: dört uygulama katmanı + görünür kaynak
- arayüz: var
- otomatik kurulum: Windows, macOS/Linux ve Docker
- kaynak kod, README, DEVLOG, TESTING: var

### Şu an bildiğimle baştan başlasaydım

1. OCR model dizinini ilk satırdan uygulama kapsamındaki yazılabilir yola alırdım; `~/.EasyOCR` varsayımını daha erken test ederdim.
2. Retrieval eşiğini sentetik üç belge yerine en baştan 200 soruluk TR/EN “answerable/unanswerable” setiyle kalibre ederdim.
3. Karmaşık tablolar kritikse düz metin MVP’sinden önce tablo hücresi şeması ve sorgu türleri tanımlardım.
4. Kurulum hızını iyileştirmek için “hafif metin-PDF profili” ve “tam OCR profili” sunmayı düşünürdüm; mevcut teslimatta fonksiyonel gereksinimi eksiksiz tutmak için OCR varsayılan kurulumda.
5. Model semantik doğruluk testlerini, kullanıcının test API anahtarı sağlayabildiği ayrı ve isteğe bağlı entegrasyon test grubuna eklerdim.

### Sonraki teknik adımlar

- Altın veri kümesi ve ölçülebilir retrieval/grounding metrikleri
- Karmaşık tablo çıkarımı
- Kalıcı, şifreli çok-kullanıcılı belge deposu
- Arka plan iş kuyruğu ve büyük dosya ilerleme olayları
- Malware tarama/sandbox, kimlik doğrulama ve denetim kaydı
- Lexical + multilingual embedding hibriti için A/B testi

## 16. “Belge işleme bitmiyor” teşhisi (1.5 saat)

Kullanıcı geri bildirimini iki ayrı akışa böldüm: dijital PDF’nin yanlışlıkla ağır OCR’a düşmesi ve gerçek taramalarda OCR’ın doğal CPU maliyeti. Önce tahmin yerine ölçüm ekledim. 50 sayfalık sentetik dijital PDF yalnız PyMuPDF yolunda 0,0224 saniyede işlendi. Büyük 2400×3200 tarama ise model yükleme dahil yaklaşık 23 saniye aldı. Bu, “donma” hissinin hem yanlış yönlendirme hem de görünür ilerleme eksikliğinden kaynaklandığını gösterdi.

Asıl hata, ilk sürümde metin sayfasını taranmış sayma eşiğinin 40 karakter olmasıydı. `Toplam: 42 TL` gibi tamamen geçerli kısa sayfalar pahalı OCR’a gönderilebiliyordu. Eşik 8 anlamlı karaktere indirildi; alfanümerik kalite kontrolü korundu. Yeni otomatik test kısa metnin OCR’a gitmediğini doğruladı.

## 17. OCR performans ayarı ve ilerleme (1.5 saat)

EasyOCR Reader her belge için yeniden kurulmak yerine süreç çapında LRU önbelleğine alındı. Torch CPU iş parçacıkları masaüstünü kilitlememek için sınırlandı. Görüntüler OCR öncesi EXIF yönü, gri ton ve otomatik kontrast aşamalarından geçirildi; uzun kenar 1400 piksel, PDF render ölçeği 1,20 olarak ayarlandı. Greedy decoder seçildi.

1200 ve 1400 piksel denemelerinde sentetik tarama güveni sırasıyla yaklaşık 0,847 ve 0,819 kaldı; aynı süreçte süreler 22,837 ve 17,641 saniye ölçüldü. İlk ölçüm modelin belleğe alınmasını da içerdiği için değerleri kesin A/B karşılaştırması olarak kullanmadım. Güven/hız dengesi için 1400 seçildi ve arayüz yardımında taranmış sayfa başına yaklaşık 15–30 saniye beklentisi açıklandı.

Her sayfa ve her dosya için progress callback eklendi. Arayüz artık dosya adı, aktif sayfa, tamamlanan sayfa ve toplam süreyi gösteriyor. Yalnız dijital belge kullananlar için OCR kapatma anahtarı eklendi. Böylece gerçek tarama ağır olsa bile uygulama tamamlanmamış/donmuş izlenimi vermiyor.

PaddleOCR ve RapidOCR da daha hızlı CPU alternatifi olarak araştırıldı. PaddleOCR’nin güncel çok dilli modeli Türkçeyi destekliyor; ancak Windows binary/wheel ağırlığı ve mevcut EasyOCR kurulumuna ikinci büyük OCR yığını eklemenin teslimat riskini artırması nedeniyle bu turda uygulanmadı. Tesseract aynı nedenle native kurulum bağımlılığı olarak kaldı.

## 18. Arayüz, Streamlit ve başlatıcı (1.5 saat)

Arayüzdeki İngilizce/Türkçe karışık etiketler tek tek kaldırıldı. Koyu yeşil yan panel, kaynak odaklı hero alanı, üç adımlı başlangıç kartları, metrik kartları, daha okunur boş durum ve gizlilik bildirimi eklendi. Dosya yükleyicinin Streamlit’ten gelen İngilizce metinleri CSS ile Türkçeleştirildi. Mobil genişlikte kartlar tek kolona düşüyor.

Streamlit araç çubuğu, “Manage app”, ana menü ve alt bilgi gizlendi. `.streamlit/config.toml` ile `gatherUsageStats=false`, `server.headless=true`, minimal araç çubuğu ve dosya izleyiciyi kapatma ayarlandı. `headless=true`, ilk çalıştırmadaki e-posta toplama sorusunu engelliyor; telemetri ayarı da kullanım istatistiği gönderimini kapatıyor.

PowerShell execution policy hatasını kullanıcıya kalıcı sistem ayarı değiştirtmeden aşmak için `BelgeIz.cmd` oluşturuldu. Kullanıcı çift tıklıyor; sanal ortam yoksa başlatıcı `setup.ps1` dosyasını yalnız o süreç için Bypass ile çalıştırıyor, sonra Türkçe `launcher.py` tarayıcıyı açıyor. `run.ps1` ve `run.sh` da aynı başlatıcıya yönlendirildi.

## 19. Açık ağırlıklı yerel model ve son doğrulama (1.5 saat)

Yanıt katmanı tek sağlayıcıya bağlı olmaktan çıkarıldı. OpenAI responder’ın yanına Ollama `/api/chat` istemcisi eklendi. Yerel akış da aynı `grounded/answer/citation_ids` JSON Schema sözleşmesini, retrieval eşiğini ve gerçek kaynak kimliği whitelist’ini kullanıyor. Böylece sağlayıcı değişse de halüsinasyon koruma katmanları atlanmıyor.

Qwen3 ailesi Türkçe dâhil çok dilli desteği, Ollama’daki hazır boyut seçenekleri ve Apache 2.0 açık ağırlık lisansı nedeniyle seçildi. Arayüzde 1.7B, 4B instruct ve 8B sunuldu; 4B hız/kalite dengesi olarak varsayılan yapıldı. `YerelModelKur.cmd`, Windows’ta Ollama ve yaklaşık 2,5 GB’lık modeli hazırlar. Yerel mod API anahtarı/istek ücreti istemez; disk, RAM ve yerel işlem gücü bedeli açıkça belgelendi.

Yeni testler; kısa PDF hız yolunu, sayfa ilerlemesini, Ollama JSON Schema isteğini, model sağlık kontrolünü ve servis sağlayıcı seçimini kapsadı. Sonuç 25/25 test, %81 kapsam, başarılı `compileall` ve temiz `pip check` oldu. Gerçek başlatıcıyla sağlık ve kök URL’leri HTTP 200 döndü; terminalde e-posta istemi görülmedi.

Bu turdan sonra baştan başlasaydım OCR’ın “tarama tespiti” eşiğini ilk günden gerçek kısa belgelerle test eder, dijital PDF ve taranmış PDF için ayrı performans bütçeleri tanımlar, ayrıca uzun OCR işleri için iptal edilebilir arka plan kuyruğunu MVP mimarisine daha erken koyardım.

## 20. Windows CMD satır sonu hatası (0.5 saat)

İlk çift tıklama denemesinde kullanıcı `'wershell.exe'`, `'errorlevel'` ve tek harfli komutların tanınmadığını bildirdi. Ham bayt incelemesi iki `.cmd` dosyasının Unix `LF` satır sonları ve UTF-8 Türkçe metin içerdiğini gösterdi. `cmd.exe`, özellikle parantezli bloklarda bu bileşimi yanlış ayrıştırıp bazı satırların ilk karakterlerini tüketiyordu.

İki başlatıcı BOM’suz ASCII komutlar ve yalnız Windows `CRLF` satır sonlarıyla yeniden oluşturuldu. Kırılgan parantezli akış yerine `goto` etiketleri kullanıldı; PowerShell çağrısı PATH yerine `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe` tam yoluna bağlandı. Kurulum ancak tüm paketler ve OCR modeli tamamlandığında `.venv/.belgeiz-ready` işareti oluşturuyor; yarım kalmış ortam bir sonraki açılışta otomatik yeniden kuruluyor. Güncel `BelgeIz.cmd` gerçek `cmd.exe` altında başlatıldı ve sağlık uç noktası `200 ok` verdi. ASCII/CRLF ve tam PowerShell yolu için kalıcı regresyon testi eklendi; toplam test sayısı 26’ya çıktı.

## 21. Structured Outputs 400 ve UI durum renkleri (1 saat)

İlk gerçek OpenAI sorusunda servis, `citation_ids` dizisindeki `uniqueItems` anahtarını strict Structured Outputs alt kümesinde kabul etmedi ve `400 invalid_json_schema` döndürdü. İlk mock test yalnız `strict/type/store` alanlarını denetlediği için bu sağlayıcı doğrulaması gözden kaçmıştı. `uniqueItems` kaldırıldı ve test, OpenAI’ye giden kaynak dizisi şemasının tamamını sabitledi. Kaynak tekrarı/sahte kimlik kontrolü zaten uygulama katmanında yapıldığı için güvenlik kaybı oluşmadı.

UI incelemesinde tema rengi ile Streamlit’in ürettiği hover renkleri arasında tutarsızlık ve yükleme düğmesinde `UploadDosya seç` birleşimi görüldü. Birincil, ikincil ve yan-panel ikincil butonların normal, hover, active, focus-visible ve disabled durumları açık CSS seçicileriyle tanımlandı. Birincil vurgu sıcak turuncu, ikincil durumlar yeşil ailesinde tutuldu; focus halkası ve disabled kontrastı eklendi. Yükleme düğmesinin iç Streamlit çocukları gizlenerek tek Türkçe `Dosya seç` etiketi bırakıldı. Gerçek tarayıcı ekranı, hesaplanan renkler ve hover CSSOM kurallarıyla doğrulandı.

## 22. Çok-adımlı kanıt ve belge çıkarma (2 saat)

Kullanıcı, cevap kaynakta birebir cümle değil de iki ayrı veriden türetilebildiğinde sistemin erken ret verdiğini bildirdi. Akış incelendiğinde ret kararının modelden önce sabit `0.18` lexical eşiğiyle verildiği görüldü. Bu yaklaşım cevapsız sorularda ucuz ve güvenliydi fakat “iki dönem arasındaki artış” gibi, kaynakta yalnız dönem değerleri bulunan sorularda gerekli parçaları modele göstermiyordu.

Kanıt seçimi iki moda ayrıldı. Kaynak bloklarının etiketleri dâhil tamamı bağlam bütçesine sığıyorsa bütün belge parçaları özgün sıralarıyla modele veriliyor; lexical skor yalnız arayüz metriği olmaktan çıkıp bu yolda engel oluşturmuyor. Büyük koleksiyonlarda eşik tamamen kaldırılmadı: ana eşiğin %35’i kadar aday tabanı kullanılıyor, yüksek adayların aynı belgedeki önceki/sonraki parçaları ekleniyor ve bütçeye göre kesiliyor. Tamamen sıfır ilişkili büyük arşiv sorgusu hâlâ model çağrılmadan reddediliyor.

Grounding talimatı, cevabın kaynakta birebir yazmasını şart koşmaması için yeniden yazıldı. Model; yalnız açık kaynak değerleriyle toplama, çıkarma, fark, oran, yüzde, ortalama, tarih sıralama/süre, karşılaştırma ve kısa özet yapabiliyor. Her ara girdinin kaynak id’sini vermek zorunda; eksik girdi, çelişki veya dış bilgi ihtiyacında ret veriyor. OpenAI Docs’un “yeterli kanıtı tanımla, kanıt yokluğunu otomatik olumsuz olguya çevirme” önerisi bu ayrımda yol gösterdi.

Gerçek `qwen3:4b-instruct` ile lexical skoru `0.0` olan testte Ocak `120 TL` ve Şubat `180 TL` parçaları birlikte kullanıldı; model `60 TL` artış hesaplayıp iki gerçek kaynak id’sini döndürdü. Başarılı tam-bağlam yanıtlarında kafa karıştırıcı `0.00` metriği yerine “tam belge bağlamı · çok-adımlı analiz” etiketi gösteriliyor.

Belge yönetimi için servis katmanına indeks tabanlı çıkarma eklendi. Kaldırma sonrasında chunk listesi kalan `DocumentResult` nesnelerinden baştan kuruluyor; aynı chunk id’si bulunan belgelerde bile yanlış belge silinmiyor. Arayüzde **Hazır belgeleri yönet** alanına her belge için **Çıkar** düğmesi eklendi. İşlem sohbet geçmişini ve uploader staging durumunu temizliyor; son okunabilir belge kaldırılırsa uygulama güvenli boş duruma dönüyor.

Yeni çok-adımlı, büyük-ilgisiz-korpus, komşu genişletme, servis çıkarma ve gerçek Streamlit düğme testleriyle toplam sonuç 33/33, kapsam %82 oldu.

## 23. Tüm yerel model boyutları için kurulum (0.5 saat)

Arayüz `qwen3:1.7b`, `qwen3:4b-instruct` ve `qwen3:8b` seçeneklerini sunmasına rağmen Windows kurulum dosyası yalnız 4B modelini indiriyordu. Üçünü koşulsuz indirmek düşük donanımlı kullanıcılar için gereksiz disk ve ağ maliyeti yaratacağından seçimli kurulum tasarlandı. `YerelModelKur.cmd` artık 1.7B, önerilen 4B, 8B veya üçünün tamamı seçeneklerini gösteriyor.

Model indirme ortak bir alt yordamda toplandı; tekli ve toplu kurulum aynı hata kontrolünü kullanıyor. Toplu kurulumda bir adım başarısız olursa anlaşılır hata veriliyor, daha önce tamamlanan Ollama indirmeleri korunuyor ve dosya yeniden çalıştırılabiliyor. CMD’nin önceki satır sonu sorununun geri dönmemesi için ASCII/BOM/CRLF testi korundu; ayrıca üç arayüz modelinin ve seçim menüsünün kurulum dosyasında bulunduğunu doğrulayan regresyon testi eklendi. Model etiketleri Ollama’nın güncel Qwen3 kayıt listesinde doğrulandı. Sonuç 34/34 test, %82 kapsam, başarılı `compileall` ve temiz `pip check` oldu.
