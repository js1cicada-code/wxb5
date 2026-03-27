/**
 * 性能优化工具库
 * 用于优化彩票选号H5应用
 */

// ============================================
// 1. 数据结构优化 - 使用Map加速查找
// ============================================

class MatchDataManager {
    constructor() {
        this.matchList = [];
        this.matchMap = new Map();
        this.selections = {};
    }

    setMatches(matches) {
        this.matchList = matches;
        this.matchMap.clear();
        matches.forEach(m => {
            this.matchMap.set(String(m.id), m);
            if (!this.selections[String(m.id)]) {
                this.selections[String(m.id)] = { spf: [], bf: [], bqc: [], zjq: [], sxds: [] };
            }
        });
    }

    getMatch(id) {
        return this.matchMap.get(String(id));
    }

    hasMatch(id) {
        return this.matchMap.has(String(id));
    }

    getSelection(id) {
        const idStr = String(id);
        if (!this.selections[idStr]) {
            this.selections[idStr] = { spf: [], bf: [], bqc: [], zjq: [], sxds: [] };
        }
        return this.selections[idStr];
    }

    getSelectedMatchCount() {
        let count = 0;
        for (const id in this.selections) {
            const sel = this.selections[id];
            if (sel.spf.length > 0 || sel.bf.length > 0 || sel.bqc.length > 0 || sel.zjq.length > 0 || sel.sxds.length > 0) {
                count++;
            }
        }
        return count;
    }

    clearSelections() {
        for (const id in this.selections) {
            this.selections[id] = { spf: [], bf: [], bqc: [], zjq: [], sxds: [] };
        }
    }
}

// ============================================
// 2. DOM缓存管理器
// ============================================

class DOMCache {
    constructor() {
        this.cache = new Map();
    }

    get(id) {
        if (!this.cache.has(id)) {
            this.cache.set(id, document.getElementById(id));
        }
        return this.cache.get(id);
    }

    clear() {
        this.cache.clear();
    }
}

// ============================================
// 3. 文档片段批量渲染
// ============================================

function createDocumentFragment(html) {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content;
}

function batchRender(container, items, renderFn) {
    const fragment = document.createDocumentFragment();
    
    items.forEach((item, index) => {
        const element = renderFn(item, index);
        if (typeof element === 'string') {
            const div = document.createElement('div');
            div.innerHTML = element;
            while (div.firstChild) {
                fragment.appendChild(div.firstChild);
            }
        } else {
            fragment.appendChild(element);
        }
    });
    
    container.innerHTML = '';
    container.appendChild(fragment);
}

// ============================================
// 4. 事件委托
// ============================================

function delegate(container, selector, eventType, handler) {
    container.addEventListener(eventType, function(event) {
        const target = event.target.closest(selector);
        if (target && container.contains(target)) {
            handler.call(target, event, target);
        }
    });
}

// ============================================
// 5. 防抖和节流
// ============================================

function debounce(fn, delay = 300) {
    let timer = null;
    return function(...args) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
            fn.apply(this, args);
        }, delay);
    };
}

function throttle(fn, delay = 100) {
    let lastTime = 0;
    return function(...args) {
        const now = Date.now();
        if (now - lastTime >= delay) {
            lastTime = now;
            fn.apply(this, args);
        }
    };
}

// ============================================
// 6. 增量渲染 - 虚拟列表
// ============================================

class VirtualList {
    constructor(options) {
        this.container = options.container;
        this.itemHeight = options.itemHeight || 80;
        this.bufferSize = options.bufferSize || 5;
        this.renderItem = options.renderItem;
        this.items = [];
        this.visibleStart = 0;
        this.visibleEnd = 0;
        
        this.wrapper = document.createElement('div');
        this.wrapper.style.cssText = 'position: relative; overflow-y: auto; height: 100%;';
        
        this.content = document.createElement('div');
        this.content.style.cssText = 'position: relative;';
        
        this.wrapper.appendChild(this.content);
        this.container.appendChild(this.wrapper);
        
        this.wrapper.addEventListener('scroll', throttle(() => this.onScroll(), 50));
    }

    setItems(items) {
        this.items = items;
        this.content.style.height = (items.length * this.itemHeight) + 'px';
        this.render();
    }

    onScroll() {
        const scrollTop = this.wrapper.scrollTop;
        const viewportHeight = this.wrapper.clientHeight;
        
        const newStart = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.bufferSize);
        const newEnd = Math.min(
            this.items.length,
            Math.ceil((scrollTop + viewportHeight) / this.itemHeight) + this.bufferSize
        );
        
        if (newStart !== this.visibleStart || newEnd !== this.visibleEnd) {
            this.visibleStart = newStart;
            this.visibleEnd = newEnd;
            this.render();
        }
    }

    render() {
        const fragment = document.createDocumentFragment();
        
        for (let i = this.visibleStart; i < this.visibleEnd; i++) {
            const item = this.items[i];
            if (!item) continue;
            
            const element = this.renderItem(item, i);
            if (typeof element === 'string') {
                const div = document.createElement('div');
                div.innerHTML = element;
                div.firstElementChild.style.position = 'absolute';
                div.firstElementChild.style.top = (i * this.itemHeight) + 'px';
                fragment.appendChild(div.firstElementChild);
            } else {
                element.style.position = 'absolute';
                element.style.top = (i * this.itemHeight) + 'px';
                fragment.appendChild(element);
            }
        }
        
        this.content.innerHTML = '';
        this.content.appendChild(fragment);
    }
}

// ============================================
// 7. 缓存计算结果
// ============================================

function memoize(fn) {
    const cache = new Map();
    return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            return cache.get(key);
        }
        const result = fn.apply(this, args);
        cache.set(key, result);
        return result;
    };
}

// ============================================
// 8. 批量更新 - 减少重绘
// ============================================

class BatchUpdater {
    constructor() {
        this.pending = false;
        this.updates = [];
    }

    add(updateFn) {
        this.updates.push(updateFn);
        if (!this.pending) {
            this.pending = true;
            requestAnimationFrame(() => this.flush());
        }
    }

    flush() {
        const updates = this.updates;
        this.updates = [];
        this.pending = false;
        
        updates.forEach(fn => fn());
    }
}

// ============================================
// 9. 模板缓存
// ============================================

const templateCache = new Map();

function createTemplate(id, template) {
    if (!templateCache.has(id)) {
        const element = document.createElement('template');
        element.innerHTML = template;
        templateCache.set(id, element);
    }
    return templateCache.get(id).content.cloneNode(true);
}

// ============================================
// 10. 性能监控
// ============================================

class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
    }

    start(name) {
        this.metrics.set(name, { start: performance.now() });
    }

    end(name) {
        const metric = this.metrics.get(name);
        if (metric) {
            metric.end = performance.now();
            metric.duration = metric.end - metric.start;
            console.log(`[Performance] ${name}: ${metric.duration.toFixed(2)}ms`);
            return metric.duration;
        }
        return 0;
    }

    measure(name, fn) {
        this.start(name);
        const result = fn();
        this.end(name);
        return result;
    }

    async measureAsync(name, fn) {
        this.start(name);
        const result = await fn();
        this.end(name);
        return result;
    }
}

// ============================================
// 导出
// ============================================

window.PerfUtils = {
    MatchDataManager,
    DOMCache,
    createDocumentFragment,
    batchRender,
    delegate,
    debounce,
    throttle,
    VirtualList,
    memoize,
    BatchUpdater,
    createTemplate,
    PerformanceMonitor
};