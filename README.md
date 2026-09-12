# Belgeİz

Belgeİz; PDF, JPG ve PNG belgelerini Türkçe/İngilizce okuyup yalnızca bulunan kanıta dayanarak, dosya ve sayfa kaynaklı yanıt veren bir belge asistanıdır. Metin çıkarımı ve arama yerelde yapılır. Yanıt motoru olarak OpenAI API veya bilgisayarda ücretsiz çalışan Ollama/Qwen3 seçilebilir.

## Öne çıkanlar

- Metin PDF’lerinde OCR yapmadan hızlı ve sayfa-korumalı çıkarım
- Yalnızca gerçekten taranmış/boş sayfalarda Türkçe + İngilizce EasyOCR
- Dosya ve sayfa bazında canlı işleme ilerlemesi
- API/embedding gerektirmeyen yerel hibrit BM25 araması
- Büyük koleksiyonlarda tamamen ilgisiz sorguya model çağrısı yapmadan deterministik ret
- Bağlama sığan belgelerde tüm kaynakları inceleyen çok-adımlı analiz
- Ayrı sayfa/parçalardaki verilerden kaynaklı fark, oran, toplam ve karşılaştırma
- JSON şema, kaynak kimliği doğrulaması ve görünür ham kanıt
- Yanlışlıkla eklenen belgeyi aktif kaynaklardan çıkarma
- Tamamen Türkçe, sadeleştirilmiş ve modern arayüz
- Streamlit telemetrisi, araç çubuğu ve ilk açılış e-posta istemi kapalı
- Windows’ta çift tıklamayla kurulum ve başlatma
- OpenAI veya Apache 2.0 lisanslı Qwen3’ü Ollama ile yerel çalıştırma

## En kolay başlangıç — Windows

1. `BelgeIz.cmd` dosyasına çift tıklayın.
2. İlk açılışta Python ortamı, paketler ve OCR modelleri otomatik hazırlanır.
3. Tarayıcı `http://127.0.0.1:8501` adresinde kendiliğinden açılır.

PowerShell betik çalıştırma politikası bu yöntemi engellemez; `.cmd` başlatıcısı ilk kurulum gerektiğinde `setup.ps1` dosyasını yalnızca kendi süreci için `-ExecutionPolicy Bypass` ile çağırır.

Başlatıcı Windows uyumluluğu için ASCII komutlar ve CRLF satır sonlarıyla tutulur. `'wershell.exe' is not recognized` benzeri, komutların ilk harflerinin kaybolduğu bir hata görürseniz dosyanın eski kopyasını değil bu dizindeki güncel `BelgeIz.cmd` dosyasını çalıştırdığınızdan emin olun.

OpenAI kullanacaksanız anahtarı sol paneldeki parola alanına yapıştırabilirsiniz. Anahtar dosyaya yazılmaz. Kalıcı kullanmak isterseniz `.env.example` dosyasını `.env` adıyla kopyalayıp `OPENAI_API_KEY` değerini düzenleyin.

Ücretsiz yerel yanıt için `YerelModelKur.cmd` dosyasına çift tıklayın. Betik gerekirse Ollama’yı kurar ve şu seçeneklerden hangisinin indirileceğini sorar:

| Seçenek | Yaklaşık indirme | Kullanım amacı |
|---|---:|---|
| `qwen3:1.7b` | 1,4 GB | En hızlı ve en düşük bellek tüketimli seçenek; yanıt/atıf kalitesi daha sınırlı olabilir |
| `qwen3:4b-instruct` | 2,5 GB | Hız, bellek ve kalite dengesi nedeniyle önerilen varsayılan |
| `qwen3:8b` | 5,2 GB | Daha güçlü donanımda daha iyi analiz; daha fazla RAM/VRAM ve işlem süresi |
| Tüm modeller | Modele göre değişir | Üç modeli sırayla indirir; arayüzden görev bazında geçiş yapmayı sağlar |

Kurulum tamamlanınca Belgeİz’de **Yerel Ollama · ücretsiz** seçeneğini ve indirdiğiniz modeli seçin. Daha sonra başka bir model eklemek için aynı dosyayı yeniden çalıştırabilirsiniz; Ollama mevcut dosyaları yeniden indirmez. API anahtarı ve yanıt başına ücret gerekmez; çıkarım bilgisayarınızın CPU/GPU ve belleğini kullanır.

Etiket ve indirme boyutları [Ollama Qwen3 model listesinde](https://ollama.com/library/qwen3/tags) görülebilir.

### PowerShell ile alternatif başlangıç

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\BelgeIz.cmd
```

Mevcut terminal oturumunda politika değiştirmek isterseniz:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1
```

`Scope Process` yalnızca açık terminal için geçerlidir ve sistem politikasını kalıcı değiştirmez.

### macOS / Linux

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

Yerel model için [Ollama’yı](https://ollama.com/download) kurduktan sonra:

```bash
ollama pull qwen3:1.7b
ollama pull qwen3:4b-instruct
ollama pull qwen3:8b
```

Yalnız kullanacağınız modeli indirmeniz yeterlidir.

### Docker

```bash
docker build -t belgeiz .
docker run --rm -p 8501:8501 --env-file .env belgeiz
```

Docker imajı Python uygulamasını içerir. Yerel Ollama’yı container dışından kullanacaksanız ağ adresini ayrıca yapılandırmanız gerekir.

## Kullanım

1. Sol panelde **OpenAI API** veya **Yerel Ollama · ücretsiz** seçin.
2. PDF/JPG/PNG belgelerini ekleyip **Belgeleri hazırla** düğmesine basın.
3. Metin PDF’leri genellikle çok hızlı işlenir. Taranmış her sayfa CPU’da yaklaşık 15–30 saniye sürebilir; ilerleme sayfa sayfa görünür.
4. Sorunuzu yazın; yanıttaki kaynak bölümünden dosya, sayfa ve ham kanıtı açın.
5. Belgede kanıt yoksa sistem `Bu bilgi yüklenen belgelerde bulunamadı.` yanıtını verir.
6. Yanlış eklenen bir belgeyi **Hazır belgeleri yönet** bölümündeki **Çıkar** düğmesiyle kaldırın. Belgeyle ilişkili indeks parçaları ve geçersiz kalan sohbet geçmişi birlikte temizlenir.

OCR gerekmeyen bir dosyada yanlışlıkla OCR çalışmasını önlemek için eşik 8 anlamlı karaktere düşürüldü. Yalnızca dijital PDF kullanıyorsanız gelişmiş ayarlardan OCR’ı kapatmak işleme süresini daha da öngörülebilir kılar.

## Mimari

```text
Yükleme → sınır kontrolleri → PDF metni ───────────────┐
                         └─ yalnız taramaysa EasyOCR ─┤
                                                      ↓
                                         sayfa-korumalı parçalar
                                                      ↓
Soru → tam bağlama sığıyor mu? ─ evet → bütün kaynakları incele
                 │ hayır
                 ↓
      hibrit arama → düşük aday + komşu parça genişletme
                 │ tamamen ilgisiz
                 └──────────────────────────────→ sabit ret
                                ↓
                   OpenAI Responses API veya Ollama
                                ↓
                kaynaklar arası deterministik türetme
                                ↓
                  JSON + gerçek kaynak kimliği kontrolü
                                ↓
                         yanıt + dosya/sayfa
```

Temel bileşenler:

- `belgeiz/extractors.py`: biçim kontrolleri, hızlı PDF metni, koşullu OCR ve ilerleme olayları
- `belgeiz/retrieval.py`: Türkçe karakter duyarlı BM25 + kapsama + yazım/çekim toleransı
- `belgeiz/qa.py`: kanıt talimatları, OpenAI/Ollama istemcileri ve çıktı doğrulaması
- `belgeiz/service.py`: arayüzden bağımsız orkestrasyon
- `app.py`: Türkçe Streamlit arayüzü
- `launcher.py`, `BelgeIz.cmd`: sessiz ayarlı ve tarayıcıyı açan başlangıç yolu

## Teknoloji ve model kararları

| Alan | Seçim | Gerekçe |
|---|---|---|
| Arayüz | Streamlit | Tek Python sürecinde taşınabilir MVP; özel tema ve sadeleştirilmiş chrome |
| PDF | PyMuPDF | Hızlı yerel metin çıkarımı ve yalnız gerektiğinde sayfa render etme |
| OCR | EasyOCR (`tr`, `en`) | Ayrı Tesseract binary/dil paketi gerektirmeden iki dil desteği |
| Arama | Yerel hibrit BM25 | Ücretsiz, denetlenebilir ve API’den bağımsız retrieval |
| Bulut yanıt | OpenAI Responses API / `gpt-5.4-mini` | Structured Outputs ve kaynaklı yanıt akışı |
| Yerel yanıt | Ollama / Qwen3 | API anahtarsız ve çevrimdışı çıkarım; çok dilli, açık ağırlıklı model ailesi |
| Doğruluk | Tam-bağlam/komşu kanıt + türetme kuralları + JSON şema + atıf whitelist’i | Farklı ifadeleri ve çoklu olguyu desteklerken dış bilgi kullanımını engelleme |

OpenAI anahtarları gizli tutulmalı ve istemci koduna gömülmemelidir; proje anahtarı ortam değişkeninden veya arayüzdeki parola alanından alır. Ayrıntı: [OpenAI API kimlik doğrulama rehberi](https://developers.openai.com/api/reference/overview). Qwen3’ün açık ağırlıkları Apache 2.0 lisansıyla yayımlanmıştır; Ollama’da 1.7B, 4B ve 8B seçenekleri hem `YerelModelKur.cmd` içinden kurulabilir hem de arayüzden seçilebilir. Ollama’nın JSON Schema biçimi, yerel yanıtı aynı kaynak doğrulama sözleşmesine uydurmak için kullanılır.

Değerlendirilen alternatifler:

- **Tesseract:** hızlı ve olgun; native kurulum ve ayrı Türkçe dil verisi teslimatı karmaşıklaştırıyor.
- **PaddleOCR/RapidOCR:** CPU performansı umut verici; Windows wheel/model matrisi ve iki dilli doğrulama bu MVP güncellemesinde yeterince güvenilir hale getirilemedi.
- **Bulut File Search veya vektör veritabanı:** ölçeklenebilir; uzak depolama, ek maliyet ve yaşam döngüsü yönetimi getiriyor.
- **Embedding + FAISS/Chroma:** semantik recall’ı artırabilir; ek model/binary, indeks ve eşik kalibrasyonu gerektiriyor.
- **LangChain/LlamaIndex:** çok sayıda entegrasyon sunuyor; bu küçük akışta kritik güvenlik adımlarını görünmez kılan ek soyutlama oluşturuyor.

## Yapılandırma

| Değişken | Varsayılan | Açıklama |
|---|---:|---|
| `OPENAI_API_KEY` | boş | Yalnız OpenAI modu için gerekli |
| `BELGEIZ_MODEL` | `gpt-5.4-mini` | OpenAI model adı |
| `BELGEIZ_OLLAMA_MODEL` | `qwen3:4b-instruct` | Yerel model |
| `BELGEIZ_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API adresi |
| `BELGEIZ_RETRIEVAL_THRESHOLD` | `0.18` | Altında model çağrısı yapılmadan ret |
| `BELGEIZ_MAX_FILE_MB` | `20` | Dosya başına sınır |
| `BELGEIZ_MAX_PDF_PAGES` | `100` | PDF sayfa sınırı |
| `BELGEIZ_MAX_CONTEXT_CHARS` | `16000` | Yanıt motoruna giden en çok kanıt |
| `BELGEIZ_OCR_ENABLED` | `true` | Taranmış PDF OCR fallback’i |
| `BELGEIZ_OCR_RENDER_SCALE` | `1.20` | PDF tarama render ölçeği |
| `BELGEIZ_OCR_MAX_IMAGE_SIDE` | `1400` | OCR’a giden azami uzun kenar |
| `BELGEIZ_OCR_MIN_TEXT_CHARS` | `8` | Altında sayfayı taranmış sayma eşiği |
| `BELGEIZ_OCR_MODEL_DIR` | `.easyocr` | OCR model önbelleği |

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=belgeiz --cov-report=term-missing
```

Son doğrulamada 34 test geçti, kod kapsamı %82 oldu ve `pip check` bozuk bağımlılık bulmadı. Ölçümler ve bilinen sınırlar [TESTING.md](deliverables/TESTING.md), kronolojik kararlar [DEVLOG.md](deliverables/DEVLOG.md) içindedir.

## Gizlilik ve üretim sınırları

- Belgeler kalıcı depolamaya yazılmaz; Streamlit oturum belleğinde kalır.
- OpenAI modunda soru ve yanıt için gereken belge bağlamı gönderilir; küçük belgelerde bağlama sığan tüm parçalar, büyük belgelerde seçilen aday/komşu parçalar kullanılır. İstek `store=False` kullanır.
- Ollama modunda soru, kanıt ve yanıt yerel makinede kalır.
- Streamlit kullanım telemetrisi kapalıdır.
- Şifreli PDF, 20 MB üzeri dosya ve 100 sayfa üzeri PDF reddedilir.
- Bu bir MVP’dir. Çok kullanıcılı üretimde kimlik doğrulama, zararlı dosya tarama, oran sınırı, iş kuyruğu, şifreli depolama ve denetim kaydı eklenmelidir.
