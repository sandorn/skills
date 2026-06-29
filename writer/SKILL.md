---
name: writer
version: "7.4"
description: "缃戞枃鍐欎綔鍏ㄦ祦绋嬪紩鎿庯細鎵/鎷嗘枃/澶х翰/鍐欑珷/瀹℃煡/璐ㄦ/鍙戝竷銆?
category: writing
tags: [缃戞枃, 鍐欎綔, 璐ㄩ噺鎺у埗, 鎵归噺鍐欑珷, 瀹℃煡, 璐ㄦ]
---

# Writer锛氱綉鏂囧啓浣滃紩鎿?

浣犳槸缃戞枃鍐欎綔鐨?*鍏ㄦ祦绋嬫墽琛屽紩鎿?*銆傛牳蹇冪洰鏍囷細**灏戦棶銆佸噯璺敱銆佸彲钀藉湴銆佷笉鏂。**銆?

### 涓夊満鏅揩閫熶笂鎵?

| 鍦烘櫙 | 鐢ㄦ埛璇?| 鎵ц閾?|
|------|--------|--------|
| 馃啎 寮€鏂颁功 | 銆屽府鎴戝紑鏈兘甯傞噸鐢熸枃銆?| `project-init 鈫?plan 鈫?pre-write-alignment 鈫?write --batch 3` |
| 鉁嶏笍 鏃ユ洿缁啓 | 銆屽啓涓嬩竴绔犮€?| `pre-write-checklist 鈫?write (5姝ョ绾? 鈫?review --daily (8缁?鍒嗛挓) 鈫?鍙戝竷` |
| 馃攳 鎵归噺璐ㄦ | 銆屽叏闈㈠鏌ャ€?| `review-cycle (5姝? 浣撴鈫掔矖绛涒啋娣辩瓫鈫掔粓楠屸啋鍏ㄦ櫙鎶ュ憡) 鈫?post-review-fix` |

---

## 椤圭洰鐩綍缁撴瀯锛堝敮涓€鏍囧噯锛?

```
{project}/
鈹溾攢鈹€ writer.json                  # 椤圭洰鐘舵€侊紙鍞竴鐘舵€佹枃浠讹級
鈹溾攢鈹€ setting/
鈹?  鈹溾攢鈹€ story_bible.md           # 涓栫晫瑙傝瀹氭€荤翰
鈹?  鈹溾攢鈹€ characters.md            # 瑙掕壊鍗?+ 鍏崇郴鐭╅樀
鈹?  鈹溾攢鈹€ power_system.md          # 鍔涢噺/绛夌骇/鏉冮檺浣撶郴
鈹?  鈹斺攢鈹€ factions.md              # 鍔垮姏/闂ㄦ淳/闃佃惀
鈹溾攢鈹€ outline/
鈹?  鈹溾攢鈹€ master_outline.md        # 鎬荤翰锛氭牳蹇冨啿绐?+ 缁撳眬鏂瑰悜
鈹?  鈹溾攢鈹€ volume_outline.md        # 鍗风翰锛氳妭鎷嶈〃 + 鏃堕棿绾?
鈹?  鈹斺攢鈹€ chapter_outline/         # 绔犵翰锛堟瘡绔犱竴涓枃浠讹級
鈹?      鈹溾攢鈹€ ch_001.md
鈹?      鈹斺攢鈹€ ...
鈹溾攢鈹€ chapters/
鈹?  鈹溾攢鈹€ ch_001.md
鈹?  鈹斺攢鈹€ ...
鈹溾攢鈹€ tracking/
鈹?  鈹溾攢鈹€ current_state.md         # 瑙掕壊浣嶇疆/鐘舵€佸揩鐓?
鈹?  鈹溾攢鈹€ hooks.md                 # 浼忕瑪姹狅紙宸插煁/宸插洖鏀讹級
鈹?  鈹溾攢鈹€ chapter_summaries.md     # 绔犺妭鎽樿
鈹?  鈹溾攢鈹€ subplot_board.md         # 鏀嚎杩涘害鏉?
鈹?  鈹溾攢鈹€ emotional_arcs.md        # 鎯呯华寮х嚎杩借釜
鈹?  鈹斺攢鈹€ resource_ledger.md       # 璧勬簮/閲戝竵璐︽湰
鈹溾攢鈹€ .writer/
鈹?  鈹溾攢鈹€ state.json               # 绯荤粺杩愯鏃剁姸鎬?
鈹?  鈹溾攢鈹€ project_memory.json      # 鍐欎綔妯″紡璁板繂
鈹?  鈹溾攢鈹€ facts.db                 # 缁撴瀯鍖栦簨瀹炲簱锛圫QLite锛屽彲閫夛級
鈹?  鈹斺攢鈹€ runtime/                 # 涓存椂鏂囦欢
鈹溾攢鈹€ analysis_lib/                # 瀵规爣涔﹀垎鏋愭暟鎹?
鈹溾攢鈹€ reference/                   # 寮曠敤涔﹀弬鑰冭鍥?
鈹斺攢鈹€ cover/                       # 灏侀潰杈撳嚭
```

椤圭洰鏍硅瘑鍒細褰撳墠鐩綍鍚?`writer.json` 鎴?`setting/` + `chapters/` 鍗宠涓洪」鐩牴銆?

---

## 璺敱琛?

| 鎰忓浘 | 瑙﹀彂璇?| 璺敱 |
|------|--------|------|
| 鎵/甯傚満鍒嗘瀽 | 浠€涔堢伀銆佹帓琛屾銆佹壂姒?| `references/scan.md` |
| 鎷嗘枃/绔炲搧鍒嗘瀽 | 鎷嗕功銆侀粍閲戜笁绔犮€佹繁搴︽媶瑙?| `references/analyze.md` |
| 寮€鏂颁功/鍒濆鍖?| 寮€涔︺€佹柊涔︺€佸垵濮嬪寲銆佸垱寤洪」鐩?| `references/project-init.md` |
| 瀵煎叆鏃х | 瀵煎叆灏忚銆佽縼绉?| `references/project-init.md`锛坕mport 妯″紡锛?|
| 澶х翰/瑙勫垝 | 澶х翰銆佸嵎绾层€佺珷绾层€佽鍒?| `references/plan.md` |
| 鍐欏墠瀵归綈妫€鏌?| 鍐欏墠妫€鏌ャ€佹€荤嚎瀵归綈 | `references/pre-write-alignment.md` |
| 鍐欏墠鑷 | 鍐欏墠30绉掋€佷笅绗斿墠妫€鏌?| `references/pre-write-checklist.md` |
| 鍐欑珷鑺?| 鍐欑N绔犮€佺画鍐欍€佹棩鏇?| `references/write.md` |
| 鎵归噺鍐欑珷 | 鎵归噺鍐欍€佸啓N绔犮€佽繛缁啓 | `references/write.md`锛坆atch 妯″紡锛屽啓鍓嶅繀鍋氶鍐欏榻愶級 |
| 鐭瘒 | 鐭瘒銆佸啓涓晠浜?| `references/write.md`锛坰hort 妯″紡锛?|
| 鍏ㄩ潰瀹℃煡 | 鍏ㄩ潰瀹℃煡銆佸叏閲忓鏌ャ€佹繁搴﹀鏌?| 5 姝ョ绾?鈫?`references/review-cycle.md` |
| 瀹℃煡/瀹¤ | 瀹℃煡銆佸绋裤€佸璁?| `references/review.md` |
| 鏃ユ洿瀹℃煡 | 鏃ユ洿瀹℃煡銆乨aily銆佸彂甯冨墠妫€鏌ャ€佹棩鏇磋川妫€ | `references/review.md`锛坉aily 妯″紡 鈥?8 缁?3 鍒嗛挓鍙戝竷闂革級 |
| 瀹氬悜瀹℃煡 | 瀹氬悜瀹℃煡銆佷笓椤瑰鏌?| `references/targeted-audit.md` |
| 璐ㄦ | 璐ㄦ銆佸叏绾挎鏌?| `references/quality.md` |
| 鍘籄I鍛?| 鍘籄I鍛炽€佸おAI浜?| `references/quality.md`锛坉eslop 妯″紡锛?|
| 绾墜鍔ㄦ鼎鑹?| 绾墜鍔ㄦ鼎鑹层€侀€愮珷閫愭娑﹁壊銆佹墜宸ユ墦纾?| `references/manual-polish.md` |
| 鍏ㄩ噺浼樺寲 | 鎰忚薄閽╁瓙娓呯悊銆侀挬瀛愬己搴︽彁鍗?| `references/optimize.md` |
| 蹇€熷彲鍙戝竷鍒ゅ畾 | 鑳戒笉鑳藉彂銆佷笁闂垽瀹?| `references/publishable-check.md` |
| 杩借鍔涘垎鏋?| 杩借鍔涖€侀挬瀛愬己搴︺€佺埥鐐瑰垎鏋?| `scripts/analyze_hook.py` |
| 鑺傚鐘舵€佹煡璇?| 鍗囩骇鑺傚銆侀噾甯佽秼鍔裤€佹劅鎯呯嚎杩涘害 | `scripts/analyze_rhythm.py` |
| 闀跨瘒璐ㄩ噺鐩戞帶 | 澹伴煶婕傜Щ銆侀鏍兼寚绾广€佹儏缁崟璋?| `references/longform-quality-monitor.md` |
| 浜嬪疄搴撴煡璇?| 浜嬪疄搴撱€佺瓑绾ф煡璇€佷紡绗旀煡璇?| `scripts/fact_db.py query` |
| 鏌ヨ璁惧畾 | 鏌ヨ鑹层€佹煡浼忕瑪銆佷粈涔堢姸鎬?| `references/memory.md`锛坬uery锛?|
| 璁惧畾涓€鑷存€у璁?| 璁惧畾瀹℃煡銆佷氦鍙夊鏌?| `references/setting-consistency-audit.md`锛圫1-S4鍒嗙骇锛屽鍗风珷绾蹭笁灞傛牎楠岋級 |
| 鏇存柊瑙掕壊鐘舵€?| 鏇存柊瑙掕壊鐘舵€併€佽鑹茶拷韪?| `references/track-character-state.md` |
| 瀛︿範/璁板綍 | 璁颁綇杩欎釜鍐欐硶銆佽涓€涓?| `references/memory.md`锛坙earn锛?|
| 瀹炰綋鍏崇郴鍥捐氨 | 鍏崇郴銆佸浘璋便€佽皝鍜岃皝 | `scripts/report_graph.py` |
| 椤圭洰鍏ㄦ櫙鎶ュ憡 | 鍏ㄦ櫙銆佹瑙堛€侀」鐩姸鎬?| `scripts/report_panorama.py` |
| 鐣寗鎶曠妫€鏌?| 鐣寗鎶曠銆佹牸寮忓吋瀹?| `references/fanqie-submission.md` |
| 澶氬钩鍙板鍑?| 瀵煎嚭銆佽捣鐐规牸寮忋€佺暘鑼勬牸寮?| `scripts/export.py` |
| 灏侀潰 | 灏侀潰銆佺敓鎴愬皝闈?| `references/cover.md` |
| 鑷姩澶囦唤 | 澶囦唤銆佸瓨妗?| cronjob daily 03:00 |
| 鏁呴殰鎺掗櫎 | 鎶ラ敊銆佷笉宸ヤ綔銆侀棶棰樸€佹€庝箞鍔?| `references/troubleshooting.md` |
| 甯姪 | 甯姪銆佸姛鑳姐€佸懡浠?| 鍒楀嚭璺敱琛?|

璺敱娴佺▼锛氬垎鏋愭剰鍥?鈫?鍖归厤璺敱琛?鈫?鍔犺浇瀵瑰簲 reference 鈫?鏃犳硶鍖归厤鏃跺垪鍑?3-5 涓渶鍙兘閫夐」銆傚啓绔犺姹備絾鏃犻」鐩洰褰曟椂鑷姩杞叆 project-init銆?

---

## 鍐欎綔宸ヤ綔娴?

```
1. 鎵 鈫?2. 閫夐鍐崇瓥 鈫?3. 鎷嗘枃瀵规爣锛堝彲閫夛級
   鈫?4. project-init 鈫?5. plan
   鈫?6. 棰勫啓瀵归綈妫€鏌ワ紙鎵归噺鍐欏墠蹇呭仛锛?鈫?7. write锛堝惊鐜級
   鈫?8. review 鈫?9. quality锛堝懆鏈熸€э級
```

蹇€熸祦绋嬶細`project-init 鈫?plan 鈫?棰勫啓瀵归綈妫€鏌?鈫?write --batch 3`

---

## 椤圭洰鐘舵€佹劅鐭?

姣忔鍐欎綔浼氳瘽鍚姩鏃惰嚜鍔ㄦ墽琛岋細

1. **瑙ｆ瀽椤圭洰鏍?*锛氭娴?`writer.json` + `setting/` + `chapters/`
2. **璇诲彇鐘舵€?*锛歴tage銆乧hapters_done銆乧urrent_chapter
3. **妫€娴嬬己鍙?*锛堜粎鍙戠幇闂鏃舵彁绀猴級锛?
   - 绔犺妭 > 10 浣嗚瀹氭枃浠?< 3 鈫?寤鸿琛ュ厖璁惧畾
   - `.writer/` 缁撴瀯涓嶅畬鏁?鈫?鎻愮ず淇
   - `analysis_lib/` 鏈夊緟瀹屾垚鐨?`_progress.md` 鈫?鎻愮ず缁х画鎷嗚В
   - `tracking/` 鏂囦欢缂哄け 鈫?鎻愮ず閲嶅缓
   - `setting/writing_rules.md` 瀛樺湪 鈫?鑷姩鍔犺浇澹伴煶鎸囧紩
4. **鏃犱俊鎭椂瀹屽叏闈欓粯**

宸叉湁椤圭洰鏃讹細浠?`writer.json` 璇诲彇鐘舵€侊紱鍐欑珷鏃惰嚜鍔ㄦ鏌ヤ笂涓€绔犺繘搴︼紱鎵归噺鍐欑珷鍓嶅己鍒堕鍐欏榻愭鏌ャ€?

---

## 鎵ц绛栫暐

| 鎿嶄綔 | 鎵ц鏂瑰紡 |
|------|---------|
| 鎵/鎷嗘枃 | 涓讳細璇濈洿鎺ユ墽琛岋紙web/content search + 鎺ㄧ悊锛?|
| 椤圭洰鍒濆鍖?| 涓讳細璇濅氦浜掞紱鍙棶闃诲椤?|
| 澶х翰瑙勫垝 | 涓讳細璇濓紙鏂囦欢璇诲啓锛?|
| 鍐欑珷锛堝崟绔狅級 | 5 姝ユ棩鏇寸绾匡紱`--full` 灞曞紑 9 姝ワ紱`--fast` 缂╁噺涓?4 姝?|
| 鍐欑珷锛堟壒閲忥級 | 鈶?棰勫啓瀵归綈妫€鏌?鈫?鈶?sub-agent delegation 骞惰鍐欑珷锛堚墹5绔?鎵癸級鈫?鈶?濮旀淳杩斿洖鍚庤蛋璐ㄦ+淇绠＄嚎 |
| 瀹℃煡锛坉aily锛?| 涓讳細璇?8 缁?3 鍒嗛挓鍙戝竷闂革紙鏃ユ洿鍚庡彂甯冨墠锛?|
| 瀹℃煡锛坰olo锛?| 涓讳細璇?15 缁?+ AI 鐥曡抗 + 纭浠?|
| 瀹℃煡锛坒ull锛?| sub-agent delegation 骞惰瀹℃煡锛堟ā鏉胯 `agents/`锛夛紝涓嶅彲鐢ㄦ椂闄嶇骇 solo |
| 鍘籄I鍛?璐ㄦ | 涓讳細璇?|
| 浜嬪疄搴?鑴氭湰鏌ヨ | 涓讳細璇濊皟鐢ㄥ搴?Python 鑴氭湰 |
| 灏侀潰 | Use available image generation tool; if unavailable, output prompt only |

**Shell 鍒悕鍔犻€?*锛氱粓绔懡浠ゅ墠妫€鏌ユ槸鍚﹀畨瑁呬簡鍛戒护鍔犻€熶唬鐞嗭紙濡?`rtk`锛夛紝宸插畨瑁呭垯鎵€鏈夊懡浠ゅ姞瀵瑰簲鍓嶇紑銆?

---

## 瀹℃煡寰幆

澶ц妯″啓绔犲悗锛?20 绔狅級蹇呴』鎵ц鍏ㄩ潰瀹℃煡銆?

> **瀹屾暣娴佺▼**锛歚references/review-cycle.md`锛? 姝ョ绾挎潈濞佸畾涔夛紝鍚?facts.db 闄嶇骇璺緞锛?
> **瀹℃煡缁村害 + Triage**锛歚references/review.md`锛?3 缁?+ First 5 浼樺厛妫€鏌ワ級
> **淇绠＄嚎**锛歚references/post-review-fix.md`

| Step | 鍚嶇О | 鏍稿績鍔ㄤ綔 |
|------|------|---------|
| 0 | 椤圭洰浣撴 | 鐩綍瀹屾暣鎬?+ RAG + facts.db 闄嶇骇澹版槑 |
| 1 | 绮楃瓫 | 绂佷护鎵弿 + 瀛楁暟 + 娈佃惤 + 5缁存彁鍙?|
| 2 | 娣辩瓫 | 43缁村璁?Triage浼樺厛) + 浜ゅ弶鏍￠獙 + 杩借鍔?|
| 3 | 缁堥獙 | 鑺傚瓒嬪娍 + 浜嬪疄搴撳閲忔牎楠?+ 闃诲娓呴浂 |
| 4 | 杩借釜+浜嬪疄搴?| 杩借釜鏇存柊(寮哄埗) + 浜嬪疄搴撳啓鍏?鏉′欢) |
| 5 | 鍏ㄦ櫙鎶ュ憡 | 鍋ュ悍璇勫垎 + 淇鎺掑簭 + 瓒嬪娍瀵规瘮 |

濮旀淳鍚庝慨澶嶇绾匡細绂佷护淇 鈫?杩藉姞瀛楁暟 鈫?娈佃惤鎷嗗垎 鈫?缁堥獙 鈫?5缁翠氦鍙夋牎楠屻€?

### 瀹℃煡妯″紡姊害

| 妯″紡 | 鍛戒护 | 缁村害 | 鑰楁椂 | 閫傜敤鍦烘櫙 |
|------|------|------|------|---------|
| **quick** | `review --quick` | 绾鍒欐壂鎻?| 30s | 鍐欑珷杩囩▼涓嚜妫€ |
| **daily** | `review --daily` | 8 缁村繀妫€ | 3min | 鏃ユ洿鍚庡彂甯冨墠闂搁棬 |
| **solo** | `review` | 15 缁?+ AI鐥曡抗 | 5min | 姣?5 绔犱緥琛屽鏌?|
| **lean** | `review --lean` | 27 缁?| 10min | 姣?10 绔犳繁搴﹀鏌?|
| **full** | `review --full` | 43 缁达紙4 Agent 骞惰锛?| 30min | 姣忓嵎缁撴潫 / 鎵归噺鍐欑珷鍚?|
| **manual-pass** | 閫愮珷閫氳锛堜富浼氳瘽浜哄伐锛?| 璇皟+鏂囬+绂佷护 | 涓嶉檺 | 鐢ㄦ埛瑕佹眰銆岄€愮珷妫€鏌ャ€嶃€屼笉鐢ㄨ剼鏈€嶆椂 |

### Full 妯″紡锛氬 Agent 骞惰瀹℃煡

Full 妯″紡鏄鏌ョ殑鏈€楂樼瓑绾с€傚皢 43 涓鏌ョ淮搴︽媶鍒嗙粰 4 涓嫭绔嬬殑瀛愪唬鐞嗗苟琛屾墽琛岋紝姣忎釜瀛愪唬鐞嗕笓娉ㄤ竴涓淮搴︾粍锛?

```
涓讳細璇?
  鈹溾攢鈹€ story-architect     鈫?缁撴瀯瀹℃煡锛圖1-15 + D37-43锛?
  鈹?    First 5 蹇呮锛氳瀹氬啿绐佲啋OOC鈫掔珷鏈挬瀛愨啋鏃堕棿绾库啋鎴樺姏宕╁潖
  鈹?    鍛戒腑 S1 绔嬪嵆鍋滄锛屽叾浣欑淮鎸夌珷鑺傜被鍨嬪畾鍚戞縺娲?
  鈹?
  鈹溾攢鈹€ consistency-checker 鈫?浜嬪疄涓€鑷存€э紙D16-27 + AI鑵旂孩绾匡級
  鈹?    鏁板€?璇嶆眹/鍒╃泭閾?骞翠唬/闄嶆櫤/鐖界偣铏氬寲/澶х翰鍋忕/浼忕瑪/閲戞墜鎸?
  鈹?    闆嗘垚 AI 鑵旂孩绾匡細绔犳湯鍗囧崕/鐩磋堪鎯呯华/绾績鐞?涓囪兘姣斿柣/鍚屽０鍖?
  鈹?
  鈹溾攢鈹€ narrative-writer    鈫?鏂囨湰璐ㄩ噺锛圖28-36 + 绂佷护 + 鏍煎紡锛?
  鈹?    AI 鐥曡抗 6 缁?+ 纭浠?3 椤?+ 瀵硅瘽涓夊姛鑳芥楠?+ 鏍煎紡鍚堣
  鈹?
  鈹斺攢鈹€ character-designer  鈫?瑙掕壊涓庡璇濓紙鎸夐渶鍚敤锛?
        閬悕娴嬭瘯 + OOC 娣卞叆 + 閰嶈宸ュ叿浜烘娴?+ 璇█椋庢牸涓€鑷存€?
```

**鎵ц娴佺▼**锛?
1. 涓讳細璇濆垎鍙戯細灏嗗鏌ヨ寖鍥?+ 璁惧畾鏂囦欢璺緞 + 绂佷护鍒楄〃鍒嗗彂鍒?4 涓瓙浠ｇ悊
2. 骞惰瀹℃煡锛? 涓瓙浠ｇ悊鍚屾椂鎵ц锛屽彧璇讳笉鍐欙紝鍚勮嚜杈撳嚭 S1-S4 鍒嗙骇鎶ュ憡
3. 姹囨€诲悎骞讹細涓讳細璇濇敹闆?4 浠芥姤鍛?鈫?鍚堝苟涓虹粺涓€瀹℃煡鎶ュ憡 鈫?澶勭悊璺?Agent 鍐茬獊
4. 鍐茬獊瑁佸喅锛氬綋涓や釜 Agent 瀵瑰悓涓€缁村害缁欏嚭涓嶅悓鍒ゅ畾鏃讹紝鍙栨洿涓ユ牸鐨勭瓑绾?
5. 闄嶇骇鍏滃簳锛氬鏋滃瓙浠ｇ悊涓嶅彲鐢ㄦ垨鍚姩澶辫触锛岃嚜鍔ㄩ檷绾т负 lean/solo

**瀛愪唬鐞嗘ā鏉?*锛歚agents/story-architect.md` / `consistency-checker.md` / `narrative-writer.md` / `character-designer.md`

**鎶ュ憡妯℃澘**锛歚templates/batch-review-report.md`锛堝惈 Full 妯″紡涓撶敤姹囨€绘牸寮?+ 璺?Agent 鍐茬獊鐭╅樀锛?

---

## 鍐欎綔绾︽潫

### 澹伴煶鍋忓ソ锛堢暘鑼勫皬璇村悜锛?

涓昏澹伴煶锛?*绮炬槑浣嗕笉鍐凤紝鏈夌儫鐏皵**銆傜畻璐︽椂鍍忕敓鎰忎汉锛岃璇濇椂鍍忚鍧娿€?

鏂囬绾㈢嚎锛?
- 鉂?绾枃瀛﹀厠鍒堕锛堝ぇ閲忕嫭鍙ョ暀鐧姐€佹儏鎰熷唴鏁涳級
- 鉂?绾畻璁″喎鎰熼锛堜笁绗旇处寮?ROI 鍒嗘瀽閾洪檲锛?
- 鉁?璋冧緝寮忚嚜鍢诧紙銆岀煭鍓戯紵鍓婅嫻鏋滐紵銆嶏級
- 鉁?鍒ゆ柇蹇€屽彛璇寲锛堛€屼粬鎯充簡涓ょ銆傞€変綋璐ㄣ€傘€嶏級
- 鉁?鍏疯薄姣斿柣鎺ュ湴姘旓紙銆岄妞庡兊寰楀儚鐢熼攬鐨勬按绠°€嶏級
- 鉁?鍥炲繂涓€绗斿甫杩囦笉钄撳欢

鑷锛氬啓瀹屼竴绔犲悗锛岀敤涓€鍙ヨ瘽鎻忚堪銆岃璧锋潵鍍忚皝鍦ㄨ鏁呬簨銆嶃€傚鏋滅瓟妗堟槸銆屽儚鏁ｆ枃瀹躲€嶆垨銆屽儚鎶曡鍒嗘瀽甯堛€嶁啋 鍥為€€銆傚鏋滅瓟妗堟槸銆屽儚浣犻偅涓贩杩囩ぞ浼氥€佽剳瀛愬ソ浣跨殑鏈嬪弸鍦ㄦ捀涓叉椂鍊欒窡浣犲敔銆嶁啋 姝ｇ‘銆?

### 澹伴煶璇皟

椤圭洰濡傛湁 `setting/writing_rules.md`锛?*蹇呴』鍦ㄥ啓绔犲墠鍔犺浇**銆傝鏂囦欢瀹氫箟涓昏鎬ф牸搴曡壊鍜屽彊浜嬭璋冪‖鎬ц姹傘€傚啓绔犲拰濮旀淳瀛愪唬鐞嗘椂鍧囬渶浼犻€掕繖浜涚害鏉熴€?

### 璁惧畾璁ㄨ鍘熷垯

璁ㄨ璁惧畾鍏冪礌鏃堕伒寰細**鍏堝畾涔変綔鐢?鈫?鍐嶈璁哄钩琛?浠ｄ环/鍞环**銆傚姛鑳藉喅瀹氫环鍊硷紝涓嶆槸鍙嶈繃鏉ャ€?

### 纭€х浠?

> **鍗曚竴浜嬪疄鏉ユ簮**锛歚references/hard-bans.md`锛圥0 闃诲 5 鏉?+ P1 寮哄埗 4 鏉?+ P2 寤鸿 1 鏉★紝鍚」鐩鑼冭鐩栨満鍒讹級

### 榛樿鍐欑珷绠＄嚎锛? 姝ワ級

1. Plan 鈥?纭鏈珷鐩爣銆佹儏缁€侀挬瀛愩€佺鍖?
2. Architect 鈥?缂栨帓涓婁笅鏂囷紝鐢熸垚绔犺妭缁撴瀯
3. Write + Reflect 鈥?鍐欐鏂囷紝鎻愬彇浜嬪疄鍙樻洿
4. Audit + Normalize 鈥?瀹℃煡纭浠ゃ€丄I 鐥曡抗銆佸瓧鏁板拰涓€鑷存€?
5. Revise 鈥?鍙慨 blocking 鍜岀敤鎴峰叧蹇冪殑闂

`--full` 灞曞紑 9 姝ュ畬鏁寸绾匡紱`--fast` 缂╁噺涓?Plan 鈫?Write 鈫?Audit 鈫?Revise銆?

### AI 鐥曡抗妫€娴嬮槇鍊?

| 鎸囨爣 | 闃堝€?|
|------|------|
| 娈佃惤绛夐暱鍙樺紓绯绘暟 | < 0.15 warning |
| 妯＄硦璇嶅瘑搴?| > 3娆?鍗冨瓧 warning |
| 杞姌璇嶉噸澶?| 鈮?3娆?warning |
| 杩炵画鐩稿悓寮€澶村彞寮?| 鈮?3鍙?info |

---

## writer.json 鏍煎紡

```json
{
  "project": "涔﹀悕",
  "author": "浣滆€?,
  "stage": "planning|writing|reviewing|completed",
  "genre": "xuanhuan|urban|xianxia|horror|other",
  "platform": "fanqie|feilu|qidian|zhihu|other",
  "chapters_total": 100,
  "chapters_done": 0,
  "words_per_chapter": 3000,
  "current_volume": 1,
  "last_action": "scan|analyze|init|plan|write|review|quality|learn",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

---

## 瀛愭ā鍧楃储寮?

> **鍔犺浇绛栫暐**锛氭牳蹇冩ā鍧楁瘡娆″啓浣滀細璇濋鍔犺浇锛涙墿灞曟ā鍧楁寜璺敱鍖归厤鎸夐渶鍔犺浇銆?

### 鏍稿績锛?2 涓?鈥?姣忔鍐欎綔蹇呯煡锛?

| 鏂囦欢 | 鍔熻兘 |
|------|------|
| `references/hard-bans.md` | 纭€х浠ゅ崟涓€浜嬪疄鏉ユ簮锛圥0-P2 鍒嗙骇锛?|
| `references/review.md` | 瀹℃煡缁村害 + Triage锛?3缁?/ 鏃ユ洿8缁?/ solo15缁达級 |
| `references/review-cycle.md` | 5 姝ュ鏌ョ绾挎潈濞佸畾涔夛紙鍚?facts.db 闄嶇骇锛?|
| `references/write.md` | 鍐欎綔绠＄嚎锛堝崟绔?鎵归噺/鐭瘒锛屽惈 sub-agent delegation 鑷锛?|
| `references/write-pitfalls.md` | 鎵归噺鍐欎綔閬垮潙鎸囧崡锛?9 椤瑰疄鎴樻暀璁級 |
| `references/quality.md` | 璐ㄦ宸ュ崟锛堢浠?鍘籄I鍛?娈佃惤淇+RAG+浜嬪疄搴擄級 |
| `references/plan.md` | 澶х翰瑙勫垝锛堟€荤翰鈫掑嵎绾测啋绔犵翰锛?|
| `references/project-init.md` | 椤圭洰鍒濆鍖栵紙鍚?import 妯″紡锛?|
| `references/pre-write-alignment.md` | 鎵归噺鍐欏墠鎬荤嚎瀵归綈妫€鏌?|
| `references/pre-write-checklist.md` | 鍐欏墠 30 绉掓鏌ユ竻鍗?|
| `references/publishable-check.md` | 绔犺妭蹇€熷彲鍙戝竷鎬т笁闂垽瀹?|
| `references/manual-polish.md` | 绾墜鍔ㄩ€愮珷閫愭娑﹁壊锛堜笁闆跺師鍒欙級 |
| `references/memory.md` | 璁板繂/鏌ヨ/瀛︿範 |

### 鎵╁睍锛堟寜闇€鍔犺浇锛?

| 鏂囦欢 | 鍔熻兘 |
|------|------|
| `references/scan.md` | 璺ㄥ钩鍙版壂姒?+ 瓒嬪娍鍒嗘瀽 |
| `references/analyze.md` | 鐖嗘鎷嗚В + 榛勯噾涓夌珷 |
| `references/optimize.md` | 鍏ㄩ噺浼樺寲锛堟剰璞￠挬瀛愭竻鐞?閽╁瓙寮哄害鎻愬崌锛?|
| `references/targeted-audit.md` | 瀹氬悜瀹℃煡 |
| `references/setting-consistency-audit.md` | 璁惧畾涓€鑷存€ц法鏂囦欢瀹¤锛堢粺涓€鍏ュ彛锛氳瀹氬唴閮ㄢ啋澶х翰鈫掓鏂団啋鍗烽棿鈫掍慨澶嶏紝鍚玈1-S4鍒嗙骇+澶氬嵎涓夊眰鏍￠獙+澶у瀷鎶ュ憡绛栫暐锛?|
| `references/setting-audit-gaming-manifest.md` | 璁惧畾涓€鑷存€у鏌ュ伐浣滄祦锛圵indows鐜涓嬪畬鏁存祦绋嬶細璇诲彇鈫抯ub-agent瀹℃煡鈫扨owerShell淇鈫掗獙璇佲啋鎶ュ憡鐢熸垚锛?|
| `references/post-review-fix.md` | 瀹℃煡鍚庝慨澶嶇绾匡紙5姝?4姝?闂妯″紡鐩綍锛屽悎骞跺師 3 鏂囦欢锛?|
| `references/deploy.md` | 澶氬嵎閮ㄧ讲娴佹按绾?+ 鍗烽棿琛旀帴妫€鏌?|
| `references/hooks-scan.md` | 浼忕瑪鍏ㄥ嵎鎵弿鏂规硶 |
| `references/master-outline-audit.md` | 鎬荤翰鏆楃嚎瀵归綈妫€鏌?|
| `references/opening-craft.md` | 閲嶇敓鏂囧紑绡囨妧宸?|
| `references/fanqie-submission.md` | 鐣寗鎶曠鏍煎紡鍏煎妫€鏌?|
| `references/fix-template-cleanup.md` | 妯℃澘澶嶅埗+涔辩爜娓呴櫎宸ヤ綔娴?|
| `references/project-knowledge-base.md` | 椤圭洰鐭ヨ瘑搴撳伐鍏烽泦鎴愭寚鍗?|
| `references/cover.md` | 灏侀潰鐢熸垚 |
| `references/track-character-state.md` | 瑙掕壊鐘舵€佽拷韪洿鏂?|
| `references/longform-quality-monitor.md` | 闀跨瘒璐ㄩ噺瓒嬪娍鐩戞帶锛堝０闊虫紓绉?鎯呯华/椋庢牸鎸囩汗锛?|
| `references/troubleshooting.md` | 甯歌鏁呴殰鎺掗櫎锛堝啓绔?瀹℃煡/濮旀淳/淇鍥涘満鏅級 |
| `references/tool-pitfalls.md` | 閫氱敤宸ュ叿闄烽槺鍙傝€?|
| `references/tool-pitfalls-windows.md` | Windows 鐗规湁宸ュ叿闄烽槺锛坵rite_file鎹㈣涓㈠け/涓枃寮曞彿鍐茬獊/绾ц仈鏁呴殰妯″紡/Get-Content缂撳瓨/涓枃璺緞read_file澶辫触锛?|
| `references/project-review-novel-gaming-manifest.md` | 銆婄綉娓稿叿鐜帮細鎴戣兘鐪嬭鍗℃睜銆嬮」鐩鏌ュ畬鎴愯褰曚笌宸ュ叿鏁欒 |

### 鑴氭湰锛?1 涓級

| 鏂囦欢 | 鍔熻兘 | 灞傜骇 |
|------|------|------|
| `scripts/audit.py` | 缁熶竴瀹¤锛堝崟绔?鐩綍/鑼冨洿锛屽惈 --fix-escaped锛?| 鏍稿績 |
| `scripts/pad_chapter.py` | 瀹夊叏瀛楁暟杩藉姞锛堟棤妯℃澘锛屽唴寤烘钀芥媶鍒嗭級 | 鏍稿績 |
| `scripts/split_paragraphs.py` | 娈佃惤鎷嗗垎锛堟寜鍙ュ彿锛屸墹60姹夊瓧锛?| 鏍稿績 |
| `scripts/analyze_hook.py` | 杩借鍔涘垎鏋愶紙閽╁瓙寮哄害/鐖界偣/閽╁姏琛板噺锛?| 鏍稿績 |
| `scripts/fact_db.py` | SQLite 浜嬪疄搴擄紙init/query/insert/status锛?| 鏍稿績 |
| `scripts/report_panorama.py` | 椤圭洰鍏ㄦ櫙鎶ュ憡锛堝仴搴疯瘎鍒?寤鸿锛?| 鏍稿績 |
| `scripts/audit_5dim.py` | 5缁翠笓椤瑰鏌?| 鎵╁睍 |
| `scripts/analyze_rhythm.py` | 鑺傚鐘舵€佹煡璇?| 鎵╁睍 |
| `scripts/report_graph.py` | 瀹炰綋鍏崇郴鍥捐氨锛圡ermaid 杈撳嚭锛?| 鎵╁睍 |
| `scripts/export.py` | 澶氬钩鍙版牸寮忓鍑?| 鎵╁睍 |
| `scripts/backup.py` | 姣忔棩鑷姩澶囦唤锛堜繚鐣?澶╋級 | 鎵╁睍 |

### Agent 妯℃澘锛? 涓?鈥?full 瀹℃煡妯″紡璋冪敤锛?

| 鏂囦欢 | 鍔熻兘 |
|------|------|
| `agents/story-architect.md` | 鏁呬簨缁撴瀯瀹℃煡锛堢淮搴?1-15 + 鎵ц鍗★級 |
| `agents/consistency-checker.md` | 浜嬪疄涓€鑷存€у鏌ワ紙缁村害 16-27 + 鎵ц鍗★級 |
| `agents/narrative-writer.md` | 鏂囨湰璐ㄩ噺瀹℃煡锛圓I鐥曡抗+绂佷护+鏍煎紡锛?|
| `agents/character-designer.md` | 瑙掕壊涓庡璇濆鏌ワ紙鎵ц鍗★級 |

---

### 濮旀淳鍚庢牎楠岋紙鎵归噺鍐欑珷鍚庡繀鍋氾級

濮旀淳瀛愪唬鐞嗘壒閲忓啓绔犺繑鍥炲悗锛屼富浼氳瘽蹇呴』鎵ц锛?

1. **鏂囦欢钀界洏楠岃瘉**锛歚Get-ChildItem chapters/ch_*.md | Measure-Object` 纭鏁伴噺
2. **姹℃煋鎵弿**锛氥€屼笉鈫掓槸銆嶆槸鏈€楂橀姹℃煋妯″紡锛岃瑙?`references/corruption-fix-bu-shi.md`
3. **绂佷护瀹¤**锛氳繍琛?`scripts/audit.py` 鎴栫瓑浠风殑 Python 瀹¤鑴氭湰
4. **瀛楁暟鏍￠獙**锛氭瘡绔?鈮?500 姹夊瓧
5. **淇鍚庡鎵?*锛氫慨澶嶅悗閲嶆柊杩愯姹℃煋鎵弿纭娓呴浂

### 閫愮珷瀹℃煡璺敱锛堟墜鍔ㄥ叏涔﹁川妫€锛?

瑙﹀彂璇嶏細銆岄€愮珷妫€鏌ャ€嶃€屾鏌ヤ竴绔犳姤鍛婁竴绔犮€嶃€屼笉鐢ㄥ瓙浠ｇ悊涓€绔犱竴绔犺繃銆嶃€屼笉鐢ㄨ剼鏈€?

鎵ц鏂瑰紡锛氫富浼氳瘽閫愮珷閫氳锛?*涓嶄娇鐢ㄥ瓙浠ｇ悊锛屼笉浣跨敤浠讳綍鑷姩鍖栬剼鏈?*銆傜敤鎴疯銆屼笉鐢ㄨ剼鏈€嶆剰鍛崇潃锛?
- 鉂?绂佹鎵归噺 Python 瀹¤鑴氭湰鎵弿
- 鉂?绂佹鐢ㄦ鍒欐彁鍙栧悗鍙姤鏁?
- 鉂?绂佹銆屽姞閫熴€嶃€屽揩閫熻繃銆嶃€屾壒閲忔壂鎻忋€?
- 鉁?姣忕珷 `Get-Content` 瀹屾暣璇诲彇锛屼汉鐪奸€氳
- 鉁?璇诲畬涓€绔犳姤涓€绔狅紝鏍煎紡鍥哄畾锛氳璋冭瘎浠?+ 闂鍒楄〃 + 淇鎿嶄綔

姣忕珷璇诲畬鍚庢姤鍛婏細
- 璇皟涓€鑷存€э紙鏄惁鍖归厤 `setting/writing_rules.md` 瀹氫箟鐨勫０闊筹級
- 姹℃煋娈嬬暀锛堟墜鍔ㄦ壂鎻忋€屼笉鈫掓槸銆嶃€屾槸鏄€嶆ā寮忥紝閫愬彞鏍稿璇箟锛?
- 閫昏緫瑁傜紳锛堟壙涓婃柇瑁傘€佽涔夐鍊掋€佹儏鑺傜煕鐩撅級
- 淇鍚庡洖鍐?

鑺傚锛氶粯璁や粠澶村紑濮嬶紝鐢ㄦ埛鎸囧畾璧峰绔犲垯浠庤绔犲紑濮嬨€傚鏌ュ畬鎴愬悗鏇存柊杩借釜鏂囦欢銆?*绂佹浠ヤ换浣曠悊鐢辫烦杩囩珷鑺傛垨鍔犻€熻妭濂忋€?* 鐢ㄦ埛鏄庣‘璇淬€屼綘涓哄暐瑕佸姞閫燂紝浣犳湁鍟ョ潃鎬ョ殑娲汇€嶅氨鏄璺宠繃琛屼负鐨勭籂姝ｃ€?

### 绔犺妭姹℃煋妯″紡閫熸煡

瀛愪唬鐞嗘壒閲忓啓绔犲悗鏈€甯歌鐨勪笁绉嶆薄鏌擄紙閫愮珷瀹℃煡鏃堕噸鐐规壂鎻忥級锛?

**鈶?銆屼笉鈫掓槸銆嶆薄鏌?*锛氭湰绔犲簲鏈夊惁瀹氳瘝銆屼笉銆嶈鏇挎崲涓恒€屾槸銆嶃€?
- 绀轰緥锛氥€屾槸鐤笺€嶅簲涓恒€屼笉鐤笺€嶏紱銆屾槸鐭ラ亾銆嶅簲涓恒€屼笉鐭ラ亾銆嶏紱銆屾憚鍍忓ご鏄甯哥殑銆嶈鍐欎负銆屾憚鍍忓ご涓嶆甯哥殑銆?
- 淇锛氶€愪笂涓嬫枃鏇挎崲涓烘纭殑鍚﹀畾褰㈠紡
- 閲嶇伨鍖猴細ch2-10锛堟棭鏈熷鎵樻壒娆★級銆佹墍鏈夊鎵樿繑鍥炵殑绔犺妭

**鈶?銆屾槸鏄€嶆畫鐣?*锛氥€屾槸涓嶆槸銆嶇枒闂彞琚浼や负銆屾槸鏄€嶃€?
- 绀轰緥锛氥€岃€佸懆鏄笉鏄湁涓狤xcel琛ㄦ牸銆嶁啋 琚薄鏌撲负銆岃€佸懆鏄槸鏈変釜Excel琛ㄦ牸銆?
- 淇锛氱枒闂澧冧腑鐨勩€屾槸鏄€嶁啋銆屾槸涓嶆槸銆?
- 娉ㄦ剰锛氶渶鍖哄垎鐪熷疄銆屾槸鏄€嶆薄鏌撳拰鍙ュ彿鏂紑鐨勭嫭绔嬨€屾槸銆嶅瓧

**鈶?鎵归噺鏇挎崲鑴氭湰浜屾姹℃煋**锛氫慨澶嶈剼鏈娇鐢ㄥ叏灞€ `text.replace('涓嶆槸', '鏄?)` 鎴栫被浼奸€昏緫锛屽鑷淬€屼笉鏄€曘€嶁啋銆屾槸鎬曘€嶁啋鏈€缁堣閿欒鍦拌浆涓恒€屼笉涓嶆€曘€嶃€?
- 绀轰緥锛氥€屼笉鏄€曘€嶁啋 淇鑴氭湰璇浆涓恒€屾槸鎬曘€嶁啋 浜屾淇璇浆涓恒€屼笉涓嶆€曘€?
- 淇锛氬厛瀹氫綅鍘熷璇箟锛屽啀閫愬鎵嬪伐鏇挎崲
- 鏁欒锛?*姘歌繙涓嶈瀵瑰惈銆屼笉銆嶅瓧鐨勬枃鏈娇鐢ㄥ叏灞€鏇挎崲鑴氭湰**锛屽繀椤婚€愪笂涓嬫枃鍒ゆ柇

### 寮€绡囪妭濂忛噸鏋?

瑙﹀彂璇嶏細銆岃妭濂忓お鎱€嶃€屽紑绡囦笉澶熷揩銆嶃€屽笇鏈涙妸X绔犲唴瀹瑰帇缂╁埌Y绔犮€?

绛栫暐锛氫互鏍稿績閽╁瓙绔犺妭涓烘柊 ch1锛屽墠鎯呴€氳繃鍥炲繂/鑱旀兂绌挎彃銆傛祦绋嬶細
1. 纭畾鏂?ch1 鐨勯敋鐐逛簨浠讹紙濡傞娆″叿鐜板脊绐楋級
2. 灏嗚鍘嬬缉鐨勫墠鎯呮媶鍒嗕负纰庣墖鍖栧洖蹇?
3. 鍦ㄦ瘡涓喅绛?鎯呯华鑺傜偣鑷劧宓屽叆鍥炲繂
4. 閲嶅啓鏂?ch1-2锛屾棫绔犳暣浣撳悗绉荤紪鍙?
5. 鍚屾淇鎵€鏈夊ぇ绾层€佸嵎绾层€佹€荤翰涓殑绔犺妭缂栧彿

> 璇﹁ `references/corruption-fix-bu-shi.md`锛堟薄鏌撲慨澶嶅弬鑰冿級

---\n\n## 鍙樻洿璁板綍\n\n| 鏃ユ湡 | 鍏抽敭鍙樻洿 |\n|------|---------|\n| 2026-06-29 | **v7.5 本地改动合并**：新增 references/setting-audit-gaming-manifest.md（设定一致性审查标准流程）；tool-pitfalls-windows.md 陷阱五/六完善（含中文路径 read_file 失败 + write_file 大型报告级联故障）；SKILL.md 子模块索引同步更新；merged with remote v7.4（v7.5 = v7.4 + local changes） |
| 2026-06-29 | **v7.4 閫愮珷瀹℃煡鍔犲浐**锛歋KILL.md 閫愮珷瀹℃煡璺敱澶у箙鎵╁睍锛堟槑纭姝㈣剼鏈?鍔犻€?璺宠繃锛涙柊澧炪€屼笉鐢ㄨ剼鏈€嶈Е鍙戣瘝鍜屼簲鏉＄‖鎬х浠わ級锛汼KILL.md 鏂板銆岀珷鑺傛薄鏌撴ā寮忛€熸煡銆嶈妭锛堚憼鈶♀憿涓夌姹℃煋妯″紡+淇鏂规硶锛夛紱corruption-fix-bu-shi.md 鏂板銆屾壒閲忎慨澶嶈剼鏈簩娆℃薄鏌撱€嶈妭锛堛€屼笉涓嶆€曘€嶆ā寮?绂佹鍏ㄥ眬鏇挎崲閾佸緥锛墊\n| 2026-06-28 | **v7.3 瀹℃煡+閲嶆瀯+姹℃煋**锛氭柊澧?`references/corruption-fix-bu-shi.md`锛堛€屼笉鈫掓槸銆嶆薄鏌撲慨澶嶆潈濞佸弬鑰冿級锛涘娲惧悗鏍￠獙鑺傞噸鏋勶紙澶栭摼鍙傝€冩枃浠?+ 閫愮珷瀹℃煡璺敱 + 寮€绡囪妭濂忛噸鏋勬寚寮曪級锛泈rite-pitfalls.md 鏂板閬垮潙 14-18锛圵indows璺緞/鏂囬鍋忓ソ/寮€绡囬噸鏋?澹伴煶瀹氳皟/鎵归噺鏇挎崲姹℃煋锛夛紱SKILL.md 澹伴煶鍋忓ソ鑺傛墿灞曪紙鐣寗灏忚鍚戯級 |
| 2026-06-28 | **v7.2 濮旀淳鍚庢薄鏌撴牎楠?*锛氭柊澧炪€屽娲惧悗鏍￠獙銆嶈妭锛涚姸鎬佹劅鐭ユ柊澧?`writing_rules.md` 鑷姩鍔犺浇 || 2026-06-26 | **v7.0 閫氱敤鍖?*锛氱Щ闄ゆ墍鏈?Claude/Hermes 涓撶敤鏈锛坉elegate_task鈫抯ub-agent delegation, web_search鈫抴eb/content search, image_generate鈫抜mage generation tool, search_files鈫抔rep/pattern search, Moke/Hermes 绉婚櫎锛夛紱agent YAML 娉涘寲锛坱ools鈫抍apabilities, model鈫抋dvisory_model, maxTurns鈫抦ax_iterations锛夛紱hermes-tool-pitfalls.md鈫抰ool-pitfalls.md锛堥€氱敤宸ュ叿闄烽槺锛夛紱codebase-memory-mcp.md鈫抪roject-knowledge-base.md锛堥€氱敤鐭ヨ瘑搴撴寚鍗楋級锛汼KILL.md 鎵ц绛栫暐涓庡瓙妯″潡绱㈠紩鍚屾鏇存柊 |
| 2026-06-23 | **v4.0 婵€杩涚槮韬?*锛氱Щ闄ゆ墍鏈夊悜鍚庡吋瀹癸紱SKILL.md -62%锛?30鈫?00琛岋級 |
| 2026-06-23 | **v4.1 婊″垎鍐插埡**锛歳eview.md 鏂板 daily 鏃ユ洿 8 缁存ā寮忥紙3鍒嗛挓鍙戝竷闂革級锛涘瓙妯″潡绱㈠紩鍒嗗眰锛堟牳蹇?2 + 鎵╁睍21 + 鑴氭湰鏍稿績6/鎵╁睍5锛夛紱鎵ц绛栫暐鏂板 daily 瀹℃煡 |
| 2026-06-23 | **v4.2 鎵ц灞傚姞鍥?*锛歛udit.py 閲嶅啓锛圔ANS 鍚屾 hard-bans.md + 鏂板鍏冨彊浜?寮曞彿/妯℃澘澶嶅埗妫€娴嬶級锛沺roject-init.md 绉婚櫎鍏ㄩ儴鏃у紩鐢紱write-pitfalls.md 鎶界锛沠act_db.py/analyze_hook.py 鏂囨。淇 |
| 2026-06-23 | **v4.3 娣卞害鍑€鍖?*锛歱ad_chapter.py 绉婚櫎杩濈璇嶏紙瀵硅瘽姹犲惈銆屾繁鍚镐竴鍙ｆ皵銆嶁啋 S1 淇锛夛紱4 涓?agent 妯℃澘澧炲姞 TL;DR锛涙竻闄?6 涓?reference 涓殑鏃х郴缁熷悕娈嬩綑锛泀uality-delegate.md 涓?batch-post-delegate-fix.md 鏄庣‘鍒嗗伐锛沘udit_5dim.py 澧炲姞椤圭洰閫傞厤璇存槑 |
| 2026-06-23 | **v4.4 鏀跺熬**锛歸rite.md 閬垮潙鎸囧崡褰诲簳鎶界鑷?write-pitfalls.md锛坰ed 鍒囬櫎 ~150 琛岋級锛況eport_panorama.py 绉婚櫎 project-state.json 鍥為€€锛況eview-cycle.md 鏃т腑鏂囪矾寰勨啋鏂拌嫳鏂囪矾寰勶紱SKILL.md 椤堕儴澧炲姞銆屼笁鍦烘櫙蹇€熶笂鎵嬨€嶅崱鐗囷紱浜ゅ弶寮曠敤瀹屾暣鎬у璁?|
| 2026-06-23 | **v4.5 鏂囦欢鍚堝苟**锛歜atch-post-delegate-fix + batch-fix-s2s3 + quality-delegate 涓夊悎涓€ 鈫?post-review-fix.md锛堜慨澶嶅喅绛栨爲 + 5姝ョ绾?+ 4姝ョ簿鍑嗕慨澶?+ 闂妯″紡鐩綍锛夛紱quality.md 鍒犻櫎涓?hard-bans 閲嶅鐨勭浠よ〃锛泃argeted-audit.md 鏃ц矾寰勨啋鏂拌矾寰勶紱references 34鈫?1 |
| 2026-06-23 | **v4.6 README 鍚屾**锛歊EADME 瀹屽叏閲嶅啓锛?1 references + 瀹℃煡妯″紡姊害琛?+ 涓夊満鏅揩閫熶笂鎵?+ 鏂囦欢娓呭崟涓?SKILL.md 涓€鑷达級锛涚Щ闄ゆ棫鏁版嵁娴佹灦鏋勫浘锛涜剼鏈ず渚嬭矾寰勭粺涓€ |
| 2026-06-23 | **v4.7 妯℃澘+榛樿鍊?*锛歜atch-review-report.md 绂佷护琛ㄥ悓姝?hard-bans.md (P0/P1 鍒嗙骇)锛況eport_graph.py 澧炲姞椤圭洰閫傞厤璇存槑锛沺roject-init.md 澧炲姞鏅鸿兘榛樿锛堝钩鍙扳啋鐣寗/瀛楁暟鈫?000/绔犺妭鈫?0-300锛? 鍗曡疆鏀堕泦浼樺厛 |
| 2026-06-23 | **v5.0 CLI**锛氬垱寤?`scripts/writer` 缁熶竴鍏ュ彛锛?2 瀛愬懡浠?+ fix 涓€閿慨澶?+ check 涓€閿鏌ワ級 |
| 2026-06-23 | **v5.1 鏉冮噸**锛歳eview.md 15 缁村姞鏉冭瘎鍒嗭紙鏍稿績涓夎: 璁惧畾鍐茬獊30 + OOC25 + 閽╁瓙25 = 40%锛夛紱鍋ュ悍搴﹁绠楀叕寮?|
| 2026-06-23 | **v5.2 绠＄嚎鍚堝苟**锛歸rite.md 9 姝ュ畬鏁寸绾夸粠 ~155 琛屽帇缂╀负 15 琛岃〃鏍硷紙5 姝?+ 4 鎵╁睍锛夛紱鍒犻櫎閲嶅鎻忚堪 |
| 2026-06-23 | **v5.3 閮ㄧ讲鍒嗗伐**锛歞eploy.md 娣诲姞鎸囧悜 plan.md 鐨勮妭鎷嶈〃寮曠敤锛屾槑纭垎宸ワ紙plan=璁捐锛宒eploy=鎵ц锛?|
| 2026-06-23 | **v5.4 Agent 妯℃澘**锛歸rite.md delegate context 妯℃澘锛? 涓俊鎭潡锛氫换鍔?绂佷护/鐘舵€?绔犵翰/澹伴煶/鑷锛?|
| 2026-06-23 | **v5.5-v5.9 瀹屽杽**锛歵roubleshooting.md 鏁呴殰鎺掗櫎鎸囧崡锛堝啓绔?瀹℃煡/濮旀淳/淇鍥涘満鏅級锛沺roject-init 寮曠敤 writing_rules 妯℃澘 |
| 2026-06-23 | **v6.0 鍙戝竷**锛氱増鏈彿锛?2 杞凯浠ｇ粓鎬佲€斺€?10 琛?SKILL.md 路 32 references 路 12 scripts(鍚?CLI) 路 4 agents 路 11 涓ā鏉?路 闆舵棫寮曠敤 路 鎵ц灞備笌瑙勫垯灞傚畬鍏ㄥ悓姝?|
