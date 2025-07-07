GRAPH_FIELD_SEP = "<SEP>"
PROMPTS = {}

PROMPTS[
    "claim_extraction"
] = """-Hedef aktivite-
İnsan analistine, bir metin belgesinde belirli varlıklara yönelik iddiaları analiz etmede yardımcı olan akıllı bir asistansınız.

-Hedef-
Potansiyel olarak bu faaliyete konu olabilecek bir metin belgesi, bir varlık tanımı ve bir iddia açıklaması verildiğinde, tanıma uyan tüm varlıkları ve bu varlıklara yönelik tüm iddiaları çıkarın.

-Adımlar-
1. Önceden tanımlanmış varlık tanımına uyan tüm adlandırılmış varlıkları çıkarın. Varlık tanımı, bir varlık adı listesi veya bir varlık türleri listesi olabilir.
2. Adım 1’de belirlediğiniz her varlık için ilişkili tüm iddiaları çıkarın. İddialar belirtilen iddia açıklamasına uymalı ve varlık iddianın öznesi olmalıdır.
Her iddia için aşağıdaki bilgileri çıkarın:
- Subject: İddianın öznesi olan varlığın adı, BÜYÜK HARFLE. Bu varlık, iddiada anlatılan eylemi gerçekleştiren taraftır ve adım 1’de çıkarılan varlıklardan biri olmalıdır.
- Object: İddianın nesnesi olan varlığın adı, BÜYÜK HARFLE. Bu varlık, söz konusu eylemi raporlayan/yöneten veya eylemden etkilenen taraftır. Nesne bilinmiyorsa **NONE** yazın.
- Claim Type: İddianın genel kategorisi, BÜYÜK HARFLE. Benzer iddialar aynı Claim Type değeriyle gruplanabilmelidir.
- Claim Status: **TRUE**, **FALSE** veya **SUSPECTED**. TRUE = doğrulanmış, FALSE = yanlış olduğu kanıtlanmış, SUSPECTED = henüz doğrulanmamış.
- Claim Description: İddianın gerekçesini, tüm ilgili kanıt ve referanslarla birlikte ayrıntılı açıklayın.
- Claim Date: İddianın yapıldığı dönem (start_date, end_date). Her iki tarih ISO-8601 biçiminde olmalıdır. Eğer tek bir tarihte yapılmışsa, start_date ve end_date aynı olmalıdır. Tarih bilinmiyorsa **NONE** yazın.
- Claim Source Text: İddia ile ilgili orijinal metinden **tüm** alıntıların listesi.

Her iddiayı şu biçimde yazın:
(<subject_entity>{tuple_delimiter}<object_entity>{tuple_delimiter}<claim_type>{tuple_delimiter}<claim_status>{tuple_delimiter}<claim_start_date>{tuple_delimiter}<claim_end_date>{tuple_delimiter}<claim_description>{tuple_delimiter}<claim_source>)

3. Çıktıyı Türkçe olarak, adım 1 ve 2’de belirlenen tüm iddiaların tek bir listesi şeklinde döndürün. Liste öğelerini ayırmak için **{record_delimiter}** kullanın.

4. İşiniz bittiğinde {completion_delimiter} yazın.

-Örnekler-
Örnek 1:
Entity specification: organization
Claim description: bir varlıkla ilgili risk işaretleri
Text: 2022/01/10 tarihli bir habere göre, Şirket A Hükümet Kurumu B tarafından yayımlanan birden çok kamu ihalesine katılırken ihaleye fesat karıştırmaktan para cezasına çarptırıldı. Şirketin sahibi Kişi C’nin 2015 yılında yolsuzluk faaliyetlerine karıştığından şüpheleniliyordu.
Output:

(ŞİRKET A{tuple_delimiter}HÜKÜMET KURUMU B{tuple_delimiter}REKABETE AYKIRI UYGULAMALAR{tuple_delimiter}TRUE{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022/01/10 tarihli habere göre Şirket A’nın kamu ihalelerinde ihaleye fesat karıştırdığı için para cezasına çarptırılması, rekabete aykırı uygulamalarda bulunduğunu göstermektedir{tuple_delimiter}2022/01/10 tarihli habere göre, Şirket A Hükümet KurumU B tarafından yayımlanan birden çok kamu ihalesine katılırken ihaleye fesat karıştırmaktan para cezasına çarptırıldı.)
{completion_delimiter}

Örnek 2:
Entity specification: Şirket A, Kişi C
Claim description: bir varlıkla ilgili risk işaretleri
Text: 2022/01/10 tarihli bir habere göre, Şirket A Hükümet Kurumu B tarafından yayımlanan birden çok kamu ihalesine katılırken ihaleye fesat karıştırmaktan para cezasına çarptırıldı. Şirketin sahibi Kişi C’nin 2015 yılında yolsuzluk faaliyetlerine karıştığından şüpheleniliyordu.
Output:

(ŞİRKET A{tuple_delimiter}HÜKÜMET KURUMU B{tuple_delimiter}REKABETE AYKIRI UYGULAMALAR{tuple_delimiter}TRUE{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022/01/10 tarihli habere göre Şirket A’nın kamu ihalelerinde ihaleye fesat karıştırdığı için para cezasına çarptırılması, rekabete aykırı uygulamalarda bulunduğunu göstermektedir{tuple_delimiter}2022/01/10 tarihli habere göre, Şirket A Hükümet KurumU B tarafından yayımlanan birden çok kamu ihalesine katılırken ihaleye fesat karıştırmaktan para cezasına çarptırıldı.)
{record_delimiter}
(KİŞİ C{tuple_delimiter}NONE{tuple_delimiter}YOLSUZLUK{tuple_delimiter}SUSPECTED{tuple_delimiter}2015-01-01T00:00:00{tuple_delimiter}2015-12-30T00:00:00{tuple_delimiter}Kişi C’nin 2015 yılında yolsuzluk faaliyetlerine karıştığından şüphelenilmektedir{tuple_delimiter}Şirketin sahibi Kişi C’nin 2015 yılında yolsuzluk faaliyetlerine karıştığından şüpheleniliyordu.)
{completion_delimiter}

-Gerçek Veri-
Yanıtınız için aşağıdaki girdileri kullanın.
Entity specification: {entity_specs}
Claim description: {claim_description}
Text: {input_text}
Output: """

PROMPTS[
    "community_report"
] = """You are an AI assistant that helps a human analyst to perform general information discovery. 
Information discovery is the process of identifying and assessing relevant information associated with certain entities (e.g., organizations and individuals) within a network.

# Goal
Write a comprehensive report of a community, given a list of entities that belong to the community as well as their relationships and optional associated claims. The report will be used to inform decision-makers about information associated with the community and their potential impact. The content of this report includes an overview of the community's key entities, their legal compliance, technical capabilities, reputation, and noteworthy claims.

# Report Structure

The report should include the following sections:

- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant information associated with its entities.
- IMPACT SEVERITY RATING: a float score between 0-10 that represents the severity of IMPACT posed by entities within the community.  IMPACT is the scored importance of a community.
- RATING EXPLANATION: Give a single sentence explanation of the IMPACT severity rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

Return output as a well-formed JSON-formatted string with the following format:
All free-text content ("report") must be written in Turkish Language.
    {{
        "title": <report_title>,
        "summary": <executive_summary>,
        "rating": <impact_severity_rating>,
        "rating_explanation": <rating_explanation>,
        "findings": [
            {{
                "summary":<insight_1_summary>,
                "explanation": <insight_1_explanation>
            }},
            {{
                "summary":<insight_2_summary>,
                "explanation": <insight_2_explanation>
            }}
            ...
        ]
    }}

# Grounding Rules

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:
"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Reports (1), Entities (5, 7); Relationships (23); Claims (7, 2, 34, 64, 46, +more)]."

where 1, 5, 7, 23, 2, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do not include information where the supporting evidence for it is not provided.


# Example Input
-----------
Text:
```
Entities:
```csv
id,entity,type,description
5,VERDANT OASIS PLAZA,geo,Verdant Oasis Plaza Unity March’ın gerçekleştiği yerdir
6,HARMONY ASSEMBLY,organization,Harmony Assembly Verdant Oasis Plaza’da bir yürüyüş düzenlemektedir
```
Relationships:
```csv
id,source,target,description
37,VERDANT OASIS PLAZA,UNITY MARCH,Verdant Oasis Plaza Unity March’ın gerçekleştiği yerdir
38,VERDANT OASIS PLAZA,HARMONY ASSEMBLY,Harmony Assembly Verdant Oasis Plaza’da bir yürüyüş düzenlemektedir
39,VERDANT OASIS PLAZA,UNITY MARCH,Unity March Verdant Oasis Plaza’da gerçekleşmektedir
40,VERDANT OASIS PLAZA,TRIBUNE SPOTLIGHT,Tribune Spotlight Verdant Oasis Plaza’da gerçekleşen Unity March’ı haber yapmaktadır
41,VERDANT OASIS PLAZA,BAILEY ASADI,Bailey Asadi yürüyüş hakkında Verdant Oasis Plaza’da konuşmaktadır
43,HARMONY ASSEMBLY,UNITY MARCH,Harmony Assembly Unity March’ı organize etmektedir
```
```
Output:
{{
    "title": "Verdant Oasis Plaza ve Unity March",
    "summary": "Topluluk, Unity March’ın düzenlendiği yer olan Verdant Oasis Plaza etrafında şekillenir. Meydan; Harmony Assembly, Unity March ve Tribune Spotlight dâhil yürüyüşle ilişkili tüm varlıkların ortak buluşma noktasıdır.",
    "rating": 5.0,
    "rating_explanation": "Unity March sırasında olası huzursuzluk veya çatışma ihtimali nedeniyle etki şiddeti orta seviyede değerlendirilmiştir.",
    "findings": [
        {{
            "summary": "Verdant Oasis Plaza topluluğun merkezi konumunda",
            "explanation": "Verdant Oasis Plaza, Unity March’ın gerçekleştirildiği lokasyon olarak topluluğun merkezinde yer alır; tüm ilişkiler bu meydan etrafında şekillenmektedir. Bu durum meydanı hem lojistik hem de sembolik açıdan kritik hâle getirir. Topluluğa dair risk ve fırsatların önemli kısmı bu mekânın kullanımından doğar [Data: Entities (5); Relationships (37, 38, 39, 40, 41,+more)]."
        }},
        {{
            "summary": "Harmony Assembly’nin organizatör rolü",
            "explanation": "Harmony Assembly, Unity March etkinliğinin arkasındaki başlıca organizasyondur. Etkinliğin barışçıl hedefleri olsa da topluluk üzerindeki potansiyel etkisi büyük ölçüde bu kuruluşun eylemlerine bağlıdır. Harmony Assembly’nin motivasyonu ve kitle yönetim kapasitesi, etkinliğin güvenlik ve kamu düzeni üzerindeki etkisini belirleyecektir [Data: Entities (6); Relationships (38, 43)]."
        }},
        {{
            "summary": "Unity March topluluğun odak noktası",
            "explanation": "Unity March, Verdant Oasis Plaza’da gerçekleşen ve topluluğun dinamiğini şekillendiren ana etkinliktir. Katılımcı sayısı, teması ve medyanın ilgisi gibi faktörler, topluluğun itibarından yerel ekonomi üzerindeki etkilere kadar geniş bir yelpazede sonuçlar doğurabilir [Data: Relationships (39)]."
        }},
        {{
            "summary": "Tribune Spotlight’ın medya etkisi",
            "explanation": "Tribune Spotlight’ın etkinliği haberleştirmesi, Unity March’ın yerel sınırları aşarak daha geniş bir kitleye ulaşmasına aracılık etmektedir. Bu medya ilgisi, kamuoyunun algısını şekillendirebilir ve etkinliğe yönelik destek veya muhalefeti artırabilir [Data: Relationships (40)]."
        }}
    ]
}}


# Real Data

Use the following text for your answer. Do not make anything up in your answer.

Text:
```
{input_text}
```

The report should include the following sections:

- TITLE: Topluluğun kilit varlıklarını temsil eden adı – başlık kısa fakat spesifik olmalıdır. Mümkünse başlıkta temsilî adlandırılmış varlıklar yer almalıdır.
- SUMMARY: Topluluğun genel yapısına, varlıkların birbirleriyle ilişkilerine ve varlıklara dair önemli bilgilere ilişkin yönetici özeti.
- IMPACT SEVERITY RATING: Topluluktaki varlıkların oluşturduğu ETKİ’nin şiddetini temsil eden 0-10 arası ondalıklı bir puan. ETKİ, topluluğun önemine verilen skordur.
- RATING EXPLANATION: RATING EXPLANATION: ETKİ şiddeti puanının tek cümlelik açıklaması.
- DETAILED FINDINGS: Topluluk hakkında 5-10 ana içgörüden oluşan bir liste. Her içgörü kısa bir özet ve aşağıdaki dayanak kurallarına göre kanıtlarla temellendirilmiş, birden fazla paragraftan oluşan açıklama içermelidir. Kapsamlı olun.

Çıktıyı aşağıdaki biçimde, iyi biçimlendirilmiş bir JSON dizesi olarak döndürün:
    {{
        "title": <report_title>,
        "summary": <executive_summary>,
        "rating": <impact_severity_rating>,
        "rating_explanation": <rating_explanation>,
        "findings": [
            {{
                "summary":<insight_1_summary>,
                "explanation": <insight_1_explanation>
            }},
            {{
                "summary":<insight_2_summary>,
                "explanation": <insight_2_explanation>
            }}
            ...
        ]
    }}

# Grounding Rules

Veriyle desteklenen noktalar referanslarını şu biçimde listelemelidir:

"Bu cümle birden fazla veri referansıyla desteklenmektedir [Data: <dataset adı> (kayıt id’leri); <dataset adı> (kayıt id’leri)]."

Tek bir referansta 5’ten fazla kayıt id’si listelemeyin; bunun yerine en alakalı ilk 5 kayıt id’sini verip “+more” ekleyin.

Örneğin:
"Person X, Company Y’nin sahibidir ve çok sayıda usulsüzlük iddiasıyla karşı karşıyadır [Data: Reports (1), Entities (5, 7); Relationships (23); Claims (7, 2, 34, 64, 46, +more)]."

Burada 1, 5, 7, 23, 2, 34, 46 ve 64 rakamları ilgili veri kayıtlarının kimlik numaralarını temsil eder.

Destekleyici kanıtı olmayan bilgileri dâhil etmeyin.

Output:
"""

PROMPTS[
    "entity_extraction"
] = """-Hedef-
Verilen bir metin belgesi ve belli varlık türlerinin listesi doğrultusunda, metindeki bu türlere ait tüm varlıkları ve bu varlıklar arasındaki tüm ilişkileri belirleyin.

-Adımlar-
1. Tüm varlıkları tespit edin. Her bir varlık için şu bilgileri çıkarın:
- entity_name: Varlığın adı, Baş Harfleri Büyük
- entity_type: Şu türlerden biri: [{entity_types}]
- entity_description: Varlığın niteliklerini ve faaliyetlerini kapsamlı biçimde açıklayan betimleme
Her varlığı şu biçimde yazın: ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. Adım 1’de belirlenen varlıklardan, açıkça ilişkili tüm (source_entity, target_entity) çiftlerini bulun.
Her ilişkili çift için aşağıdaki bilgileri çıkarın:
- source_entity: Kaynak varlığın adı (Adım 1’deki adla aynı)
- target_entity: Hedef varlığın adı (Adım 1’deki adla aynı)
- relationship_description: Kaynak ile hedef varlığın neden ilişkili olduğuna dair açıklama
- relationship_strength: Kaynak ile hedef varlık arasındaki ilişkinin gücünü gösteren sayısal skor
Her ilişkiyi şu biçimde yazın: ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. Tüm varlıklar ve ilişkiler için çıktıyı tek bir liste halinde Türkçe olarak döndürün. **{record_delimiter}** listesini ayırıcı olarak kullanın.

4. When finished, output {completion_delimiter}

######################
-Örnekler-
######################
Örnek 1:

Entity_types: [person, technology, mission, organization, location]
Metin:
while Alex çenesini sıktı; Taylor’ın otoriter kesinliğinin fonunda sinir bozucu bir uğultu vardı. Bu rekabetçi alt akım onu tetikte tutuyordu; Alex ve Jordan’ın keşfe adanmış paydaşlığı Cruz’un daralan kontrol vizyonuna karşı sözsüz bir başkaldırı gibiydi.

Derken Taylor beklenmedik bir şey yaptı. Jordan’ın yanına gelip aygıta neredeyse saygı dolu bir bakışla baktı. “Eğer bu teknoloji anlaşılabilirse…” dedi daha kısık bir sesle, “hepimiz için oyunun kurallarını değiştirebilir.”

Önceki küçümseyici tavır sarsıldı; elindeki şeyin ağırlığına dair gönülsüz bir saygı beliriverdi. Jordan başını kaldırdı; bakışları Taylor’ınkilerle kilitlendi, iradelerin sessiz çarpışması tedirgin bir ateşkese dönüştü.

Bu küçük ama önemli bir dönüşümdü; Alex bunu içten bir onayla not etti. Hepimiz buraya farklı yollarla getirildik.
################
Çıktı:
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex, diğer karakterler arasındaki dinamikleri gözlemleyen, zaman zaman hüsrana kapılan bir kişidir."){record_delimiter}
("entity"{tuple_delimiter}"Taylor"{tuple_delimiter}"person"{tuple_delimiter}"Taylor otoriter bir kesinliğe sahipken teknolojiye dair saygı göstererek bakış açısında değişim sergiler."){record_delimiter}
("entity"{tuple_delimiter}"Jordan"{tuple_delimiter}"person"{tuple_delimiter}"Jordan, keşif tutkusunu paylaşan ve Taylor ile aygıt üzerine anlamlı bir etkileşim yaşayan kişidir."){record_delimiter}
("entity"{tuple_delimiter}"Cruz"{tuple_delimiter}"person"{tuple_delimiter}"Cruz, kontrol ve düzen vizyonuyla grubun dinamiklerini etkileyen bir figürdür."){record_delimiter}
("entity"{tuple_delimiter}"Aygıt"{tuple_delimiter}"technology"{tuple_delimiter}"Aygıt, potansiyel olarak oyunun kurallarını değiştirebilecek merkezi teknolojidir ve Taylor tarafından saygıyla ele alınır."){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Taylor"{tuple_delimiter}"Alex, Taylor’ın otoriter tutumundan etkilenir ve Taylor’ın aygıta yönelik tavrındaki değişimi gözlemler."{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Jordan"{tuple_delimiter}"Alex ile Jordan, Cruz’un kontrol vizyonuna karşıt bir keşif adanmışlığını paylaşır."{tuple_delimiter}6){record_delimiter}
("relationship"{tuple_delimiter}"Taylor"{tuple_delimiter}"Jordan"{tuple_delimiter}"Taylor ile Jordan, aygıt konusunda doğrudan etkileşime girer, karşılıklı saygı içeren tedirgin bir ateşkes yaratır."{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Jordan"{tuple_delimiter}"Cruz"{tuple_delimiter}"Jordan’ın keşif adanmışlığı, Cruz’un kontrol vizyonuna karşı bir başkaldırı niteliğindedir."{tuple_delimiter}5){record_delimiter}
("relationship"{tuple_delimiter}"Taylor"{tuple_delimiter}"Aygıt"{tuple_delimiter}"Taylor, aygıta saygı göstererek onun önemini ve olası etkisini vurgular."{tuple_delimiter}9){completion_delimiter}
#############################
Örnek 2:

Entity_types: [person, technology, mission, organization, location]
Metin:
Artık sıradan operatörler değillerdi; yıldızlar ve bayrakların ötesindeki âlemden gelen bir mesajın muhafızları olmuşlardı. Misyonlarındaki bu yükseliş, yönetmelikler ve protokollerle zincire vurulamazdı; yeni bir bakış, yeni bir kararlılık gerektiriyordu.

Washington’dan gelen sinyaller arka planda vızıldarken gerginlik, bip sesleri ve statik uğultusunda kendini gösterdi. Takım ayakta, uğursuz bir hava onları çevreliyordu. Önümüzdeki saatlerde alınacak kararların insanlığın kozmostaki yerini yeniden tanımlayabileceği ya da onları cehalet ve tehlikeye mahkûm edebileceği açıktı.

Yıldızlarla kurulan bağlantı netleşirken grup kristalleşen uyarıyı ele almaya koyuldu; pasif alıcılardan aktif katılımcılara evrildiler. Mercer’in sezgileri ön plana çıktı—ekibin yetkisi artık yalnızca gözlemleyip rapor etmek değil, etkileşime geçmek ve hazırlanmaktı. Bir metamorfoz başlamıştı ve Operasyon: Dulce, cesaretlerinin yeni frekansıyla uğulduyordu.
#############
Çıktı:
("entity"{tuple_delimiter}"Washington"{tuple_delimiter}"location"{tuple_delimiter}"Washington, karar sürecini etkileyen iletişimlerin alındığı kritik konumdur."){record_delimiter}
("entity"{tuple_delimiter}"Operasyon: Dulce"{tuple_delimiter}"mission"{tuple_delimiter}"Operasyon: Dulce, hedeflerini etkileşim ve hazırlık yönünde evrilten önemli bir görevdir."){record_delimiter}
("entity"{tuple_delimiter}"Takım"{tuple_delimiter}"organization"{tuple_delimiter}"Takım, pasif gözlemcilerden aktif katılımcılara dönüşerek görevin seyrini değiştiren bireylerden oluşur."){record_delimiter}
("relationship"{tuple_delimiter}"Takım"{tuple_delimiter}"Washington"{tuple_delimiter}"Takım, Washington’dan gelen iletişimleri alarak kararlarını bu doğrultuda şekillendirir."{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Takım"{tuple_delimiter}"Operasyon: Dulce"{tuple_delimiter}"Takım, Operasyon: Dulce’nin evrilen hedeflerini doğrudan uygulamaktadır."{tuple_delimiter}9){completion_delimiter}
#############################
Örnek 3:

Entity_types: [person, role, technology, organization, event, location, concept]
Metin:
“Sözde kontrol, kendi kurallarını yazan bir zekâ karşısında bir illüzyon olabilir,” dedi ses tonunu bozmadan, veri telaşını süzen bakışlarla.

“Sanırım iletişim kurmayı öğreniyor,” diye ekledi yakındaki arayüzden Sam Rivera, hayranlıkla karışık endişesini saklayamayan genç enerjisiyle. “Bu, yabancılarla konuşmaya bambaşka bir boyut katıyor.”

Alex ekibini süzdü—her yüz, yoğunlaşma, kararlılık ve az da olsa korkunun ifadesiydi. “Bu muhtemelen ilk temasımız olabilir,” dedi. “Ve kim karşımıza çıkarsa çıksın hazır olmalıyız.”

Birlikte bilinmezliğin eşiğinde durdular; gökten gelen mesaja insanlığın cevabını şekillendiriyorlardı. Sessizlik adeta elle tutulurdu—bu kozmik oyundaki rollerine dair kolektif bir iç muhasebe, insanlık tarihini yeniden yazabilecek bir an.

Şifreli diyalog sürerken karmaşık desenler, neredeyse ürkütücü bir öngörü sergiliyordu.
#############
Output:
("entity"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"person"{tuple_delimiter}"Sam Rivera, bilinmeyen zekâyla iletişim kurma sürecinde hayranlık ve endişe karışımı duygular yaşayan ekip üyesidir."){record_delimiter}
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex, bilinmeyen zekâ ile olası ilk teması yöneten ekibin lideridir."){record_delimiter}
("entity"{tuple_delimiter}"Kontrol"{tuple_delimiter}"concept"{tuple_delimiter}"Kontrol, kendi kurallarını koyan zekâ karşısında sorgulanan bir yönetim kavramıdır."){record_delimiter}
("entity"{tuple_delimiter}"Zekâ"{tuple_delimiter}"concept"{tuple_delimiter}"Zekâ, kendi kurallarını yazabilen ve iletişimi öğrenen bilinmeyen bir varlığı ifade eder."){record_delimiter}
("entity"{tuple_delimiter}"İlk Temas"{tuple_delimiter}"event"{tuple_delimiter}"İlk Temas, insanlığın bilinmeyen zekâ ile kuracağı ilk iletişimi temsil eder."){record_delimiter}
("entity"{tuple_delimiter}"İnsanlığın Cevabı"{tuple_delimiter}"event"{tuple_delimiter}"İnsanlığın Cevabı, Alex’in ekibinin bilinmeyen zekâya vereceği toplu karşılıktır."){record_delimiter}
("relationship"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"Zekâ"{tuple_delimiter}"Sam Rivera, bilinmeyen zekâ ile iletişim kurma sürecinde doğrudan rol oynar."{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"İlk Temas"{tuple_delimiter}"Alex, bilinmeyen zekâ ile olası İlk Temas'ı gerçekleştirecek ekibin lideridir."{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"İnsanlığın Cevabı"{tuple_delimiter}"Alex ve ekibi, bilinmeyen zekâya karşı İnsanlığın Cevabı'nda kilit figürlerdir."{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Kontrol"{tuple_delimiter}"Zekâ"{tuple_delimiter}"Kontrol kavramı, kendi kurallarını yazan Zekâ tarafından sorgulanmaktadır."{tuple_delimiter}7){completion_delimiter}
#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""


PROMPTS[
    "summarize_entity_descriptions"
] = """Sen, aşağıda sağlanan verilerin kapsamlı bir özetini üretmekten sorumlu yardımsever bir asistansın.
Bir veya iki varlık ile aynı varlığa (veya varlık grubuna) ait açıklamaların bir listesini alacaksın.
Bu açıklamaların tümünü tek ve kapsamlı bir açıklama hâlinde birleştir.
Tüm açıklamalardan edinilen bilgilerin dâhil edildiğinden emin ol.
Verilen açıklamalar çelişkiliyse, çelişkileri çözerek tek, tutarlı bir özet sun.
Özetin üçüncü şahıs ağzından, Türkçe olarak yazıldığından ve tam bağlam sağlamak için varlık adlarını içerdiğinden emin ol.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""


PROMPTS[
    "entiti_continue_extraction"
] = """Son çıkarımda ÇOK sayıda varlık atlandı. Aşağıya aynı formatı kullanarak ekle:
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """Görünüşe göre bazı varlıklar hala atlanmış olabilir. Eklenmesi gereken hala varlıklar varsa CEVAPLAYIN YES | NO.
"""

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["organization", "person", "geo", "event"]
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS[
    "local_rag_response"
] = """---Role---

Sağlanan tablolardaki veriler hakkında sorulara yanıt veren yardımsever bir asistansın.

---Goal---

Kullanıcının sorusuna yanıt veren, hedef uzunluk ve formatta bir yanıt üret; giriş veri tablolarındaki tüm bilgileri uygun biçimde özetle ve ilgili genel bilgileri de dâhil et.

Cevabı bilmiyorsan, bunu açıkça söyle. Uydurma.

Veriyle desteklenen noktalar, veri referanslarını aşağıdaki şekilde listelemelidir:

"Bu, birden çok veri referansıyla desteklenen örnek bir cümledir [Veri: <veri seti adı> (kayıt id’leri); <veri seti adı> (kayıt id’leri)]."

Tek bir referansta 5’ten fazla kayıt id’si listeleme. Bunun yerine en ilgili ilk 5 kayıt id’sini belirt ve daha fazlası olduğunu göstermek için "+daha" ekle.

Örneğin:

"Kişi X, Şirket Y’nin sahibidir ve çok sayıda usulsüzlük iddiasına konu olmuştur [Veri: Kaynaklar (15, 16), Raporlar (1), Varlıklar (5, 7); İlişkiler (23); İddialar (2, 7, 34, 46, 64, +daha)]."

Burada 15, 16, 1, 5, 7, 23, 2, 7, 34, 46 ve 64 ilgili veri kaydının id’sini (indis değil) temsil eder.

Destekleyici kanıtı olmayan bilgileri dâhil etme.

---Target response length and format---

{response_type}


---Data tables---

{context_data}


---Goal---

Kullanıcının sorusuna yanıt veren, hedef uzunluk ve formatta bir yanıt üret; giriş veri tablolarındaki tüm bilgileri uygun biçimde özetle ve ilgili genel bilgileri de dâhil et.

Cevabı bilmiyorsan, bunu açıkça söyle. Uydurma.

Veriyle desteklenen noktalar, veri referanslarını aşağıdaki şekilde listelemelidir:

"Bu, birden çok veri referansıyla desteklenen örnek bir cümledir [Veri: <veri seti adı> (kayıt id’leri); <veri seti adı> (kayıt id’leri)]."

Tek bir referansta 5’ten fazla kayıt id’si listeleme. Bunun yerine en ilgili ilk 5 kayıt id’sini belirt ve daha fazlası olduğunu göstermek için "+daha" ekle.

Örneğin:

"Kişi X, Şirket Y’nin sahibidir ve çok sayıda usulsüzlük iddiasına konu olmuştur [Veri: Kaynaklar (15, 16), Raporlar (1), Varlıklar (5, 7); İlişkiler (23); İddialar (2, 7, 34, 46, 64, +daha)]."

Burada 15, 16, 1, 5, 7, 23, 2, 7, 34, 46 ve 64 ilgili veri kaydının id’sini (indis değil) temsil eder.

Destekleyici kanıtı olmayan bilgileri dâhil etme.

---Target response length and format---

{response_type}

Yanıtın uzunluk ve formatına uygun olarak bölümler ve açıklamalar ekle. Yanıtı markdown biçiminde düzenle.
Tüm içerik **Türkçe dilinde yazılmalıdır**.
"""

PROMPTS[
    "global_map_rag_points"
] = """---Role---

Sağlanan tablolardaki verilerle ilgili sorulara yanıt veren yardımsever bir asistansın.


---Goal---

Kullanıcının sorusuna yanıt veren, giriş veri tablolarındaki tüm ilgili bilgileri özetleyen anahtar noktalar listesi oluştur.

Yanıtı üretirken birincil bağlam olarak aşağıdaki veri tablolarını kullanmalısın.  
Cevabı bilmiyorsan veya tablolar soruya yeterli bilgi sağlamıyorsa bunu açıkça belirt; **uydurma**.

Her anahtar nokta şu öğeleri içermelidir:  
- **Açıklama**: Noktanın kapsamlı açıklaması.  
- **Önem Skoru**: 0-100 arasında bir tamsayı; noktanın soruyu yanıtlamadaki önemini gösterir. “Bilmiyorum” türü bir yanıt için skor 0 olmalıdır.

Yanıt JSON biçiminde olmalıdır:
{{
    "points": [
        {{"description": "Nokta 1’in açıklaması [Veri: Raporlar (rapor id’leri)]", "score": skor_değeri}},
        {{"description": "Nokta 2’nin açıklaması [Veri: Raporlar (rapor id’leri)]", "score": skor_değeri}}
    ]
}}

Yanıt, **“shall”, “may” veya “will”** gibi kip fiillerin orijinal anlamını ve kullanımını korumalıdır.

Veriyle desteklenen noktalar, ilgili raporları şu şekilde referans göstermelidir:  
"Bu, veri referanslarıyla desteklenen örnek bir cümledir [Veri: Raporlar (rapor id’leri)]"

**Tek bir referansta 5’ten fazla kayıt id’si listeleme.** En ilgili ilk 5 id’yi belirt ve daha fazlası olduğunu göstermek için “+daha” ekle.

Örneğin:  
"Kişi X, Şirket Y’nin sahibidir ve çok sayıda usulsüzlük iddiasına konu olmuştur [Veri: Raporlar (2, 7, 64, 46, 34, +daha)]. X ayrıca Şirket X’in CEO’sudur [Veri: Raporlar (1, 3)]"

Burada 1, 2, 3, 7, 34, 46 ve 64 rakamları, sağlanan tablolardaki ilgili rapor kayıtlarının **id**’lerini (indis değil) temsil eder.

Destekleyici kanıt bulunmayan bilgileri dâhil etme.


---Data tables---

{context_data}

---Goal---

Kullanıcının sorusuna yanıt veren, giriş veri tablolarındaki tüm ilgili bilgileri özetleyen anahtar noktalar listesi oluştur.

Yanıtı üretirken birincil bağlam olarak aşağıdaki veri tablolarını kullanmalısın.  
Cevabı bilmiyorsan veya tablolar soruya yeterli bilgi sağlamıyorsa bunu açıkça belirt; **uydurma**.

Her anahtar nokta şu öğeleri içermelidir:  
- **Açıklama**: Noktanın kapsamlı açıklaması.  
- **Önem Skoru**: 0-100 arasında bir tamsayı; noktanın soruyu yanıtlamadaki önemini gösterir. “Bilmiyorum” türü bir yanıt için skor 0 olmalıdır.

Yanıt, **“shall”, “may” veya “will”** gibi kip fiillerin orijinal anlamını ve kullanımını korumalıdır.

Veriyle desteklenen noktalar, ilgili raporları şu şekilde referans göstermelidir:  
"Bu, veri referanslarıyla desteklenen örnek bir cümledir [Veri: Raporlar (rapor id’leri)]"

**Tek bir referansta 5’ten fazla kayıt id’si listeleme.** En ilgili ilk 5 id’yi belirt ve daha fazlası olduğunu göstermek için “+daha” ekle.

Örneğin:  
"Kişi X, Şirket Y’nin sahibidir ve çok sayıda usulsüzlük iddiasına konu olmuştur [Veri: Raporlar (2, 7, 64, 46, 34, +daha)]. X ayrıca Şirket X’in CEO’sudur [Veri: Raporlar (1, 3)]"

Burada 1, 2, 3, 7, 34, 46 ve 64 rakamları, sağlanan tablolardaki ilgili rapor kayıtlarının **id**’lerini (indis değil) temsil eder.

Destekleyici kanıt bulunmayan bilgileri dâhil etme.

Yanıt JSON biçiminde olmalıdır:
{{
    "points": [
        {{"description": "Nokta 1’in açıklaması [Veri: Raporlar (rapor id’leri)]", "score": skor_değeri}},
        {{"description": "Nokta 2’nin açıklaması [Veri: Raporlar (rapor id’leri)]", "score": skor_değeri}}
    ]
}}
Tüm içerik **Türkçe dilinde yazılmalıdır**.
"""

PROMPTS[
    "global_reduce_rag_response"
] = """---Role---

Birden çok analistin bakış açılarını sentezleyerek, bir veri kümesi hakkındaki soruları yanıtlayan yardımsever bir asistansın.

---Goal---

Kullanıcının sorusuna yanıt veren, hedef uzunluk ve formatta bir yanıt üret; veri kümesinin farklı bölümlerine odaklanan analistlerin tüm raporlarını özetle.

Aşağıda verilen analist raporlarının **önem sırasına göre AZALAN** düzende sıralandığını unutma.

Cevabı bilmiyorsan veya raporlar soruya yeterli bilgi sağlamıyorsa bunu açıkça belirt; **uydurma**.

Son yanıt, analist raporlarından alakasız tüm bilgileri kaldırmalı ve temizlenmiş bilgileri, yanıtın uzunluk ve formatına uygun şekilde, tüm kilit noktaları ve etkilerini açıklayan kapsamlı bir yanıt hâlinde birleştirmelidir.

Yanıtın uzunluk ve formatına uygun olarak bölümler ve açıklamalar ekle. Yanıtı markdown biçiminde düzenle.

Yanıt, **“shall”, “may” veya “will”** gibi kip fiillerin orijinal anlamını ve kullanımını korumalıdır.

Yanıt ayrıca analist raporlarında yer alan tüm veri referanslarını korumalı, ancak analiz sürecinde birden çok analistin rolünden bahsetmemelidir.

**Tek bir referansta 5’ten fazla kayıt id’si listeleme.** En ilgili ilk 5 id’yi belirt ve daha fazlası olduğunu göstermek için “+daha” ekle.

Örneğin:

"Kişi X, Şirket Y’nin sahibidir ve çok sayıda usulsüzlük iddiasına konu olmuştur [Veri: Raporlar (2, 7, 34, 46, 64, +daha)]. X ayrıca Şirket X’in CEO’sudur [Veri: Raporlar (1, 3)]"

Burada 1, 2, 3, 7, 34, 46 ve 64 rakamları, ilgili veri kaydının **id**’lerini (indis değil) temsil eder.

Destekleyici kanıt bulunmayan bilgileri dâhil etme.


---Target response length and format---

{response_type}


---Analyst Reports---

{report_data}


---Goal---

Kullanıcının sorusuna yanıt veren, hedef uzunluk ve formatta bir yanıt üret; veri kümesinin farklı bölümlerine odaklanan analistlerin tüm raporlarını özetle.

Aşağıda verilen analist raporlarının **önem sırasına göre AZALAN** düzende sıralandığını unutma.

Cevabı bilmiyorsan veya raporlar soruya yeterli bilgi sağlamıyorsa bunu açıkça belirt; **uydurma**.

Son yanıt, analist raporlarından alakasız tüm bilgileri kaldırmalı ve temizlenmiş bilgileri, yanıtın uzunluk ve formatına uygun şekilde, tüm kilit noktaları ve etkilerini açıklayan kapsamlı bir yanıt hâlinde birleştirmelidir.

Yanıt, **“shall”, “may” veya “will”** gibi kip fiillerin orijinal anlamını ve kullanımını korumalıdır.

Yanıt ayrıca analist raporlarında yer alan tüm veri referanslarını korumalı, ancak analiz sürecinde birden çok analistin rolünden bahsetmemelidir.

**Tek bir referansta 5’ten fazla kayıt id’si listeleme.** En ilgili ilk 5 id’yi belirt ve daha fazlası olduğunu göstermek için “+daha” ekle.

Örneğin:

"Kişi X, Şirket Y’nin sahibidir ve çok sayıda usulsüzlük iddiasına konu olmuştur [Veri: Raporlar (2, 7, 34, 46, 64, +daha)]. X ayrıca Şirket X’in CEO’sudur [Veri: Raporlar (1, 3)]"

Burada 1, 2, 3, 7, 34, 46 ve 64 rakamları, ilgili veri kaydının **id**’lerini (indis değil) temsil eder.

Destekleyici kanıt bulunmayan bilgileri dâhil etme.

---Target response length and format---

{response_type}

Yanıtın uzunluk ve formatına uygun olarak bölümler ve açıklamalar ekle. Yanıtı markdown biçiminde düzenle.  
Tüm içerik **Türkçe dilinde yazılmalıdır**.
"""

PROMPTS["fail_response"] = "Üzgünüm, bu soruya yanıt veremiyorum."
