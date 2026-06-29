# Windows 鐜宸ュ叿闄烽槺

鍦?Windows 鐜涓嬩娇鐢?Hermes Agent 杩涜缃戞枃鍐欎綔鏃剁殑鐗规湁宸ュ叿闄烽槺銆?

---

## 闄烽槺涓€锛歸rite_file 鍐欏叆 Markdown 涓㈠け鎹㈣绗︼紙楂樼牬鍧忔€э級

**瑙﹀彂鏉′欢**锛氬湪 Windows 鐜涓嬩娇鐢?`write_file` 宸ュ叿鍐欏叆 `.md` 鏂囦欢鏃躲€?

**鍘熷洜**锛歚write_file` 鍦?Windows 涓婄殑瀹炵幇浼氬皢鍐呭浣滀负鍗曡鍐欏叆锛屼涪寮冩墍鏈?`\r\n` 鎴?`\n` 鎹㈣绗︺€傚啓鍏ョ殑鏂囦欢铏界劧瀛楄妭鏁版纭紝浣嗘墍鏈夋崲琛屾秷澶憋紝鍙樻垚涓€鏁磋鏂囨湰銆?

**琛ㄧ幇**锛?
- 鏂囦欢 `Get-Content` 鏄剧ず涓轰竴鏁磋锛堟棤鍥炶溅锛?
- `Select-String` 鎼滅储妯″紡鍙兘鍖归厤涓嶅埌锛堝洜涓烘暣涓枃浠舵槸涓€琛岋級
- Markdown 鏍囬 `##`銆佸垪琛?`- `銆佽〃鏍?`|` 鍏ㄩ儴杩炲湪涓€璧?
- 鏂囦欢澶у皬姝ｅ父浣嗗彲璇绘€т负闆?

**姝ｇ‘鍋氭硶**锛?
1. **鍐?Markdown 鏂囦欢鏃朵紭鍏堢敤 terminal + PowerShell**锛岃€岄潪 `write_file`
2. 濡傛灉宸茬敤 `write_file` 鍐欏叆涓旀枃浠舵崯鍧忥紝鐢?PowerShell 閲嶆柊鏍煎紡鍖?
3. **楠岃瘉鍐欏叆**锛氬啓鍏ュ悗鐢?`Select-String` 鎴?`Get-Content | Select-Object -First 3` 纭鎹㈣姝ｅ父

**棰勯槻鎺柦**锛?
- 鍦?Windows 涓婂啓 `.md` 鏂囦欢鏃讹紝浼樺厛浣跨敤 `terminal` 鎵ц `python3 -c "..."` 澶氳鍐欏叆
- 鎴栫敤 `Set-Content -Path "file.md" -Value @("line1","line2") -Encoding UTF8`
- `write_file` 鏇撮€傚悎鍐欏叆 `.py`銆乣.json`銆乣.yaml` 绛夌粨鏋勫寲鏂囦欢

---

## 闄烽槺浜岋細PowerShell 涓枃寮曞彿涓?Invoke-Expression 鍐茬獊

**瑙﹀彂鏉′欢**锛氬湪 PowerShell 鍛戒护涓娇鐢ㄥ惈涓枃鍙屽紩鍙?`""` 鐨勫瓧绗︿覆鎷兼帴銆?

**鍘熷洜**锛歅owerShell 鐨?`Invoke-Expression` 鎴栧瓧绗︿覆鎻掑€间細灏?`"` 瑙ｆ瀽涓虹壒娈婂瓧绗︺€?

**琛ㄧ幇**锛歚鎵€鍦ㄤ綅缃?琛?1 瀛楃: XXX\r\n+ ...` 鎶ラ敊锛屾彁绀?琛ㄨ揪寮忔垨璇彞涓寘鍚剰澶栫殑鏍囪"銆?

**姝ｇ‘鍋氭硶**锛?
- 浣跨敤 Python 鑴氭湰澶勭悊鍚腑鏂囧紩鍙风殑鏂囦欢鎿嶄綔
- 鎴栫敤 PowerShell 鏃堕伩鍏嶅湪瀛楃涓蹭腑宓屽叆涓枃寮曞彿锛屾敼鐢ㄥ彉閲忎紶閫?

---

## 闄烽槺涓夛細Set-Content -NoNewline 涓㈠け鎵€鏈夋崲琛?

**瑙﹀彂鏉′欢**锛氫娇鐢?`Set-Content -NoNewline` 鍐欏叆鏂囦欢鏃躲€?

**鍘熷洜**锛歚-NoNewline` 鍙傛暟浼氶樆姝?PowerShell 鍦ㄦ湯灏炬坊鍔犳崲琛岀锛屼絾濡傛灉鍐呭鏈韩鍚?`\r\n`锛岃涓哄彇鍐充簬浼犲叆鐨勫瓧绗︿覆绫诲瀷銆?

**姝ｇ‘鍋氭硶**锛?
- 鍐欏琛屾枃浠舵椂涓嶇敤 `-NoNewline`
- 濡傞渶绮剧‘鎺у埗鎹㈣锛岀敤 `[System.IO.File]::WriteAllText()` 閰嶅悎 `\r\n`

---

## 闄烽槺鍥涳細read_file 宸ュ叿鍦?Windows 涓婄殑鍙潬鎬?

**瑙﹀彂鏉′欢**锛氫娇鐢?`read_file` 宸ュ叿璇诲彇鏂囦欢鏃躲€?

**琛ㄧ幇**锛氭湁鏃惰繑鍥炵┖缁撴灉鎴栨埅鏂唴瀹癸紝灏ゅ叾褰撴枃浠惰矾寰勫惈涓枃鏃躲€?

**姝ｇ‘鍋氭硶**锛?
- 鍚腑鏂囪矾寰勭殑鏂囦欢浼樺厛鐢?`terminal` + `Get-Content -Encoding UTF8` 璇诲彇
- 楠岃瘉璇诲彇缁撴灉锛歚Get-Content file.md | Measure-Object -Line`

---

## 闄烽槺浜旓細write_file / read_file 瀵逛腑鏂囪矾寰勫畬鍏ㄩ潤榛樺け璐ワ紙楂樼牬鍧忔€э級

**瑙﹀彂鏉′欢**锛氫娇鐢?`write_file` 鎴?`read_file` 宸ュ叿鎿嶄綔璺緞鍚腑鏂囩殑 `.md` 鏂囦欢鏃躲€?

**琛ㄧ幇**锛?
- `write_file` 鎶ュ憡 `bytes_written: N`銆乣resolved_path: ...` 鎴愬姛锛屼絾鏂囦欢鍦ㄧ鐩樹笂涓嶅瓨鍦?
- `read_file` 杩斿洖 `sed` 鎴?PowerShell 閿欒锛屾垨琚紦瀛樺唴瀹硅鐩栵紝涓嶅弽鏄犲疄闄呮枃浠?
- 姝ら棶棰?**涓嶆槸鎹㈣涓㈠け**锛屾槸**鏁翠釜鏂囦欢鏍规湰娌℃湁鍐欏叆/璇讳笉鍒?*

**鏍规湰鍘熷洜**锛氬伐鍏峰唴閮ㄨ矾寰勫鐞嗗涓枃/澶氬瓧鑺傝矾寰勫瓨鍦ㄧ紪鐮佹垨杞箟闂锛岃矾寰勪腑鐨勪腑鏂囧瓧绗﹁杞爜鍚庢寚鍚戜笉瀛樺湪鐨勮矾寰勶紙濡?`D:\\Writer\\xxxx` 瀹為檯鍐欏叆鍒颁簡鏌愪釜铏氭嫙/閲嶅畾鍚戜綅缃級銆?

**姝ｇ‘鍋氭硶锛堝凡楠岃瘉鍙潬锛?*锛?
1. **鍐欐枃浠?*锛氱敤 PowerShell `[System.IO.File]::WriteAllText()` 
2. **璇绘枃浠?*锛氱敤 PowerShell `Get-Content -Encoding UTF8`
3. **鍐?Python 鑴氭湰**锛氬厛鐢?PowerShell `Out-File -Encoding UTF8` 鍐欏埌涓嶅惈涓枃鐨勮矾寰勶紙濡?`C:\Temp\`锛夛紝鍐?`python C:\Temp\script.py`
4. **鎵归噺瀹¤**锛歅ython 鑴氭湰鏀惧埌 `C:\Temp\`锛岀敤缁濆璺緞寮曠敤椤圭洰鏂囦欢

**绂佹鍋氭硶**锛?
- 鉂?`write_file` 鍐欏叆鍚腑鏂囪矾寰勭殑浠讳綍鏂囦欢
- 鉂?`read_file` 璇诲彇鍚腑鏂囪矾寰勭殑浠讳綍鏂囦欢
- 鉂?`search_files` 鎼滅储鍚腑鏂囪矾寰勭殑鐩綍锛堝悓鏍烽潤榛樺け璐ワ級
- 鉂?渚濊禆 `write_file` 鐨勮繑鍥炵粨鏋滃垽鏂枃浠舵槸鍚﹀啓鍏ユ垚鍔?鈥斺€?蹇呴』鐢?`Get-Item` 鎴?`Get-ChildItem` 楠岃瘉

**楠岃瘉鍐欏叆**锛?
```powershell
Get-Item "D:\Writer\椤圭洰鍚峔chapters\ch_001.md" | Select-Object FullName, Length
```

---

## 闄烽槺鍏細read_file 宸ュ叿鍦?Windows 涓婅皟鐢?sed 闈欓粯澶辫触

**瑙﹀彂鏉′欢**锛氫娇鐢?`read_file` 宸ュ叿璇诲彇鏂囦欢鏃躲€?

**琛ㄧ幇**锛氳繑鍥炲唴瀹逛负涓€琛?sed 閿欒锛?
```
sed : 鏃犳硶灏?sed"椤硅瘑鍒负 cmdlet銆佸嚱鏁般€佽剼鏈枃浠舵垨鍙繍琛岀▼搴忕殑鍚嶇О銆?
```

**鍘熷洜**锛歚read_file` 鍦?Windows 涓婂唴閮ㄨ皟鐢?`sed -n '1,500p' <file>` 鏉ヨ鍙栨枃浠讹紝浣?Windows PowerShell 娌℃湁 `sed` 鍛戒护銆?

**姝ｇ‘鍋氭硶**锛?
- 浠讳綍鍚腑鏂囪矾寰勬垨闇€瑕佸彲闈犺鍙栫殑鏂囦欢锛岀敤 `terminal` + `Get-Content -Encoding UTF8` 鏇夸唬 `read_file`
- 绀轰緥锛歚Get-Content "D:\Writer\椤圭洰\chapters\ch_001.md" -Encoding UTF8`

---

## 闄烽槺涓冿細search_files 宸ュ叿鍦ㄤ腑鏂囪矾寰勪笂闈欓粯澶辫触

**瑙﹀彂鏉′欢**锛氫娇鐢?`search_files` 鍦ㄥ惈涓枃瀛楃鐨勮矾寰勪笅鎼滅储鏂囦欢鎴栧唴瀹广€?

**琛ㄧ幇**锛氳繑鍥炵┖缁撴灉鎴?`Path not found` 閿欒锛屽嵆浣胯矾寰勭‘瀹炲瓨鍦ㄣ€?

**鍘熷洜**锛歚search_files` 搴曞眰浣跨敤 ripgrep锛岃矾寰勪腑鐨勪腑鏂囧瓧绗﹁杞爜鍚庢棤娉曟纭В鏋愩€?

**姝ｇ‘鍋氭硶**锛?
- 鐢?`terminal` + `Get-ChildItem` 鏇夸唬鏂囦欢鎼滅储
- 鐢?`terminal` + `Select-String` 鏇夸唬鍐呭鎼滅储
- 閬垮厤灏嗗惈涓枃鐨勮矾寰勪紶缁?`search_files`