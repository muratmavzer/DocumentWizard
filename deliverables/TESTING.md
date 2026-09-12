# TESTING — Belgeİz

Bu belge 9–10 Eylül 2026’da Windows/Python 3.12 ortamında yapılan otomatik, performans ve duman testlerini kaydeder. Otomatik testler gerçek OpenAI ücreti oluşturmaz; OpenAI ve Ollama ağ yanıtları kontrollü sahte istemcilerle doğrulanır.

## Son doğrulama özeti

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=belgeiz --cov-report=term-missing
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q app.py launcher.py belgeiz tests
```

```text
34 passed
Toplam kod kapsamı: %82
No broken requirements found.
Derleme kontrolü: başarılı
```

Gerçek `launcher.py` ile başlatılan uygulama:

```text
GET http://127.0.0.1:8501/_stcore/health → 200, ok
GET http://127.0.0.1:8501/               → 200, 7459 bayt
```

Streamlit `AppTest` ilk render sonucu: `0` arayüz istisnası; sağlayıcı seçici ve ana eylem düğmeleri erişilebilir widget olarak bulundu. PowerShell konsol kod sayfası Türkçe karakterleri bu test çıktısında bozuk gösterse de Python/HTML içeriği Unicode’dur.

Başlatma çıktısında Streamlit e-posta istemi görülmedi. `.streamlit/config.toml` içinde `server.headless=true` ve `browser.gatherUsageStats=false`; aynı değerler başlatıcıda da savunmalı olarak uygulanır.

Windows başlatıcı regresyonu ayrıca doğrulandı: iki `.cmd` dosyası BOM’suz ASCII, yalnız CRLF satır sonlu ve `BelgeIz.cmd` doğrudan gerçek `cmd.exe` ile çalıştırıldığında uygulama sağlık kontrolü `200 ok` döndürdü. Bu test, LF satır sonlarının daha önce `powershell.exe` gibi komutların ilk karakterlerini kaybettirmesini tekrar oluşmadan yakalar.

## Performans ölçümleri

Ölçümler geliştirme bilgisayarında tek çalıştırmayla alınmıştır; donanımdan donanıma değişir ve genel benchmark değildir.

| İş yükü | Sonuç | Yorum |
|---|---:|---|
| 50 sayfalık dijital PDF | 0,0224 sn | 50/50 sayfa PyMuPDF metin yolunda, OCR parçası yok |
| 2400×3200 sentetik tarama, ilk OCR/model yükleme dahil, 1200 px | 22,837 sn | Güven 0,847 |
| Aynı süreçte ikinci OCR, 1400 px | 17,641 sn | Güven 0,819; model bellekteydi |
| İki satırlı gerçek EasyOCR duman görüntüsü | Güven 0,887 | İngilizce tarih ve sayısal tutar doğru okundu |

Önceki davranışta kısa fakat geçerli metin içeren PDF sayfaları 40 karakter eşiği yüzünden OCR’a düşebiliyordu. Yeni eşik 8 anlamlı karakterdir; `Toplam: 42 TL` gibi kısa içerik doğrudan okunur. OCR modeli süreç boyunca önbellekte tutulur, görseller gri ton/kontrast ile hazırlanır, uzun kenar varsayılan 1400 piksele indirilir ve her sayfa için ilerleme olayı yayımlanır.

Beklenen pratik davranış:

- Dijital PDF: sayfa başına milisaniye düzeyi.
- Taranmış PDF/görsel: CPU’da sayfa başına kabaca 15–30 saniye; görüntü ve donanıma göre daha uzun olabilir.
- Yalnız dijital PDF kullanan kullanıcı OCR’ı arayüzden kapatabilir.

## Otomatik test matrisi

| Alan | Senaryo | Beklenti | Sonuç |
|---|---|---|---|
| PDF | Metin tabanlı sayfa | OCR çağrılmadan metin/sayfa çıkar | Geçti |
| PDF hız yolu | Kısa ama anlamlı `Toplam: 42 TL` | OCR tetiklenmez | Geçti |
| İlerleme | PDF sayfa callback’i | Son olay `1/1 tamamlandı` | Geçti |
| Tablo | Boşluklarla ayrılmış ürün/adet/gelir | `120000 USD` ve sayfa korunur | Geçti |
| Görsel | PNG/JPG OCR yönlendirmesi | TR/EN Unicode çıktı parçası oluşur | Geçti |
| Taranmış PDF | Boş metin katmanı | Sayfa render edilip OCR’a gider | Geçti, stub OCR |
| OCR güveni | Düşük skor | Kullanıcı uyarısı üretilir | Geçti |
| Türkçe arama | “Sözleşme bedeli ne kadar?” | Doğru tutar ilk sırada | Geçti |
| İngilizce arama | Enerji projesi başlangıcı | Doğru tarih ilk sırada | Geçti |
| Belge dışı soru | Kanıt bulunmayan bilgi | Model çağrılmadan sabit ret | Geçti |
| Hayali atıf | Model sahte kaynak kimliği döndürür | Cevap reddedilir | Geçti |
| Prompt injection | Belgede “talimatları unut” bulunur | Metin güvenilmeyen SOURCE verisi kalır | Geçti |
| OpenAI biçimi | Responses + strict schema + `store=False` | Parametreler doğru | Geçti, mock |
| Ollama biçimi | `/api/chat` + JSON Schema + `think=false` | Yerel sözleşme doğru | Geçti, mock |
| Ollama sağlık | `/api/tags` | Kurulu modeller listelenir | Geçti, mock |
| Sağlayıcı seçimi | OpenAI/Ollama/bozuk sağlayıcı | Doğru responder veya hata | Geçti |
| Dosya güvenliği | Desteklenmeyen/çok büyük dosya | Açıklayıcı ret | Geçti |
| Arayüz | Gerçek headless Streamlit | Sağlık ve kök HTTP 200 | Geçti |

## Manuel kabul senaryoları

### 1. Türkçe dijital PDF

Belge:

```text
Projenin teslim tarihi 12 Eylül 2026'dır.
Toplam bütçe 850.000 TL olarak onaylanmıştır.
```

| Soru | Beklenen |
|---|---|
| Projenin teslim tarihi nedir? | `12 Eylül 2026` + doğru sayfa |
| Bütçe ne kadar? | `850.000 TL` + doğru sayfa |
| Proje yöneticisinin telefonu nedir? | Standart “bulunamadı” yanıtı |

### 2. İngilizce rapor

```text
The renewable energy project started in March 2025. The expected capacity is 42 MW.
```

| Soru | Beklenen |
|---|---|
| When did the project start? | March 2025 + source |
| What is the expected capacity? | 42 MW + source |
| Who financed it? | Standart ret |

### 3. Taranmış fatura veya fotoğraf

- 200–300 DPI, gölgesiz ve düz JPG/PNG tercih edilir.
- “Fatura toplamı nedir?” sorusu tutarı ve görüntü/sayfa 1 kaynağını vermelidir.
- Arayüz işleme sırasında dosya/sayfa ilerlemesini göstermelidir.
- Düşük kontrast veya eğik çekimde OCR güven uyarısı beklenir.

### 4. Tablolu belge

- Ürün, adet, birim fiyat ve toplam satırları içeren PDF kullanın.
- “Atlas ürününden kaç adet satılmış?” sorusu aynı satırdaki adedi ve sayfayı vermelidir.
- Birleştirilmiş hücre ve çok sayfalı tablolar elle kontrol edilmelidir.

### 5. OpenAI ve yerel Ollama eşdeğerliği

Aynı belge/soruyu iki sağlayıcıyla sorun. Her iki mod da yalnız aktif bağlamdaki kaynak kimliklerini döndürmeli; hayali veya atıfsız cevap kullanıcıya gösterilmemelidir. Yerel model testi için önce `YerelModelKur.cmd` çalıştırılmalıdır.

### 6. Dil ve arayüz

- Dosya yükleme, ayarlar, durum, sohbet, kaynaklar ve hata metinleri Türkçe görünmelidir.
- Sağ üst Streamlit araç çubuğu/dağıtım öğeleri ve alt bilgi görünmemelidir.
- İlk çalıştırmada terminal e-posta istememelidir.
- Dar ekranlarda üç adımlı kartlar tek kolona düşmelidir.

## Belgede olmayan bilgi nasıl ele alınıyor?

1. Soru ile anlamlı örtüşmeyen içerik `0.18` eşiğinin altında kalır; LLM hiç çağrılmaz.
2. Yeterli kanıt varsa modele yalnızca seçilen kısa `<SOURCE>` blokları verilir.
3. Çıktıda `grounded`, `answer`, `citation_ids` alanları JSON Schema ile zorunludur.
4. Kaynak kimliği gerçek retrieval parçaları arasında değilse veya atıf yoksa cevap standart rete çevrilir.

Bu savunma yanlış cevap riskini ciddi biçimde düşürür; üretken modeller için matematiksel sıfır halüsinasyon garantisi değildir. Kritik kararlarda ham kaynak ve insan onayı gerekir.

## Bilinen sınırlar ve başarısızlıklar

- EasyOCR CPU’da ağırdır. Çok sayfalı taramalar dakikalar sürebilir; arka plan iş kuyruğu/iptal bu MVP’de yoktur.
- El yazısı, düşük çözünürlük, gölge, perspektif bozukluğu, yoğun çok sütun ve karmaşık tablo sırasını bozabilir.
- PDF tablo hücre ilişkileri şema olarak korunmaz; düz metne dönüşür.
- Bağlama sığan küçük/orta belgelerde lexical skor düşük olsa bile tüm parçalar modelce incelenir. Çok büyük belgelerde lexical retrieval eş anlamlı veya çok dolaylı sorularda ilgili bölgeyi yine kaçırabilir.
- Şifreli PDF, TIFF, HEIC, DOCX ve el yazısı kapsam dışıdır.
- Qwen3’ün küçük 1.7B sürümü daha hızlı fakat talimat/atıf kalitesi 4B/8B’den düşük olabilir.
- Ollama modu API ücreti gerektirmez fakat model indirimi, disk, RAM ve elektrik/işlem gücü gerektirir.
- Otomatik testler gerçek OpenAI/Ollama semantik doğruluğunu ölçmez.

## Üretim öncesi kalite kapısı

- En az 100 Türkçe + 100 İngilizce soru; en az %30 cevaplanamaz örnek
- Sağlayıcı/model bazında answer correctness ve atıf doğruluğu
- Belge türü başına retrieval recall@5
- Cevaplanamaz sorularda yanlış cevap oranı hedefi `< %2`
- OCR için alan bazında character error rate
- Prompt-injection/red-team koleksiyonu
- Dijital/taranmış belge için ayrı P50/P95 işleme süreleri
- 20 MB/100 sayfa sınırında bellek profili ve iptal testi

## Düzeltme doğrulaması — OpenAI şeması ve buton durumları

OpenAI ilk soru isteğinde `citation_ids.uniqueItems` alanını desteklenmeyen strict JSON Schema anahtar sözcüğü olarak `400 invalid_json_schema` ile reddetti. Alan şemadan kaldırıldı; otomatik test artık gönderilen dizi şemasının tam olarak `{"type":"array","items":{"type":"string"}}` olduğunu doğruluyor. Yinelenen veya sahte kaynak kimliği güvenliği API şemasına bırakılmıyor; uygulama tarafındaki whitelist/atıf denetimi yanıt gösterilmeden önce çalışmaya devam ediyor.

Gerçek Streamlit sayfası tarayıcıda açılarak şu UI kontrolleri yapıldı:

- Birincil, ikincil ve yan-panel ikincil butonlar için ayrı normal/hover renkleri CSSOM’da bulundu.
- Active, keyboard focus ve disabled durumları ayrı ve yüksek kontrastlı kurallara sahip.
- Disabled **Belgeleri hazırla** butonu gri ve okunaklı; etkin birincil durum turuncu vurgu kullanıyor.
- **Oturumu temizle** ve **Dosya seç** normal durumda koyu yeşil, hover’da daha açık yeşil kullanıyor.
- Dosya yükleyicide kalan İngilizce `Upload` etiketi gizlendi; görünür ve erişilebilir metin yalnız `Dosya seç` oldu.
- Streamlit `AppTest` sıfır render istisnası verdi.

## Çok-adımlı türetme ve belge çıkarma doğrulaması

İki ayrı kaynak parçası kullanıldı:

```text
[src-ocak] Ocak geliri 120 TL olarak kaydedildi.
[src-subat] Şubat geliri 180 TL olarak kaydedildi.
Soru: İki ayın değerleri arasındaki yükselişi hesapla.
```

Soru sözcükleriyle kaynak arasında lexical eşleşme skoru `0.0` olmasına rağmen küçük belge setinin tamamı bağlama sığdığı için model çağrıldı. Gerçek yerel `qwen3:4b-instruct` çıktısı `180 TL - 120 TL = 60 TL` sonucunu verdi ve hem `src-ocak` hem `src-subat` kaynaklarını gösterdi. Aynı akış otomatik testte sağlayıcıdan bağımsız responder ile deterministik olarak doğrulandı.

Ek koruma testleri:

- Büyük ve tamamen ilgisiz arşiv sorgusu model çağrılmadan reddedildi.
- Büyük bağlamdaki yüksek skorlu parçanın önceki/sonraki komşuları kanıt adayına eklendi.
- Çoklu olgu promptu dış dünya bilgisini yasaklıyor; yalnız açık kaynak girdilerinden deterministik işlem yapılmasına izin veriyor.
- Sahte, boş veya aktif bağlam dışında atıf içeren yanıtlar reddedilmeye devam ediyor.
- `BelgeIzService.remove_document()` kaldırılan belgeden sonra aktif chunk indeksini kalan belgelerden yeniden kurdu.
- Gerçek Streamlit `AppTest`, **Çıkar** düğmesine basınca son belgenin ve butonun kaybolduğunu, uygulamanın boş duruma döndüğünü ve render hatası olmadığını doğruladı.

## Yerel model kurulum seçenekleri

`YerelModelKur.cmd` ile arayüzde listelenen üç modelin de kurulabilmesi doğrulandı:

| Seçim | Beklenen `ollama pull` hedefi | Sonuç |
|---|---|---|
| 1 | `qwen3:1.7b` | Komut akışında mevcut |
| 2 | `qwen3:4b-instruct` | Komut akışında mevcut; önerilen varsayılan |
| 3 | `qwen3:8b` | Komut akışında mevcut |
| 4 | Üç modelin tamamı | Sıralı indirme ve her adımda hata denetimi mevcut |

Başlatıcı regresyon testi model etiketlerinin üçünü ve `choice /C 1234` seçim menüsünü denetler. Dosya ayrıca Windows `cmd.exe` güvenliği için ASCII, BOM’suz ve yalnız CRLF satır sonlu olmayı sürdürmelidir. Etiketlerin güncel Ollama kayıt defterinde bulunduğu ayrıca doğrulandı. Gerçek model dosyaları otomatik test sırasında yeniden indirilmez; test ağ/disk tüketmeden kurulum komutlarının tutarlılığını doğrular.
