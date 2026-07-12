// ==UserScript==
// @name         番茄作家网 · 章节同步助手
// @namespace    fanqie-novel-sync
// @version      2.3.1
// @description  从本地JSON批量上传章节到番茄作家网，支持断点续传、进度保存、可视化操作
// @author       Sandhill（基于 Pluto 原作修改）
// @match        https://fanqienovel.com/main/writer/chapter-manage/*
// @match        https://fanqienovel.com/main/writer/*/publish*
// @match        https://fanqienovel.com/main/writer/*
// @include      https://fanqienovel.com/main/writer/*
// @icon         https://lf-lv-buz.qingting.fm/bucket/fanqienovel-common-icon/favicon.ico
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addStyle
// @grant        GM_xmlhttpRequest
// @grant        GM_registerMenuCommand
// @connect      127.0.0.1
// @run-at       document-end
// @updateURL    none
// @downloadURL  none
// ==/UserScript==

(function () {
    'use strict';

    // 最早期心跳日志：如果控制台看不到这行，说明脚本根本没被注入
    console.log(
        '%c[番茄同步助手] v2.3.1 已注入 · ' + location.href,
        'color:#e74c3c;font-weight:bold',
    );

    // ============================================================
    // 常量
    // ============================================================
    // v2.2.0 起，章节 / 进度 / 待恢复任务按 bookId 分片存储，避免多本书串数据。
    // 存储 key 形如：fanqie_sync_chapters:7661549640684162073
    // 未在书籍页时（无 bookId），使用 '_global_' 兜底（历史行为）。
    const STORAGE_KEY_PREFIX = 'fanqie_sync_chapters';
    const PROGRESS_KEY_PREFIX = 'fanqie_sync_progress';
    const PENDING_KEY_PREFIX = 'fanqie_sync_pending';
    const SETTINGS_KEY = 'fanqie_sync_settings'; // 全局
    const LOG_KEY = 'fanqie_sync_logs'; // 全局
    const LAST_BOOK_KEY = 'fanqie_sync_last_book'; // 上次同步时用的 bookId（用于跨页导航记忆）
    const LEGACY_STORAGE_KEY = 'fanqie_sync_chapters';
    const LEGACY_PROGRESS_KEY = 'fanqie_sync_progress';
    const LEGACY_PENDING_KEY = 'fanqie_sync_pending';
    const DELAY = 3500;
    const MAX_LOGS = 500;

    // 当前活动 bookId：优先当前页 URL，其次上次记忆的（用于跨页导航中转 pending）
    function currentBookId() {
        return getBookId() || GM_getValue(LAST_BOOK_KEY, '') || '_global_';
    }

    function keyFor(prefix, bookId) {
        return prefix + ':' + (bookId || currentBookId());
    }

    // 兼容旧数据：首次访问该书时，如果分片 key 无数据但全局 legacy key 有数据，一次性迁移
    let __migrated = new Set();
    function migrateLegacyIfNeeded(bookId) {
        if (!bookId || bookId === '_global_' || __migrated.has(bookId)) return;
        __migrated.add(bookId);
        const chKey = keyFor(STORAGE_KEY_PREFIX, bookId);
        const prKey = keyFor(PROGRESS_KEY_PREFIX, bookId);
        const legacyCh = GM_getValue(LEGACY_STORAGE_KEY, null);
        const legacyPr = GM_getValue(LEGACY_PROGRESS_KEY, null);
        // 只在该 book 没有专属数据时才继承 legacy
        if (legacyCh && !GM_getValue(chKey, null)) {
            GM_setValue(chKey, legacyCh);
        }
        if (legacyPr && !GM_getValue(prKey, null)) {
            GM_setValue(prKey, legacyPr);
        }
    }

    // ============================================================
    // 工具函数
    // ============================================================
    function sleep(ms) {
        return new Promise((r) => setTimeout(r, ms));
    }

    function getBookId() {
        let m = location.pathname.match(/\/writer\/(\d+)/);
        if (m) return m[1];
        m = location.pathname.match(/\/chapter-manage\/(\d+)/);
        return m ? m[1] : null;
    }

    function extractTitle(fullTitle) {
        const m = fullTitle.match(
            /^第[零一二三四五六七八九十百千\d]+章\s*(.+)/,
        );
        return m ? m[1] : fullTitle;
    }

    function extractBody(content) {
        const lines = content.split('\n').filter((l) => l.trim().length > 0);
        if (lines[0] && lines[0].includes('第') && lines[0].includes('章')) {
            return lines.slice(1).join('\n');
        }
        return lines.join('\n');
    }

    function contentToHtml(content) {
        return content
            .split('\n')
            .filter((l) => l.trim().length > 0)
            .map(
                (l) =>
                    `<p>${l.trim().replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>`,
            )
            .join('');
    }

    function now() {
        return new Date().toLocaleTimeString('zh-CN', { hour12: false });
    }

    // React 受控输入兼容写法（触发完整原生事件链，强制 React commit）
    function setNativeValue(el, value) {
        const proto = Object.getPrototypeOf(el);
        const setter =
            Object.getOwnPropertyDescriptor(proto, 'value')?.set ||
            Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
                ?.set;
        if (setter) setter.call(el, value);

        // 关键：React 的 nativeInputValueTracker 会记录上一次 value，
        // 如果新旧 value 相同就不触发 onChange。清掉它的缓存值确保 change 生效。
        if (el._valueTracker) {
            try {
                el._valueTracker.setValue('');
            } catch (e) {
                /* 兼容不同 React 版本 */
            }
        }

        // 用 InputEvent 而不是普通 Event —— React 17+ 用 inputType 区分真实输入
        try {
            el.dispatchEvent(
                new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: value,
                }),
            );
        } catch (e) {
            // 老浏览器兜底
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
        // 键盘链模拟：某些校验绑在 keyup 上
        el.dispatchEvent(
            new KeyboardEvent('keyup', { bubbles: true, key: 'End' }),
        );
    }

    // 强制 blur，让 React 把 pending 值 commit 到状态并触发 onBlur 校验
    function commitInput(el) {
        el.dispatchEvent(new Event('blur', { bubbles: true }));
        el.dispatchEvent(new FocusEvent('focusout', { bubbles: true }));
    }

    // 逐字符打字（终极兜底：模拟真实键盘输入，用于 React fiber 严格校验的输入框）
    async function typeCharByChar(el, text) {
        el.focus();
        // 先清空
        const setter =
            Object.getOwnPropertyDescriptor(
                Object.getPrototypeOf(el),
                'value',
            )?.set ||
            Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
                ?.set;
        if (setter) setter.call(el, '');
        if (el._valueTracker)
            try {
                el._valueTracker.setValue('x');
            } catch (e) {}
        el.dispatchEvent(
            new InputEvent('input', {
                bubbles: true,
                inputType: 'deleteContentBackward',
            }),
        );
        await sleep(50);

        // 逐字符
        let cur = '';
        for (const ch of text) {
            cur += ch;
            if (setter) setter.call(el, cur);
            if (el._valueTracker)
                try {
                    el._valueTracker.setValue(cur.slice(0, -1));
                } catch (e) {}
            el.dispatchEvent(
                new InputEvent('input', {
                    bubbles: true,
                    inputType: 'insertText',
                    data: ch,
                }),
            );
            await sleep(20);
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // 智能查找章节序号 / 标题输入框：多策略回退，抗类名变更
    function findChapterInputs() {
        // 策略 1：原始类名选择器（如果没变过就用它）
        let serial = document.querySelector(
            'input.serial-input:not(.serial-editor-input-hint-area)',
        );
        let title = document.querySelector(
            'input.serial-editor-input-hint-area',
        );
        if (serial && title) return { serial, title, source: 'legacy-class' };

        // 策略 2：按 placeholder 关键词匹配
        const allInputs = Array.from(document.querySelectorAll('input'));
        if (!serial) {
            serial = allInputs.find((el) =>
                /章节序号|序号|请输入序号/i.test(el.placeholder || ''),
            );
        }
        if (!title) {
            title = allInputs.find((el) =>
                /章节标题|请输入标题|标题/i.test(el.placeholder || ''),
            );
        }
        if (serial && title) return { serial, title, source: 'placeholder' };

        // 策略 3：按 aria-label
        if (!serial) {
            serial = allInputs.find((el) =>
                /序号/i.test(el.getAttribute('aria-label') || ''),
            );
        }
        if (!title) {
            title = allInputs.find((el) =>
                /标题/i.test(el.getAttribute('aria-label') || ''),
            );
        }
        if (serial && title) return { serial, title, source: 'aria-label' };

        // 策略 4：位置回退——ProseMirror 之前的最后两个可见 text/number input
        const editor = document.querySelector(
            'div.ProseMirror[contenteditable="true"]',
        );
        if (editor) {
            const editorRect = editor.getBoundingClientRect();
            const candidates = allInputs.filter((el) => {
                if (el.type && el.type !== 'text' && el.type !== 'number')
                    return false;
                const r = el.getBoundingClientRect();
                return (
                    r.top < editorRect.top &&
                    r.width > 0 &&
                    r.height > 0 &&
                    el.offsetParent !== null
                );
            });
            if (candidates.length >= 2) {
                // 章节序号一般在最前面（窄输入框），标题在其后（宽输入框）
                candidates.sort(
                    (a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top,
                );
                serial = serial || candidates[0];
                title = title || candidates[1];
                if (serial && title)
                    return { serial, title, source: 'position' };
            }
        }

        return { serial, title, source: 'incomplete' };
    }

    // ============================================================
    // 数据管理（按 bookId 分片）
    // ============================================================
    function loadChapters(bookId) {
        const bid = bookId || currentBookId();
        migrateLegacyIfNeeded(bid);
        return GM_getValue(keyFor(STORAGE_KEY_PREFIX, bid), null);
    }
    function saveChapters(chapters, bookId) {
        const bid = bookId || currentBookId();
        GM_setValue(keyFor(STORAGE_KEY_PREFIX, bid), chapters);
    }
    function loadProgress(bookId) {
        const bid = bookId || currentBookId();
        migrateLegacyIfNeeded(bid);
        return GM_getValue(keyFor(PROGRESS_KEY_PREFIX, bid), {
            lastSynced: 0,
            errors: [],
        });
    }
    function saveProgress(p, bookId) {
        const bid = bookId || currentBookId();
        GM_setValue(keyFor(PROGRESS_KEY_PREFIX, bid), p);
    }
    function loadPending(bookId) {
        const bid = bookId || currentBookId();
        return GM_getValue(keyFor(PENDING_KEY_PREFIX, bid), null);
    }
    function savePending(pending, bookId) {
        const bid = bookId || currentBookId();
        if (pending === null) {
            GM_setValue(keyFor(PENDING_KEY_PREFIX, bid), null);
        } else {
            GM_setValue(keyFor(PENDING_KEY_PREFIX, bid), pending);
            GM_setValue(LAST_BOOK_KEY, bid); // 记忆当前 book，用于跨页恢复
        }
    }
    function loadSettings() {
        return GM_getValue(SETTINGS_KEY, {
            localServer: 'http://127.0.0.1:19888',
            autoSaveLog: true,
        });
    }
    function saveSettings(s) {
        GM_setValue(SETTINGS_KEY, s);
    }

    // 日志持久化
    function loadLogs() {
        return GM_getValue(LOG_KEY, []);
    }
    function saveLogs(logs) {
        if (logs.length > MAX_LOGS) logs = logs.slice(-MAX_LOGS);
        GM_setValue(LOG_KEY, logs);
    }
    function appendLog(msg, type = 'info') {
        const logs = loadLogs();
        logs.push({ time: now(), msg, type, ts: Date.now() });
        saveLogs(logs);
    }

    // ============================================================
    // 样式
    // ============================================================
    // GM_addStyle 兜底（个别脚本管理器 / CSP 严格站点会缺）
    const addStyle =
        typeof GM_addStyle === 'function'
            ? GM_addStyle
            : function (css) {
                  const s = document.createElement('style');
                  s.textContent = css;
                  (document.head || document.documentElement).appendChild(s);
              };

    addStyle(`
/* ===== 番茄同步助手 面板 ===== */
#fq-sync-panel {
  position: fixed; right: 16px; bottom: 16px; z-index: 2147483647;
  width: 420px; max-height: 85vh;
  background: #fff; border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.1);
  font-family: "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;
  font-size: 13px; color: #333; line-height: 1.5;
  display: flex; flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}
#fq-sync-panel.collapsed { width: 56px; height: 56px; border-radius: 50%; cursor: pointer; }
#fq-sync-panel.collapsed .fq-body,
#fq-sync-panel.collapsed .fq-header-text { display: none; }
#fq-sync-panel.collapsed .fq-toggle-btn { right: 14px; }

.fq-header {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: #fff; padding: 12px 16px; display: flex; align-items: center;
  flex-shrink: 0; position: relative; min-height: 44px;
}
.fq-header-text h3 { font-size: 15px; font-weight: 600; letter-spacing: 0.5px; }
.fq-header-text span { font-size: 11px; opacity: 0.8; }
.fq-toggle-btn {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,0.2); border: none; color: #fff;
  width: 28px; height: 28px; border-radius: 50%; cursor: pointer;
  font-size: 14px; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.fq-toggle-btn:hover { background: rgba(255,255,255,0.35); }

.fq-body {
  flex: 1; overflow-y: auto; display: flex; flex-direction: column;
  max-height: calc(85vh - 44px);
}
.fq-body::-webkit-scrollbar { width: 4px; }
.fq-body::-webkit-scrollbar-thumb { background: #ccc; border-radius: 2px; }

/* Tabs */
.fq-tabs {
  display: flex; border-bottom: 1px solid #eee; flex-shrink: 0;
}
.fq-tab {
  flex: 1; padding: 8px 4px; text-align: center; cursor: pointer;
  font-size: 12px; color: #999; border-bottom: 2px solid transparent;
  transition: all 0.2s; user-select: none;
}
.fq-tab:hover { color: #666; }
.fq-tab.active { color: #e74c3c; border-bottom-color: #e74c3c; font-weight: 600; }

.fq-tab-content { display: none; padding: 12px; flex: 1; overflow-y: auto; }
.fq-tab-content.active { display: flex; flex-direction: column; }

/* Status bar */
.fq-status {
  background: #f8f9fa; border-radius: 8px; padding: 10px 12px;
  margin-bottom: 10px; display: grid; grid-template-columns: 1fr 1fr;
  gap: 6px; font-size: 12px; flex-shrink: 0;
}
.fq-status-item { display: flex; flex-direction: column; }
.fq-status-item .fq-label { color: #999; font-size: 11px; }
.fq-status-item .fq-value { font-weight: 600; }

.fq-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.fq-dot.green { background: #27ae60; box-shadow: 0 0 4px #27ae60; }
.fq-dot.red { background: #e74c3c; box-shadow: 0 0 4px #e74c3c; }

/* Progress */
.fq-progress-bg {
  height: 6px; background: #eee; border-radius: 3px; overflow: hidden; margin: 4px 0;
}
.fq-progress-fill {
  height: 100%; background: linear-gradient(90deg, #e74c3c, #f39c12);
  border-radius: 3px; transition: width 0.5s ease;
}

/* Buttons */
.fq-btn {
  padding: 7px 14px; border: none; border-radius: 6px; font-size: 12px;
  cursor: pointer; transition: all 0.2s; font-family: inherit;
  display: inline-flex; align-items: center; gap: 4px;
}
.fq-btn:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
.fq-btn:active { transform: translateY(0); }
.fq-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.fq-btn-primary { background: #e74c3c; color: #fff; }
.fq-btn-primary:hover { background: #c0392b; }
.fq-btn-secondary { background: #f1f3f5; color: #495057; }
.fq-btn-secondary:hover { background: #e9ecef; }
.fq-btn-danger { background: #fff; color: #e74c3c; border: 1px solid #e74c3c; }
.fq-btn-danger:hover { background: #fadbd8; }
.fq-btn-sm { padding: 4px 10px; font-size: 11px; }
.fq-btn-block { width: 100%; justify-content: center; }

.fq-btn-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }

/* Inputs */
.fq-input {
  padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px;
  font-size: 12px; font-family: inherit; outline: none; transition: border-color 0.2s;
}
.fq-input:focus { border-color: #e74c3c; }
.fq-input-sm { width: 60px; text-align: center; }

/* Range row */
.fq-range { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; flex-shrink: 0; }
.fq-range label { font-size: 12px; color: #666; white-space: nowrap; }

/* Chapter list */
.fq-ch-list {
  flex: 1; overflow-y: auto; border: 1px solid #eee; border-radius: 6px;
  min-height: 100px; max-height: 250px;
}
.fq-ch-item {
  display: flex; align-items: center; padding: 5px 8px;
  border-bottom: 1px solid #f5f5f5; font-size: 12px; gap: 6px;
  transition: background 0.15s; cursor: default;
}
.fq-ch-item:hover { background: #f8f9fa; }
.fq-ch-num { width: 28px; text-align: center; color: #aaa; font-size: 11px; flex-shrink: 0; }
.fq-ch-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fq-ch-words { font-size: 10px; color: #aaa; flex-shrink: 0; }
.fq-ch-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 8px; flex-shrink: 0;
}
.fq-ch-badge.ok { background: #d5f5e3; color: #27ae60; }
.fq-ch-badge.err { background: #fadbd8; color: #e74c3c; }
.fq-ch-badge.wait { background: #f1f3f5; color: #adb5bd; }
.fq-ch-badge.uploading { background: #d6eaf8; color: #2980b9; }
.fq-ch-badge.skip { background: #fdebd0; color: #f39c12; }

/* Filter */
.fq-filter {
  display: flex; gap: 6px; margin-bottom: 8px; flex-shrink: 0;
}
.fq-filter input { flex: 1; }

/* Drop zone */
.fq-dropzone {
  border: 2px dashed #ddd; border-radius: 8px; padding: 24px 12px;
  text-align: center; color: #999; font-size: 12px;
  transition: all 0.2s; cursor: pointer; flex-shrink: 0;
}
.fq-dropzone:hover, .fq-dropzone.drag-over {
  border-color: #e74c3c; color: #e74c3c; background: #fef5f5;
}
.fq-dropzone-md:hover, .fq-dropzone-md.drag-over {
  border-color: #27ae60; color: #27ae60; background: #f0faf4;
}
.fq-dropzone .fq-dz-icon { font-size: 28px; margin-bottom: 6px; }

/* Log */
.fq-log {
  flex: 1; overflow-y: auto; font-family: "Cascadia Code","Consolas","Courier New",monospace;
  font-size: 11px; line-height: 1.5; background: #212529; color: #ccc;
  border-radius: 6px; padding: 6px 8px; min-height: 120px; max-height: 300px;
}
.fq-log::-webkit-scrollbar { width: 4px; }
.fq-log::-webkit-scrollbar-thumb { background: #555; border-radius: 2px; }
.fq-log-line { padding: 1px 0; }
.fq-log-line .fq-log-ts { color: #666; margin-right: 6px; }
.fq-log-line.info .fq-log-msg { color: #d6eaf8; }
.fq-log-line.success .fq-log-msg { color: #d5f5e3; }
.fq-log-line.error .fq-log-msg { color: #ff6b6b; }
.fq-log-line.warn .fq-log-msg { color: #fdebd0; }

/* Instructions */
.fq-instructions {
  font-size: 12px; color: #666; line-height: 1.7;
}
.fq-instructions ol { padding-left: 18px; }
.fq-instructions li { margin-bottom: 3px; }
.fq-instructions code {
  background: #f1f3f5; padding: 1px 5px; border-radius: 3px;
  font-size: 11px; color: #e74c3c;
}

/* Settings */
.fq-settings-row { margin-bottom: 10px; }
.fq-settings-row label { display: block; font-size: 12px; color: #666; margin-bottom: 3px; }
.fq-settings-row .fq-input { width: 100%; }

/* Animations */
@keyframes fqPulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
.fq-pulse { animation: fqPulse 1.5s infinite; }
@keyframes fqFadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
.fq-fade-in { animation: fqFadeIn 0.25s ease; }

/* Toggle button when collapsed */
#fq-sync-panel.collapsed::after {
  content: '番';
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  font-size: 20px; font-weight: bold; color: #fff; pointer-events: none;
}
#fq-sync-panel.collapsed .fq-header { border-radius: 50%; width: 56px; height: 56px; justify-content: center; padding: 0; }
  `);

    // ============================================================
    // UI 创建
    // ============================================================
    function createPanel() {
        const panel = document.createElement('div');
        panel.id = 'fq-sync-panel';
        panel.innerHTML = `
<div class="fq-header">
  <div class="fq-header-text">
    <h3>同步助手</h3>
    <span>本地Markdown → 番茄作家网</span>
  </div>
  <button class="fq-toggle-btn" id="fq-toggle">−</button>
</div>
<div class="fq-body">
  <div class="fq-tabs">
    <div class="fq-tab active" data-tab="upload">上传</div>
    <div class="fq-tab" data-tab="chapters">章节</div>
    <div class="fq-tab" data-tab="logs">日志</div>
    <div class="fq-tab" data-tab="help">说明</div>
  </div>

  <!-- 上传 -->
  <div class="fq-tab-content active" data-tab="upload">
    <div class="fq-status" id="fq-status">
      <div class="fq-status-item">
        <span class="fq-label">连接</span>
        <span class="fq-value" id="fq-conn"><span class="fq-dot red"></span>未检测</span>
      </div>
      <div class="fq-status-item">
        <span class="fq-label">书籍</span>
        <span class="fq-value" id="fq-book">--</span>
      </div>
      <div class="fq-status-item">
        <span class="fq-label">章节</span>
        <span class="fq-value" id="fq-total">--</span>
      </div>
      <div class="fq-status-item">
        <span class="fq-label">已同步</span>
        <span class="fq-value" id="fq-synced">--</span>
      </div>
    </div>
    <div style="flex-shrink:0">
      <div style="display:flex;justify-content:space-between;font-size:11px;color:#999;margin-bottom:2px">
        <span>进度</span>
        <span id="fq-pct">0%</span>
      </div>
      <div class="fq-progress-bg"><div class="fq-progress-fill" id="fq-bar" style="width:0%"></div></div>
    </div>
    <div class="fq-range" style="margin-top:10px">
      <label>从第</label><input type="number" class="fq-input fq-input-sm" id="fq-from" value="1" min="1">
      <label>章 到第</label><input type="number" class="fq-input fq-input-sm" id="fq-to" value="1" min="1">
      <label>章</label>
    </div>
    <div class="fq-btn-row">
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-preview">预览</button>
      <button class="fq-btn fq-btn-primary" id="fq-start">开始同步</button>
      <button class="fq-btn fq-btn-danger" id="fq-stop" style="display:none">停止</button>
    </div>
    <div style="margin-top:6px" class="fq-btn-row">
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-resume">续传（跳过已同步）</button>
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-reset-progress" title="清除当前书的同步进度（不删除章节数据）">重置进度</button>
    </div>
  </div>

  <!-- 章节 -->
  <div class="fq-tab-content" data-tab="chapters">
    <div class="fq-dropzone" id="fq-dropzone">
      <div class="fq-dz-icon">📂</div>
      <div>拖拽 <strong>chapters-export.json</strong> 到此处</div>
      <div style="margin-top:4px">或点击选择文件</div>
      <input type="file" id="fq-file" accept=".json" style="display:none">
    </div>
    <div class="fq-dropzone fq-dropzone-md" id="fq-md-dropzone" style="margin-top:8px">
      <div class="fq-dz-icon">📝</div>
      <div>拖拽 <strong>正文/ch*.md</strong> 到此处（支持多选）</div>
      <div style="margin-top:4px">跳过 <code>node export-chapters.js</code>，直接解析 markdown</div>
      <input type="file" id="fq-md-file" accept=".md" multiple style="display:none">
    </div>
    <div class="fq-btn-row" style="margin:8px 0">
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-load-local">从本地服务器加载</button>
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-clear-data">清除数据</button>
    </div>
    <div class="fq-filter">
      <input type="text" class="fq-input" id="fq-ch-search" placeholder="搜索章节..." style="flex:1">
    </div>
    <div class="fq-ch-list" id="fq-ch-list">
      <div style="padding:16px;text-align:center;color:#aaa">请先导入章节数据</div>
    </div>
  </div>

  <!-- 日志 -->
  <div class="fq-tab-content" data-tab="logs">
    <div style="margin-bottom:6px;display:flex;gap:6px">
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-clear-log">清空日志</button>
      <button class="fq-btn fq-btn-secondary fq-btn-sm" id="fq-export-log">导出日志</button>
    </div>
    <div class="fq-log" id="fq-log"></div>
  </div>

  <!-- 说明 -->
  <div class="fq-tab-content" data-tab="help">
    <div class="fq-instructions">
      <h4 style="margin-bottom:6px;font-size:13px">使用步骤</h4>
      <ol>
        <li>切换到「<strong>章节</strong>」标签，导入章节 JSON 文件</li>
        <li>确认当前页面在番茄作家网的书籍管理页面</li>
        <li>切换到「<strong>上传</strong>」标签，设置同步范围</li>
        <li>点击「<strong>预览</strong>」确认章节列表</li>
        <li>点击「<strong>开始同步</strong>」，脚本会自动逐章上传</li>
      </ol>
      <h4 style="margin:10px 0 6px;font-size:13px">获取章节数据</h4>
      <p><strong>方式一（推荐）：</strong>直接从文件管理器拖拽 <code>chapters/ch_*.md</code> 文件到「章节」页面的绿色拖拽区，脚本自动解析。</p>
      <p><strong>兼容命名：</strong><code>ch_206.md</code> · <code>ch206.md</code> · <code>ch_001-标题.md</code> · <code>ch001-标题.md</code></p>
      <p><strong>方式二：</strong>在项目目录运行：</p>
      <pre style="background:#f8f9fa;padding:6px 8px;border-radius:4px;font-size:11px;margin:4px 0;overflow-x:auto">node export-chapters.js 项目名</pre>
      <p>生成 <code>chapters-export.json</code>，然后拖入「章节」页面的红色拖拽区。</p>
      <h4 style="margin:10px 0 6px;font-size:13px">本地服务器（可选）</h4>
      <p>运行本地服务器可实现：</p>
      <ul style="padding-left:18px;margin:4px 0">
        <li>直接从服务器加载章节数据</li>
        <li>同步进度自动保存到本地文件</li>
      </ul>
      <pre style="background:#f8f9fa;padding:6px 8px;border-radius:4px;font-size:11px;margin:4px 0;overflow-x:auto">node fanqie-gui/server.js</pre>
      <h4 style="margin:10px 0 6px;font-size:13px">注意事项</h4>
      <ul style="padding-left:18px;margin:4px 0">
        <li>同步过程中请<strong>不要切换页面</strong>或操作浏览器</li>
        <li>每章上传间隔约 3-4 秒，避免触发限流</li>
        <li>进度自动保存，关闭面板后重新打开可续传</li>
        <li>如遇失败，可在日志中查看原因后重试</li>
      </ul>
    </div>
  </div>
</div>
`;
        document.body.appendChild(panel);
        return panel;
    }

    // ============================================================
    // 日志系统
    // ============================================================
    let logEl = null;

    function log(msg, type = 'info') {
        if (!logEl) logEl = document.getElementById('fq-log');
        if (!logEl) return;
        const line = document.createElement('div');
        line.className = 'fq-log-line ' + type + ' fq-fade-in';
        line.innerHTML = `<span class="fq-log-ts">[${now()}]</span><span class="fq-log-msg">${escHtml(msg)}</span>`;
        logEl.appendChild(line);
        logEl.scrollTop = logEl.scrollHeight;
        appendLog(msg, type);
    }

    function restoreLogs() {
        if (!logEl) logEl = document.getElementById('fq-log');
        const logs = loadLogs();
        // Only restore last 100
        const recent = logs.slice(-100);
        recent.forEach((l) => {
            const line = document.createElement('div');
            line.className = 'fq-log-line ' + l.type;
            line.innerHTML = `<span class="fq-log-ts">[${l.time}]</span><span class="fq-log-msg">${escHtml(l.msg)}</span>`;
            logEl.appendChild(line);
        });
        logEl.scrollTop = logEl.scrollHeight;
    }

    function escHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    // ============================================================
    // 状态更新
    // ============================================================
    function refreshUI() {
        const chapters = loadChapters();
        const progress = loadProgress();
        const bookId = getBookId();

        // Connection
        const connEl = document.getElementById('fq-conn');
        if (bookId) {
            connEl.innerHTML = '<span class="fq-dot green"></span>已连接';
        } else {
            connEl.innerHTML = '<span class="fq-dot red"></span>未在作家页';
        }

        // Book ID
        document.getElementById('fq-book').textContent = bookId || '--';

        // Chapters
        const total = chapters ? chapters.length : 0;
        document.getElementById('fq-total').textContent = total || '--';
        document.getElementById('fq-synced').textContent =
            (progress.lastSynced || 0) + '/' + (total || '--');

        // Progress bar
        const pct = total ? Math.round((progress.lastSynced / total) * 100) : 0;
        document.getElementById('fq-bar').style.width = pct + '%';
        document.getElementById('fq-pct').textContent = pct + '%';

        // Range inputs
        const fromEl = document.getElementById('fq-from');
        const toEl = document.getElementById('fq-to');
        if (total) {
            fromEl.max = total;
            toEl.max = total;
            toEl.value = total;
            if (progress.lastSynced > 0 && progress.lastSynced < total) {
                fromEl.value = progress.lastSynced + 1;
            }
        }

        // Chapter list
        renderChapterList(chapters, progress);
    }

    function renderChapterList(chapters, progress) {
        const container = document.getElementById('fq-ch-list');
        if (!chapters || chapters.length === 0) {
            container.innerHTML =
                '<div style="padding:16px;text-align:center;color:#aaa">请先导入章节数据</div>';
            return;
        }

        const lastSynced = progress.lastSynced || 0;
        const errors = progress.errors || [];

        let html = '';
        for (let i = 0; i < chapters.length; i++) {
            const num = i + 1;
            const ch = chapters[i];
            const body = extractBody(ch.content);
            const isSynced = num <= lastSynced;
            const isFailed = errors.some((e) => e.chapter === num);
            let badgeClass = 'wait',
                badgeText = '待上传';
            if (isFailed) {
                badgeClass = 'err';
                badgeText = '失败';
            } else if (isSynced) {
                badgeClass = 'ok';
                badgeText = '已同步';
            }

            html += `<div class="fq-ch-item" data-idx="${num}">
        <span class="fq-ch-num">${num}</span>
        <span class="fq-ch-title" title="${escHtml(ch.title)}">${escHtml(ch.title)}</span>
        <span class="fq-ch-words">${body.length}字</span>
        <span class="fq-ch-badge ${badgeClass}">${badgeText}</span>
      </div>`;
        }
        container.innerHTML = html;
    }

    // ============================================================
    // 上传自动化
    // ============================================================
    let running = false;
    let stopFlag = false;

    async function waitForEditor(maxWait = 15000) {
        const start = Date.now();
        while (Date.now() - start < maxWait) {
            const { serial, title, source } = findChapterInputs();
            const editor = document.querySelector(
                'div.ProseMirror[contenteditable="true"]',
            );
            if (serial && title && editor) {
                if (source !== 'legacy-class') {
                    log(`⚙ 章节输入框识别策略：${source}`, 'info');
                }
                return { serialInput: serial, titleInput: title, editor };
            }
            await sleep(500);
        }
        // 超时前打印诊断
        const dump = Array.from(document.querySelectorAll('input')).map((el) => ({
            cls: el.className,
            ph: el.placeholder,
            aria: el.getAttribute('aria-label'),
        }));
        console.error('[fanqie-sync] 编辑器输入框识别失败，当前所有 input:', dump);
        throw new Error(
            '等待编辑器超时（找不到章节序号/标题输入框，查看控制台 error 排查）',
        );
    }

    /**
     * 从完整标题 "第9章 立案" 中提取章节序号 "9"
     */
    function extractChapterNum(fullTitle) {
        const m = fullTitle.match(/^第(\d+)章/);
        return m ? m[1] : '';
    }

    // ============================================================
    // 上传自动化（修复版：location.href 会销毁当前页面，必须用 PENDING 状态恢复）
    // ============================================================

    /**
     * 步骤1：跳转到发布编辑页。将章节数据和循环上下文存入 PENDING_KEY，
     * 然后通过 location.href 跳转。当前脚本执行到此结束，新页面会
     * 通过 resumePendingUpload() 恢复。
     */
    function uploadChapter(chapter, loopCtx) {
        const bookId = getBookId();
        if (!bookId) {
            log('错误：未在书籍页面', 'error');
            return;
        }

        // 保存待恢复的上下文（跳转后当前脚本就死了，靠这个在新页面恢复）
        const pending = {
            action: 'upload',
            title: chapter.title,
            content: chapter.content,
            chapterNum: loopCtx.chapterNum,
            from: loopCtx.from,
            to: loopCtx.to,
            skipSynced: loopCtx.skipSynced,
            total: loopCtx.total,
            bookId: bookId, // 记录来源书，防止跳转后 bookId 变更
        };
        savePending(pending, bookId);

        log('正在打开编辑页面...');
        location.href = `https://fanqienovel.com/main/writer/${bookId}/publish/?enter_from=chapterlist`;
        // ⚠️ 脚本在此终止，后续逻辑在 resumePendingUpload() 中
    }

    /**
     * 步骤2：在新加载的编辑页面中恢复上传 — 填标题、填正文、点保存。
     * 保存成功后，自动跳到下一章或结束循环。
     */
    async function resumePendingUpload() {
        // 先从当前 book 的 pending 读；若没有，再看上次记忆的 book（跨页导航中转）
        const pendingBook = currentBookId();
        let pending = loadPending(pendingBook);
        if (!pending || pending.action !== 'upload') return false;

        // 用 pending.bookId 作为权威（防止 URL 变更导致误取）
        const bookId = pending.bookId || pendingBook;

        // 清除 pending，防止重复触发
        savePending(null, bookId);

        const title = extractTitle(pending.title);
        const body = extractBody(pending.content);
        const chapterNum = pending.chapterNum;
        const total = pending.total;

        running = true;
        stopFlag = false;
        setRunningUI(true);
        log(`=== 继续同步: 第${chapterNum}章 - 第${pending.to}章 ===`);
        log(`[${chapterNum}/${total}] ${pending.title}`);

        try {
            // 等待编辑器加载
            const { serialInput, titleInput, editor } = await waitForEditor();
            const chapterNumStr = extractChapterNum(pending.title);

            // ============================================================
            // 通用填写函数：快速填 → 校验 → 失败则逐字符打字兜底
            // ============================================================
            async function fillInput(el, wanted, label) {
                // 第一次：快速填
                el.focus();
                el.click();
                await sleep(200);
                setNativeValue(el, '');
                await sleep(80);
                setNativeValue(el, wanted);
                await sleep(300);
                commitInput(el);
                await sleep(300);
                if (el.value === wanted) {
                    log(`  ✓ ${label}="${wanted}"（快速填）`, 'info');
                    return;
                }

                // 第二次：逐字符打字（模拟真实键盘输入）
                log(
                    `  ⚠ ${label} 快速填失败（DOM="${el.value}"），改用逐字符输入`,
                    'warn',
                );
                await typeCharByChar(el, wanted);
                await sleep(300);
                commitInput(el);
                await sleep(400);
                if (el.value === wanted) {
                    log(`  ✓ ${label}="${wanted}"（逐字符）`, 'info');
                    return;
                }

                // 两次都失败 → 报错
                throw new Error(
                    `${label} 写入失败：期望 "${wanted}"，DOM 实际 "${el.value}"`,
                );
            }

            // --- 填写章节序号 ---
            await fillInput(serialInput, chapterNumStr, '序号');

            // --- 填写章节标题 ---
            await fillInput(titleInput, title, '标题');

            // --- 填写正文（ProseMirror 编辑器） ---
            editor.focus();
            editor.click();
            await sleep(300);

            // 选中编辑器现有全部内容
            const sel = window.getSelection();
            sel.selectAllChildren(editor);
            await sleep(100);

            // 用 DataTransfer 模拟粘贴事件 — ProseMirror 监听原生 paste
            const htmlContent = contentToHtml(body);
            const dt = new DataTransfer();
            dt.setData('text/html', htmlContent);
            dt.setData('text/plain', body);

            const pasteEvent = new ClipboardEvent('paste', {
                bubbles: true,
                cancelable: true,
                clipboardData: dt,
            });
            editor.dispatchEvent(pasteEvent);
            await sleep(1000);

            // --- 验证内容 ---
            const editorText = editor.innerText || '';
            if (editorText.length < body.length * 0.5) {
                log(
                    `警告：编辑器内容(${editorText.length}字)远少于预期(${body.length}字)`,
                    'warn',
                );
            }

            // --- 存前保护：编辑正文过程可能触发 React 表单重置 ---
            //     检查序号/标题是否还在，不在就补填一次
            if (serialInput.value !== chapterNumStr) {
                log(
                    `⚠ 保存前发现序号丢失（DOM="${serialInput.value}"），补填`,
                    'warn',
                );
                await fillInput(serialInput, chapterNumStr, '序号(补)');
            }
            if (titleInput.value !== title) {
                log(
                    `⚠ 保存前发现标题丢失（DOM="${titleInput.value}"），补填`,
                    'warn',
                );
                await fillInput(titleInput, title, '标题(补)');
            }

            // 存前把焦点强制移出输入框，让 React commit 所有 pending state
            document.body.focus();
            await sleep(400);

            // --- 点击"存草稿" ---
            log('正在保存...');
            const allBtns = document.querySelectorAll('button');
            let saveBtn = null;
            for (const b of allBtns) {
                const t = b.textContent.trim();
                if (t === '存草稿' || t === '保存草稿' || t === '保存' || t === '存为草稿') {
                    saveBtn = b;
                    break;
                }
            }
            if (!saveBtn) {
                const btnTexts = Array.from(allBtns).map((b) =>
                    b.textContent.trim(),
                );
                console.error('[fanqie-sync] 找不到存草稿按钮，页面所有按钮文本:', btnTexts);
                throw new Error(
                    '找不到"存草稿"按钮（可能改名了，控制台有按钮文本清单）',
                );
            }

            saveBtn.scrollIntoView({ block: 'center' });
            await sleep(300);
            saveBtn.click();
            await sleep(3000);

            // --- 验证保存结果 ---
            const pageText = document.body.innerText || '';
            if (pageText.includes('错误') || pageText.includes('失败')) {
                throw new Error('保存失败：页面显示错误');
            }
            log('✓ 已保存到云端', 'success');

            // 更新进度
            const progress = loadProgress(bookId);
            progress.lastSynced = Math.max(progress.lastSynced, chapterNum);
            saveProgress(progress, bookId);
            syncProgressToServer(chapterNum);

            // --- 检查停止标志 ---
            if (stopFlag) {
                log('用户停止同步', 'warn');
                finishSync(total, pending);
                return true;
            }

            // --- 跳到下一章 ---
            const chapters = loadChapters(bookId);
            const nextIdx = chapterNum; // chapterNum 是 1-based，下一章的下标 = chapterNum
            const endIdx = Math.min(
                pending.to,
                chapters ? chapters.length : total,
            );

            if (chapters && nextIdx < endIdx) {
                // 还有下一章 → 保存下一章的 pending 并跳转
                const nextCh = chapters[nextIdx];
                const nextNum = nextIdx + 1;
                const nextPending = {
                    action: 'upload',
                    title: nextCh.title,
                    content: nextCh.content,
                    chapterNum: nextNum,
                    from: pending.from,
                    to: pending.to,
                    skipSynced: pending.skipSynced,
                    total: total,
                    bookId: bookId,
                };

                // 跳过已同步的
                const progress2 = loadProgress(bookId);
                if (pending.skipSynced && nextNum <= progress2.lastSynced) {
                    log(
                        `[${nextNum}/${total}] ${nextCh.title} — 已同步，跳过`,
                        'info',
                    );
                    // 递归跳过
                    const nextNext = locateNextUnsaved(
                        chapters,
                        nextNum,
                        endIdx,
                        progress2,
                        pending,
                        total,
                    );
                    if (nextNext) {
                        nextNext.bookId = bookId;
                        savePending(nextNext, bookId);
                        location.href = `https://fanqienovel.com/main/writer/${bookId}/publish/?enter_from=chapterlist`;
                    } else {
                        finishSync(total, pending);
                    }
                } else {
                    savePending(nextPending, bookId);
                    await sleep(DELAY);
                    location.href = `https://fanqienovel.com/main/writer/${bookId}/publish/?enter_from=chapterlist`;
                }
            } else {
                // 全部完成
                finishSync(total, pending);
            }
            return true;
        } catch (e) {
            log(`✗ ${pending.title}: ${e.message}`, 'error');
            const progress = loadProgress(bookId);
            progress.errors.push({
                chapter: chapterNum,
                title: pending.title,
                error: e.message,
                time: new Date().toISOString(),
            });
            saveProgress(progress, bookId);

            // 失败后也尝试继续下一章
            const chapters = loadChapters(bookId);
            const nextIdx = chapterNum;
            const endIdx = Math.min(
                pending.to,
                chapters ? chapters.length : total,
            );
            if (chapters && nextIdx < endIdx) {
                const nextCh = chapters[nextIdx];
                const nextPending = {
                    action: 'upload',
                    title: nextCh.title,
                    content: nextCh.content,
                    chapterNum: nextIdx + 1,
                    from: pending.from,
                    to: pending.to,
                    skipSynced: pending.skipSynced,
                    total: total,
                    bookId: bookId,
                };
                savePending(nextPending, bookId);
                await sleep(2000);
                location.href = `https://fanqienovel.com/main/writer/${bookId}/publish/?enter_from=chapterlist`;
            } else {
                finishSync(total, pending);
            }
            return false;
        }
    }

    function locateNextUnsaved(
        chapters,
        fromIdx,
        endIdx,
        progress,
        pending,
        total,
    ) {
        for (let i = fromIdx; i < endIdx; i++) {
            if (!pending.skipSynced || i + 1 > progress.lastSynced) {
                const ch = chapters[i];
                return {
                    action: 'upload',
                    title: ch.title,
                    content: ch.content,
                    chapterNum: i + 1,
                    from: pending.from,
                    to: pending.to,
                    skipSynced: pending.skipSynced,
                    total: total,
                };
            }
        }
        return null;
    }

    function finishSync(total, pending) {
        running = false;
        setRunningUI(false);
        log(`=== 同步完成: 上次处理到第${pending.chapterNum}章 ===`, 'success');
        appendLog(`=== 同步完成 ===`, 'success');
        refreshUI();
    }

    /**
     * 手动触发同步（从面板点击"开始同步"）
     */
    async function runUpload(from, to, skipSynced = false) {
        const chapters = loadChapters();
        if (!chapters) {
            log('没有章节数据，请先导入', 'error');
            return;
        }

        const startIdx = from - 1;
        const endIdx = Math.min(to, chapters.length);
        const progress = loadProgress();

        // 跳过已同步的章，找到第一个需要同步的
        let firstIdx = startIdx;
        if (skipSynced) {
            while (firstIdx < endIdx && firstIdx + 1 <= progress.lastSynced) {
                firstIdx++;
            }
            if (firstIdx >= endIdx) {
                log('所有章节已同步', 'info');
                return;
            }
        }

        const firstCh = chapters[firstIdx];
        const firstNum = firstIdx + 1;

        running = true;
        stopFlag = false;
        setRunningUI(true);
        log(`=== 开始同步: 第${from}章 - 第${endIdx}章 ===`);

        updateChapterBadge(firstNum, 'uploading', '上传中');
        updateProgress(firstNum, chapters.length);
        log(`[${firstNum}/${chapters.length}] ${firstCh.title}`);

        uploadChapter(firstCh, {
            chapterNum: firstNum,
            from: from,
            to: endIdx,
            skipSynced: skipSynced,
            total: chapters.length,
        });
    }

    function updateChapterBadge(num, cls, text) {
        const item = document.querySelector(`.fq-ch-item[data-idx="${num}"]`);
        if (item) {
            const badge = item.querySelector('.fq-ch-badge');
            if (badge) {
                badge.className = 'fq-ch-badge ' + cls;
                badge.textContent = text;
            }
        }
    }

    function updateProgress(current, total) {
        const pct = Math.round((current / total) * 100);
        document.getElementById('fq-bar').style.width = pct + '%';
        document.getElementById('fq-pct').textContent =
            `${current}/${total} (${pct}%)`;
        document.getElementById('fq-synced').textContent =
            current + '/' + total;
    }

    function setRunningUI(isRunning) {
        document.getElementById('fq-start').style.display = isRunning
            ? 'none'
            : '';
        document.getElementById('fq-stop').style.display = isRunning
            ? ''
            : 'none';
        document.getElementById('fq-resume').style.display = isRunning
            ? 'none'
            : '';
        document.getElementById('fq-preview').disabled = isRunning;
        if (isRunning) {
            document.getElementById('fq-start').classList.add('fq-pulse');
        } else {
            document.getElementById('fq-start').classList.remove('fq-pulse');
        }
    }

    // ============================================================
    // 本地服务器通信
    // ============================================================
    function syncProgressToServer(chapterNum) {
        const settings = loadSettings();
        if (!settings.localServer) return;
        try {
            GM_xmlhttpRequest({
                method: 'POST',
                url: settings.localServer + '/api/progress',
                data: JSON.stringify({ lastSynced: chapterNum }),
                headers: { 'Content-Type': 'application/json' },
                timeout: 3000,
            });
        } catch (e) {
            /* 静默失败 */
        }
    }

    function loadFromServer() {
        const settings = loadSettings();
        if (!settings.localServer) {
            log('请先在设置中配置本地服务器地址', 'warn');
            return;
        }
        log('正在从本地服务器加载章节数据...');
        GM_xmlhttpRequest({
            method: 'GET',
            url: settings.localServer + '/api/chapters',
            timeout: 10000,
            onload: function (res) {
                try {
                    const data = JSON.parse(res.responseText);
                    if (data.chapters && data.chapters.length > 0) {
                        saveChapters(data.chapters);
                        log(`已加载 ${data.chapters.length} 章`, 'success');
                        refreshUI();
                    } else {
                        log('服务器返回空数据', 'warn');
                    }
                } catch (e) {
                    log('解析服务器数据失败: ' + e.message, 'error');
                }
            },
            onerror: function () {
                log('无法连接本地服务器。请确认 server.js 已启动。', 'error');
            },
            ontimeout: function () {
                log('连接本地服务器超时', 'error');
            },
        });
    }

    // ============================================================
    // 文件导入
    // ============================================================
    function handleFile(file) {
        if (!file || !file.name.endsWith('.json')) {
            log('请选择 JSON 文件', 'error');
            return;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
            try {
                const data = JSON.parse(e.target.result);
                if (!Array.isArray(data) || data.length === 0) {
                    log('文件格式错误：应为章节数组', 'error');
                    return;
                }
                saveChapters(data);
                log(`已导入 ${data.length} 章: ${file.name}`, 'success');
                refreshUI();
            } catch (err) {
                log('JSON 解析失败: ' + err.message, 'error');
            }
        };
        reader.readAsText(file);
    }

    // ---- Markdown 章节解析（整合 export-chapters.js 功能） ----
    // 兼容三种文件命名：
    //   ch_206.md            ← 当前：下划线+数字（标题在正文首行）
    //   ch206.md             ← 纯数字（标题在正文首行）
    //   ch_001-开局觉醒.md   ← 旧格式：数字后跟标题
    //   ch001-开局觉醒.md    ← 旧格式无下划线
    const MD_CHAPTER_RE = /^ch[_-]?(\d+)(?:[-_](.+))?\.md$/i;

    function parseMdFile(name, text) {
        const m = name.match(MD_CHAPTER_RE);
        if (!m) return null;
        const num = parseInt(m[1]);
        const fileTitle = m[2] || ''; // 新文件名可能没有标题段

        const lines = text.split('\n');
        const titleLine = (lines[0] || '').trim();

        // 支持多种正文首行格式：
        //   # 第206章 碎片共鸣               ← 当前主流
        //   # ch206 — 碎片共鸣 / # ch206 - 碎片共鸣  ← 旧格式
        //   # 碎片共鸣                       ← 极简格式
        let chapterTitle = '';
        let m2 = titleLine.match(
            /^#\s*第[零一二三四五六七八九十百千\d]+章\s*(.+)/,
        );
        if (m2) {
            chapterTitle = m2[1].trim();
        } else if ((m2 = titleLine.match(/^#\s*ch\d+\s*[—\-]\s*(.+)/i))) {
            chapterTitle = m2[1].trim();
        } else if ((m2 = titleLine.match(/^#\s*(.+)/))) {
            chapterTitle = m2[1].trim();
        }

        // 兜底：正文首行没解出来 → 用文件名的标题段 → 再兜到空
        if (!chapterTitle) chapterTitle = fileTitle || `第${num}章`;

        const fullTitle = `第${num}章 ${chapterTitle}`;

        // Skip title line + blank lines
        let bodyStart = 1;
        while (bodyStart < lines.length && !lines[bodyStart].trim())
            bodyStart++;
        const body = lines.slice(bodyStart).join('\n').trim();

        return { title: fullTitle, content: body, num };
    }

    function handleMdFiles(files) {
        const mdFiles = Array.from(files).filter((f) => f.name.endsWith('.md'));
        if (mdFiles.length === 0) {
            log('没有 .md 文件', 'error');
            return;
        }
        log(`正在解析 ${mdFiles.length} 个 .md 文件...`, 'info');

        let done = 0;
        const parsed = [];
        mdFiles.forEach((file) => {
            const reader = new FileReader();
            reader.onload = function (e) {
                const ch = parseMdFile(file.name, e.target.result);
                if (ch) {
                    parsed.push(ch);
                } else {
                    log(
                        `⚠ 跳过: ${file.name}（文件名需以 ch 开头 + 数字，如 ch_206.md / ch206.md / ch_001-标题.md）`,
                        'warn',
                    );
                }
                done++;
                if (done === mdFiles.length) finishMdImport(parsed);
            };
            reader.onerror = function () {
                log(`读取失败: ${file.name}`, 'error');
                done++;
                if (done === mdFiles.length) finishMdImport(parsed);
            };
            reader.readAsText(file);
        });
    }

    function finishMdImport(parsed) {
        if (parsed.length === 0) {
            log('没有解析到任何章节', 'error');
            return;
        }
        // 按章节号排序
        parsed.sort((a, b) => a.num - b.num);
        const chapters = parsed.map(({ title, content }) => ({
            title,
            content,
        }));

        // 合并策略：替换序号范围内已有章节，保留范围外的
        const existing = loadChapters() || [];
        const minNum = parsed[0].num;
        const maxNum = parsed[parsed.length - 1].num;
        const merged = existing.filter(
            (_, i) => i + 1 < minNum || i + 1 > maxNum,
        );

        // 找到插入位置
        const insertIdx = existing.findIndex((_, i) => i + 1 >= minNum);
        if (insertIdx === -1) {
            merged.push(...chapters);
        } else {
            merged.splice(insertIdx, 0, ...chapters);
        }

        saveChapters(merged);
        log(
            `✅ 已解析 ${parsed.length} 章 (第${minNum}-${maxNum}章)，共 ${merged.length} 章`,
            'success',
        );
        refreshUI();
    }

    // ============================================================
    // 事件绑定
    // ============================================================
    function bindEvents(panel) {
        // Tab 切换
        panel.querySelectorAll('.fq-tab').forEach((tab) => {
            tab.addEventListener('click', () => {
                panel
                    .querySelectorAll('.fq-tab')
                    .forEach((t) => t.classList.remove('active'));
                panel
                    .querySelectorAll('.fq-tab-content')
                    .forEach((c) => c.classList.remove('active'));
                tab.classList.add('active');
                panel
                    .querySelector(
                        `.fq-tab-content[data-tab="${tab.dataset.tab}"]`,
                    )
                    .classList.add('active');
            });
        });

        // 最小化/展开
        document.getElementById('fq-toggle').addEventListener('click', () => {
            panel.classList.toggle('collapsed');
            const btn = document.getElementById('fq-toggle');
            btn.textContent = panel.classList.contains('collapsed') ? '+' : '−';
        });

        // 开始同步
        document.getElementById('fq-start').addEventListener('click', () => {
            const from =
                parseInt(document.getElementById('fq-from').value) || 1;
            const to = parseInt(document.getElementById('fq-to').value) || 200;
            runUpload(from, to);
        });

        // 续传
        document.getElementById('fq-resume').addEventListener('click', () => {
            const progress = loadProgress();
            const chapters = loadChapters();
            const from = (progress.lastSynced || 0) + 1;
            const to = chapters ? chapters.length : 200;
            document.getElementById('fq-from').value = from;
            document.getElementById('fq-to').value = to;
            log(`续传：从第${from}章开始`);
            runUpload(from, to, true);
        });

        // 重置当前书的进度（不动章节数据）
        document
            .getElementById('fq-reset-progress')
            .addEventListener('click', () => {
                const bid = currentBookId();
                const pr = loadProgress();
                if (
                    !confirm(
                        `确定重置当前书（bookId=${bid}）的同步进度？\n当前 lastSynced=${pr.lastSynced}，错误数=${(pr.errors || []).length}`,
                    )
                )
                    return;
                saveProgress({ lastSynced: 0, errors: [] });
                savePending(null);
                log(`已重置进度（${bid}）`, 'warn');
                refreshUI();
            });

        // 停止
        document.getElementById('fq-stop').addEventListener('click', () => {
            stopFlag = true;
            savePending(null); // 清除当前书的待恢复上传任务
            log('正在停止...');
        });

        // 预览
        document.getElementById('fq-preview').addEventListener('click', () => {
            const chapters = loadChapters();
            if (!chapters) {
                log('没有章节数据', 'error');
                return;
            }
            const from =
                parseInt(document.getElementById('fq-from').value) || 1;
            const to =
                parseInt(document.getElementById('fq-to').value) ||
                chapters.length;
            log(`预览: 第${from}章 - 第${Math.min(to, chapters.length)}章`);
            for (let i = from - 1; i < Math.min(to, chapters.length); i++) {
                const body = extractBody(chapters[i].content);
                log(
                    `  [${i + 1}] ${chapters[i].title} (${body.length}字)`,
                    'info',
                );
            }
            // 切换到日志标签
            panel.querySelector('.fq-tab[data-tab="logs"]').click();
        });

        // JSON 文件拖拽
        const dropzone = document.getElementById('fq-dropzone');
        const fileInput = document.getElementById('fq-file');

        dropzone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) handleFile(e.target.files[0]);
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('drag-over');
        });
        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('drag-over');
        });
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
            if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        });

        // Markdown 文件拖拽（支持多选）
        const mdDropzone = document.getElementById('fq-md-dropzone');
        const mdFileInput = document.getElementById('fq-md-file');

        mdDropzone.addEventListener('click', () => mdFileInput.click());
        mdFileInput.addEventListener('change', (e) => {
            if (e.target.files.length) handleMdFiles(e.target.files);
        });

        mdDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            mdDropzone.classList.add('drag-over');
        });
        mdDropzone.addEventListener('dragleave', () => {
            mdDropzone.classList.remove('drag-over');
        });
        mdDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            mdDropzone.classList.remove('drag-over');
            if (e.dataTransfer.files.length)
                handleMdFiles(e.dataTransfer.files);
        });

        // 从服务器加载
        document
            .getElementById('fq-load-local')
            .addEventListener('click', loadFromServer);

        // 清除数据
        document
            .getElementById('fq-clear-data')
            .addEventListener('click', () => {
                const bid = currentBookId();
                if (
                    confirm(
                        `确定清除当前书（bookId=${bid}）的章节数据？（不会影响同步进度）`,
                    )
                ) {
                    saveChapters(null);
                    log(`已清除章节数据（${bid}）`, 'warn');
                    refreshUI();
                }
            });

        // 搜索
        document
            .getElementById('fq-ch-search')
            .addEventListener('input', (e) => {
                const q = e.target.value.trim().toLowerCase();
                document.querySelectorAll('.fq-ch-item').forEach((item) => {
                    const title = item
                        .querySelector('.fq-ch-title')
                        .textContent.toLowerCase();
                    const num = item.querySelector('.fq-ch-num').textContent;
                    item.style.display =
                        !q || title.includes(q) || num.includes(q)
                            ? ''
                            : 'none';
                });
            });

        // 清空日志
        document
            .getElementById('fq-clear-log')
            .addEventListener('click', () => {
                document.getElementById('fq-log').innerHTML = '';
                GM_setValue(LOG_KEY, []);
                log('日志已清空');
            });

        // 导出日志
        document
            .getElementById('fq-export-log')
            .addEventListener('click', () => {
                const logs = loadLogs();
                const text = logs
                    .map((l) => `[${l.time}] [${l.type}] ${l.msg}`)
                    .join('\n');
                const blob = new Blob([text], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `同步日志_${new Date().toISOString().slice(0, 10)}.txt`;
                a.click();
                URL.revokeObjectURL(url);
                log('日志已导出', 'success');
            });
    }

    // ============================================================
    // 初始化
    // ============================================================
    let initialized = false;

    function init() {
        // 允许被自愈流程重复调用：只要面板不在，就重建
        if (document.getElementById('fq-sync-panel')) return;

        const panel = createPanel();
        bindEvents(panel);
        logEl = document.getElementById('fq-log');
        restoreLogs();
        refreshUI();

        if (!initialized) {
            initialized = true;
            log('同步助手已加载');

            // 检查是否有中断的同步任务需要恢复（只在首次初始化时做）
            const pending = loadPending();
            if (pending && pending.action === 'upload') {
                log(
                    `检测到未完成的同步任务：第${pending.chapterNum}章 ${pending.title}，自动恢复...`,
                    'info',
                );
                setTimeout(() => resumePendingUpload(), 1500);
            }

            // 定时刷新状态（不在同步中时）
            setInterval(() => {
                if (!running) refreshUI();
            }, 10000);
        } else {
            log('面板已重建（页面重渲染后自愈）', 'warn');
        }
    }

    // SPA 自愈：番茄作家网是 React SPA，首次挂载会替换 body，
    // 会把我们注入的面板一起冲掉。用 MutationObserver 侦测面板消失并重建。
    function startSelfHeal() {
        const observer = new MutationObserver(() => {
            if (!document.getElementById('fq-sync-panel')) {
                init();
            }
        });
        observer.observe(document.body, { childList: true, subtree: false });
    }

    // 兜底：如果 5 秒后面板仍未出现，强行再试一次（有的浏览器 load 事件晚于 SPA 首次渲染）
    function safeInit() {
        try {
            init();
            startSelfHeal();
        } catch (e) {
            console.error('[fanqie-sync] init 失败:', e);
            alert('番茄同步助手初始化失败: ' + e.message + '\n请打开控制台查看详情');
        }
    }

    // 注册菜单命令（Tampermonkey / 脚本猫 右键菜单）
    if (typeof GM_registerMenuCommand === 'function') {
        GM_registerMenuCommand('打开同步面板', () => {
            if (!document.getElementById('fq-sync-panel')) init();
            const panel = document.getElementById('fq-sync-panel');
            if (panel) panel.classList.remove('collapsed');
        });
        GM_registerMenuCommand('重新注入面板', () => {
            const old = document.getElementById('fq-sync-panel');
            if (old) old.remove();
            init();
        });
    }

    // 页面加载完成后初始化 + 冗余兜底
    if (document.readyState === 'complete') {
        safeInit();
    } else {
        window.addEventListener('load', safeInit);
    }
    // 多次兜底：0.5s / 2s / 5s / 10s 各试一次，覆盖 SPA 慢挂载场景
    [500, 2000, 5000, 10000].forEach((delay) => {
        setTimeout(() => {
            if (!document.getElementById('fq-sync-panel')) safeInit();
        }, delay);
    });
})();
