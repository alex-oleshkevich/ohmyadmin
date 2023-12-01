var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i6 = decorators.length - 1, decorator; i6 >= 0; i6--)
    if (decorator = decorators[i6])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result)
    __defProp(target, key, result);
  return result;
};

// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t5, e6, o7) {
    if (this._$cssResult$ = true, o7 !== s)
      throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t5, this.t = e6;
  }
  get styleSheet() {
    let t5 = this.o;
    const s4 = this.t;
    if (e && void 0 === t5) {
      const e6 = void 0 !== s4 && 1 === s4.length;
      e6 && (t5 = o.get(s4)), void 0 === t5 && ((this.o = t5 = new CSSStyleSheet()).replaceSync(this.cssText), e6 && o.set(s4, t5));
    }
    return t5;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t5) => new n("string" == typeof t5 ? t5 : t5 + "", void 0, s);
var S = (s4, o7) => {
  if (e)
    s4.adoptedStyleSheets = o7.map((t5) => t5 instanceof CSSStyleSheet ? t5 : t5.styleSheet);
  else
    for (const e6 of o7) {
      const o8 = document.createElement("style"), n6 = t.litNonce;
      void 0 !== n6 && o8.setAttribute("nonce", n6), o8.textContent = e6.cssText, s4.appendChild(o8);
    }
};
var c = e ? (t5) => t5 : (t5) => t5 instanceof CSSStyleSheet ? ((t6) => {
  let e6 = "";
  for (const s4 of t6.cssRules)
    e6 += s4.cssText;
  return r(e6);
})(t5) : t5;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: r2, getOwnPropertyNames: h, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t5, s4) => t5;
var u = { toAttribute(t5, s4) {
  switch (s4) {
    case Boolean:
      t5 = t5 ? l : null;
      break;
    case Object:
    case Array:
      t5 = null == t5 ? t5 : JSON.stringify(t5);
  }
  return t5;
}, fromAttribute(t5, s4) {
  let i6 = t5;
  switch (s4) {
    case Boolean:
      i6 = null !== t5;
      break;
    case Number:
      i6 = null === t5 ? null : Number(t5);
      break;
    case Object:
    case Array:
      try {
        i6 = JSON.parse(t5);
      } catch (t6) {
        i6 = null;
      }
  }
  return i6;
} };
var f = (t5, s4) => !i2(t5, s4);
var y = { attribute: true, type: String, converter: u, reflect: false, hasChanged: f };
Symbol.metadata ??= Symbol("metadata"), a.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var b = class extends HTMLElement {
  static addInitializer(t5) {
    this._$Ei(), (this.l ??= []).push(t5);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t5, s4 = y) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.elementProperties.set(t5, s4), !s4.noAccessor) {
      const i6 = Symbol(), r6 = this.getPropertyDescriptor(t5, i6, s4);
      void 0 !== r6 && e2(this.prototype, t5, r6);
    }
  }
  static getPropertyDescriptor(t5, s4, i6) {
    const { get: e6, set: h3 } = r2(this.prototype, t5) ?? { get() {
      return this[s4];
    }, set(t6) {
      this[s4] = t6;
    } };
    return { get() {
      return e6?.call(this);
    }, set(s5) {
      const r6 = e6?.call(this);
      h3.call(this, s5), this.requestUpdate(t5, r6, i6);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t5) {
    return this.elementProperties.get(t5) ?? y;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties")))
      return;
    const t5 = n2(this);
    t5.finalize(), void 0 !== t5.l && (this.l = [...t5.l]), this.elementProperties = new Map(t5.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized")))
      return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t6 = this.properties, s4 = [...h(t6), ...o2(t6)];
      for (const i6 of s4)
        this.createProperty(i6, t6[i6]);
    }
    const t5 = this[Symbol.metadata];
    if (null !== t5) {
      const s4 = litPropertyMetadata.get(t5);
      if (void 0 !== s4)
        for (const [t6, i6] of s4)
          this.elementProperties.set(t6, i6);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t6, s4] of this.elementProperties) {
      const i6 = this._$Eu(t6, s4);
      void 0 !== i6 && this._$Eh.set(i6, t6);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i6 = [];
    if (Array.isArray(s4)) {
      const e6 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e6)
        i6.unshift(c(s5));
    } else
      void 0 !== s4 && i6.push(c(s4));
    return i6;
  }
  static _$Eu(t5, s4) {
    const i6 = s4.attribute;
    return false === i6 ? void 0 : "string" == typeof i6 ? i6 : "string" == typeof t5 ? t5.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$Eg = new Promise((t5) => this.enableUpdating = t5), this._$AL = /* @__PURE__ */ new Map(), this._$ES(), this.requestUpdate(), this.constructor.l?.forEach((t5) => t5(this));
  }
  addController(t5) {
    (this._$E_ ??= /* @__PURE__ */ new Set()).add(t5), void 0 !== this.renderRoot && this.isConnected && t5.hostConnected?.();
  }
  removeController(t5) {
    this._$E_?.delete(t5);
  }
  _$ES() {
    const t5 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i6 of s4.keys())
      this.hasOwnProperty(i6) && (t5.set(i6, this[i6]), delete this[i6]);
    t5.size > 0 && (this._$Ep = t5);
  }
  createRenderRoot() {
    const t5 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t5, this.constructor.elementStyles), t5;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(true), this._$E_?.forEach((t5) => t5.hostConnected?.());
  }
  enableUpdating(t5) {
  }
  disconnectedCallback() {
    this._$E_?.forEach((t5) => t5.hostDisconnected?.());
  }
  attributeChangedCallback(t5, s4, i6) {
    this._$AK(t5, i6);
  }
  _$EO(t5, s4) {
    const i6 = this.constructor.elementProperties.get(t5), e6 = this.constructor._$Eu(t5, i6);
    if (void 0 !== e6 && true === i6.reflect) {
      const r6 = (void 0 !== i6.converter?.toAttribute ? i6.converter : u).toAttribute(s4, i6.type);
      this._$Em = t5, null == r6 ? this.removeAttribute(e6) : this.setAttribute(e6, r6), this._$Em = null;
    }
  }
  _$AK(t5, s4) {
    const i6 = this.constructor, e6 = i6._$Eh.get(t5);
    if (void 0 !== e6 && this._$Em !== e6) {
      const t6 = i6.getPropertyOptions(e6), r6 = "function" == typeof t6.converter ? { fromAttribute: t6.converter } : void 0 !== t6.converter?.fromAttribute ? t6.converter : u;
      this._$Em = e6, this[e6] = r6.fromAttribute(s4, t6.type), this._$Em = null;
    }
  }
  requestUpdate(t5, s4, i6, e6 = false, r6) {
    if (void 0 !== t5) {
      if (i6 ??= this.constructor.getPropertyOptions(t5), !(i6.hasChanged ?? f)(e6 ? r6 : this[t5], s4))
        return;
      this.C(t5, s4, i6);
    }
    false === this.isUpdatePending && (this._$Eg = this._$EP());
  }
  C(t5, s4, i6) {
    this._$AL.has(t5) || this._$AL.set(t5, s4), true === i6.reflect && this._$Em !== t5 && (this._$Ej ??= /* @__PURE__ */ new Set()).add(t5);
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$Eg;
    } catch (t6) {
      Promise.reject(t6);
    }
    const t5 = this.scheduleUpdate();
    return null != t5 && await t5, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending)
      return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [t7, s5] of this._$Ep)
          this[t7] = s5;
        this._$Ep = void 0;
      }
      const t6 = this.constructor.elementProperties;
      if (t6.size > 0)
        for (const [s5, i6] of t6)
          true !== i6.wrapped || this._$AL.has(s5) || void 0 === this[s5] || this.C(s5, this[s5], i6);
    }
    let t5 = false;
    const s4 = this._$AL;
    try {
      t5 = this.shouldUpdate(s4), t5 ? (this.willUpdate(s4), this._$E_?.forEach((t6) => t6.hostUpdate?.()), this.update(s4)) : this._$ET();
    } catch (s5) {
      throw t5 = false, this._$ET(), s5;
    }
    t5 && this._$AE(s4);
  }
  willUpdate(t5) {
  }
  _$AE(t5) {
    this._$E_?.forEach((t6) => t6.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t5)), this.updated(t5);
  }
  _$ET() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$Eg;
  }
  shouldUpdate(t5) {
    return true;
  }
  update(t5) {
    this._$Ej &&= this._$Ej.forEach((t6) => this._$EO(t6, this[t6])), this._$ET();
  }
  updated(t5) {
  }
  firstUpdated(t5) {
  }
};
b.elementStyles = [], b.shadowRootOptions = { mode: "open" }, b[d("elementProperties")] = /* @__PURE__ */ new Map(), b[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: b }), (a.reactiveElementVersions ??= []).push("2.0.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = t2.trustedTypes;
var s2 = i3 ? i3.createPolicy("lit-html", { createHTML: (t5) => t5 }) : void 0;
var e3 = "$lit$";
var h2 = `lit$${(Math.random() + "").slice(9)}$`;
var o3 = "?" + h2;
var n3 = `<${o3}>`;
var r3 = document;
var l2 = () => r3.createComment("");
var c3 = (t5) => null === t5 || "object" != typeof t5 && "function" != typeof t5;
var a2 = Array.isArray;
var u2 = (t5) => a2(t5) || "function" == typeof t5?.[Symbol.iterator];
var d2 = "[ 	\n\f\r]";
var f2 = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var v = /-->/g;
var _ = />/g;
var m = RegExp(`>|${d2}(?:([^\\s"'>=/]+)(${d2}*=${d2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var p2 = /'/g;
var g = /"/g;
var $ = /^(?:script|style|textarea|title)$/i;
var y2 = (t5) => (i6, ...s4) => ({ _$litType$: t5, strings: i6, values: s4 });
var x = y2(1);
var b2 = y2(2);
var w = Symbol.for("lit-noChange");
var T = Symbol.for("lit-nothing");
var A = /* @__PURE__ */ new WeakMap();
var E = r3.createTreeWalker(r3, 129);
function C(t5, i6) {
  if (!Array.isArray(t5) || !t5.hasOwnProperty("raw"))
    throw Error("invalid template strings array");
  return void 0 !== s2 ? s2.createHTML(i6) : i6;
}
var P = (t5, i6) => {
  const s4 = t5.length - 1, o7 = [];
  let r6, l3 = 2 === i6 ? "<svg>" : "", c4 = f2;
  for (let i7 = 0; i7 < s4; i7++) {
    const s5 = t5[i7];
    let a3, u3, d3 = -1, y3 = 0;
    for (; y3 < s5.length && (c4.lastIndex = y3, u3 = c4.exec(s5), null !== u3); )
      y3 = c4.lastIndex, c4 === f2 ? "!--" === u3[1] ? c4 = v : void 0 !== u3[1] ? c4 = _ : void 0 !== u3[2] ? ($.test(u3[2]) && (r6 = RegExp("</" + u3[2], "g")), c4 = m) : void 0 !== u3[3] && (c4 = m) : c4 === m ? ">" === u3[0] ? (c4 = r6 ?? f2, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? m : '"' === u3[3] ? g : p2) : c4 === g || c4 === p2 ? c4 = m : c4 === v || c4 === _ ? c4 = f2 : (c4 = m, r6 = void 0);
    const x2 = c4 === m && t5[i7 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === f2 ? s5 + n3 : d3 >= 0 ? (o7.push(a3), s5.slice(0, d3) + e3 + s5.slice(d3) + h2 + x2) : s5 + h2 + (-2 === d3 ? i7 : x2);
  }
  return [C(t5, l3 + (t5[s4] || "<?>") + (2 === i6 ? "</svg>" : "")), o7];
};
var V = class _V {
  constructor({ strings: t5, _$litType$: s4 }, n6) {
    let r6;
    this.parts = [];
    let c4 = 0, a3 = 0;
    const u3 = t5.length - 1, d3 = this.parts, [f3, v2] = P(t5, s4);
    if (this.el = _V.createElement(f3, n6), E.currentNode = this.el.content, 2 === s4) {
      const t6 = this.el.content.firstChild;
      t6.replaceWith(...t6.childNodes);
    }
    for (; null !== (r6 = E.nextNode()) && d3.length < u3; ) {
      if (1 === r6.nodeType) {
        if (r6.hasAttributes())
          for (const t6 of r6.getAttributeNames())
            if (t6.endsWith(e3)) {
              const i6 = v2[a3++], s5 = r6.getAttribute(t6).split(h2), e6 = /([.?@])?(.*)/.exec(i6);
              d3.push({ type: 1, index: c4, name: e6[2], strings: s5, ctor: "." === e6[1] ? k : "?" === e6[1] ? H : "@" === e6[1] ? I : R }), r6.removeAttribute(t6);
            } else
              t6.startsWith(h2) && (d3.push({ type: 6, index: c4 }), r6.removeAttribute(t6));
        if ($.test(r6.tagName)) {
          const t6 = r6.textContent.split(h2), s5 = t6.length - 1;
          if (s5 > 0) {
            r6.textContent = i3 ? i3.emptyScript : "";
            for (let i6 = 0; i6 < s5; i6++)
              r6.append(t6[i6], l2()), E.nextNode(), d3.push({ type: 2, index: ++c4 });
            r6.append(t6[s5], l2());
          }
        }
      } else if (8 === r6.nodeType)
        if (r6.data === o3)
          d3.push({ type: 2, index: c4 });
        else {
          let t6 = -1;
          for (; -1 !== (t6 = r6.data.indexOf(h2, t6 + 1)); )
            d3.push({ type: 7, index: c4 }), t6 += h2.length - 1;
        }
      c4++;
    }
  }
  static createElement(t5, i6) {
    const s4 = r3.createElement("template");
    return s4.innerHTML = t5, s4;
  }
};
function N(t5, i6, s4 = t5, e6) {
  if (i6 === w)
    return i6;
  let h3 = void 0 !== e6 ? s4._$Co?.[e6] : s4._$Cl;
  const o7 = c3(i6) ? void 0 : i6._$litDirective$;
  return h3?.constructor !== o7 && (h3?._$AO?.(false), void 0 === o7 ? h3 = void 0 : (h3 = new o7(t5), h3._$AT(t5, s4, e6)), void 0 !== e6 ? (s4._$Co ??= [])[e6] = h3 : s4._$Cl = h3), void 0 !== h3 && (i6 = N(t5, h3._$AS(t5, i6.values), h3, e6)), i6;
}
var S2 = class {
  constructor(t5, i6) {
    this._$AV = [], this._$AN = void 0, this._$AD = t5, this._$AM = i6;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t5) {
    const { el: { content: i6 }, parts: s4 } = this._$AD, e6 = (t5?.creationScope ?? r3).importNode(i6, true);
    E.currentNode = e6;
    let h3 = E.nextNode(), o7 = 0, n6 = 0, l3 = s4[0];
    for (; void 0 !== l3; ) {
      if (o7 === l3.index) {
        let i7;
        2 === l3.type ? i7 = new M(h3, h3.nextSibling, this, t5) : 1 === l3.type ? i7 = new l3.ctor(h3, l3.name, l3.strings, this, t5) : 6 === l3.type && (i7 = new L(h3, this, t5)), this._$AV.push(i7), l3 = s4[++n6];
      }
      o7 !== l3?.index && (h3 = E.nextNode(), o7++);
    }
    return E.currentNode = r3, e6;
  }
  p(t5) {
    let i6 = 0;
    for (const s4 of this._$AV)
      void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t5, s4, i6), i6 += s4.strings.length - 2) : s4._$AI(t5[i6])), i6++;
  }
};
var M = class _M {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t5, i6, s4, e6) {
    this.type = 2, this._$AH = T, this._$AN = void 0, this._$AA = t5, this._$AB = i6, this._$AM = s4, this.options = e6, this._$Cv = e6?.isConnected ?? true;
  }
  get parentNode() {
    let t5 = this._$AA.parentNode;
    const i6 = this._$AM;
    return void 0 !== i6 && 11 === t5?.nodeType && (t5 = i6.parentNode), t5;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t5, i6 = this) {
    t5 = N(this, t5, i6), c3(t5) ? t5 === T || null == t5 || "" === t5 ? (this._$AH !== T && this._$AR(), this._$AH = T) : t5 !== this._$AH && t5 !== w && this._(t5) : void 0 !== t5._$litType$ ? this.g(t5) : void 0 !== t5.nodeType ? this.$(t5) : u2(t5) ? this.T(t5) : this._(t5);
  }
  k(t5) {
    return this._$AA.parentNode.insertBefore(t5, this._$AB);
  }
  $(t5) {
    this._$AH !== t5 && (this._$AR(), this._$AH = this.k(t5));
  }
  _(t5) {
    this._$AH !== T && c3(this._$AH) ? this._$AA.nextSibling.data = t5 : this.$(r3.createTextNode(t5)), this._$AH = t5;
  }
  g(t5) {
    const { values: i6, _$litType$: s4 } = t5, e6 = "number" == typeof s4 ? this._$AC(t5) : (void 0 === s4.el && (s4.el = V.createElement(C(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e6)
      this._$AH.p(i6);
    else {
      const t6 = new S2(e6, this), s5 = t6.u(this.options);
      t6.p(i6), this.$(s5), this._$AH = t6;
    }
  }
  _$AC(t5) {
    let i6 = A.get(t5.strings);
    return void 0 === i6 && A.set(t5.strings, i6 = new V(t5)), i6;
  }
  T(t5) {
    a2(this._$AH) || (this._$AH = [], this._$AR());
    const i6 = this._$AH;
    let s4, e6 = 0;
    for (const h3 of t5)
      e6 === i6.length ? i6.push(s4 = new _M(this.k(l2()), this.k(l2()), this, this.options)) : s4 = i6[e6], s4._$AI(h3), e6++;
    e6 < i6.length && (this._$AR(s4 && s4._$AB.nextSibling, e6), i6.length = e6);
  }
  _$AR(t5 = this._$AA.nextSibling, i6) {
    for (this._$AP?.(false, true, i6); t5 && t5 !== this._$AB; ) {
      const i7 = t5.nextSibling;
      t5.remove(), t5 = i7;
    }
  }
  setConnected(t5) {
    void 0 === this._$AM && (this._$Cv = t5, this._$AP?.(t5));
  }
};
var R = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t5, i6, s4, e6, h3) {
    this.type = 1, this._$AH = T, this._$AN = void 0, this.element = t5, this.name = i6, this._$AM = e6, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = T;
  }
  _$AI(t5, i6 = this, s4, e6) {
    const h3 = this.strings;
    let o7 = false;
    if (void 0 === h3)
      t5 = N(this, t5, i6, 0), o7 = !c3(t5) || t5 !== this._$AH && t5 !== w, o7 && (this._$AH = t5);
    else {
      const e7 = t5;
      let n6, r6;
      for (t5 = h3[0], n6 = 0; n6 < h3.length - 1; n6++)
        r6 = N(this, e7[s4 + n6], i6, n6), r6 === w && (r6 = this._$AH[n6]), o7 ||= !c3(r6) || r6 !== this._$AH[n6], r6 === T ? t5 = T : t5 !== T && (t5 += (r6 ?? "") + h3[n6 + 1]), this._$AH[n6] = r6;
    }
    o7 && !e6 && this.O(t5);
  }
  O(t5) {
    t5 === T ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t5 ?? "");
  }
};
var k = class extends R {
  constructor() {
    super(...arguments), this.type = 3;
  }
  O(t5) {
    this.element[this.name] = t5 === T ? void 0 : t5;
  }
};
var H = class extends R {
  constructor() {
    super(...arguments), this.type = 4;
  }
  O(t5) {
    this.element.toggleAttribute(this.name, !!t5 && t5 !== T);
  }
};
var I = class extends R {
  constructor(t5, i6, s4, e6, h3) {
    super(t5, i6, s4, e6, h3), this.type = 5;
  }
  _$AI(t5, i6 = this) {
    if ((t5 = N(this, t5, i6, 0) ?? T) === w)
      return;
    const s4 = this._$AH, e6 = t5 === T && s4 !== T || t5.capture !== s4.capture || t5.once !== s4.once || t5.passive !== s4.passive, h3 = t5 !== T && (s4 === T || e6);
    e6 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t5), this._$AH = t5;
  }
  handleEvent(t5) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t5) : this._$AH.handleEvent(t5);
  }
};
var L = class {
  constructor(t5, i6, s4) {
    this.element = t5, this.type = 6, this._$AN = void 0, this._$AM = i6, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t5) {
    N(this, t5);
  }
};
var Z = t2.litHtmlPolyfillSupport;
Z?.(V, M), (t2.litHtmlVersions ??= []).push("3.1.0");
var j = (t5, i6, s4) => {
  const e6 = s4?.renderBefore ?? i6;
  let h3 = e6._$litPart$;
  if (void 0 === h3) {
    const t6 = s4?.renderBefore ?? null;
    e6._$litPart$ = h3 = new M(i6.insertBefore(l2(), t6), t6, void 0, s4 ?? {});
  }
  return h3._$AI(t5), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = class extends b {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t5 = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t5.firstChild, t5;
  }
  update(t5) {
    const i6 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t5), this._$Do = j(i6, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(true);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(false);
  }
  render() {
    return w;
  }
};
s3._$litElement$ = true, s3["finalized", "finalized"] = true, globalThis.litElementHydrateSupport?.({ LitElement: s3 });
var r4 = globalThis.litElementPolyfillSupport;
r4?.({ LitElement: s3 });
(globalThis.litElementVersions ??= []).push("4.0.2");

// node_modules/@lit/reactive-element/decorators/custom-element.js
var t3 = (t5) => (e6, o7) => {
  void 0 !== o7 ? o7.addInitializer(() => {
    customElements.define(t5, e6);
  }) : customElements.define(t5, e6);
};

// node_modules/@lit/reactive-element/decorators/property.js
var o4 = { attribute: true, type: String, converter: u, reflect: false, hasChanged: f };
var r5 = (t5 = o4, e6, r6) => {
  const { kind: n6, metadata: i6 } = r6;
  let s4 = globalThis.litPropertyMetadata.get(i6);
  if (void 0 === s4 && globalThis.litPropertyMetadata.set(i6, s4 = /* @__PURE__ */ new Map()), s4.set(r6.name, t5), "accessor" === n6) {
    const { name: o7 } = r6;
    return { set(r7) {
      const n7 = e6.get.call(this);
      e6.set.call(this, r7), this.requestUpdate(o7, n7, t5);
    }, init(e7) {
      return void 0 !== e7 && this.C(o7, void 0, t5), e7;
    } };
  }
  if ("setter" === n6) {
    const { name: o7 } = r6;
    return function(r7) {
      const n7 = this[o7];
      e6.call(this, r7), this.requestUpdate(o7, n7, t5);
    };
  }
  throw Error("Unsupported decorator location: " + n6);
};
function n4(t5) {
  return (e6, o7) => "object" == typeof o7 ? r5(t5, e6, o7) : ((t6, e7, o8) => {
    const r6 = e7.hasOwnProperty(o8);
    return e7.constructor.createProperty(o8, r6 ? { ...t6, wrapped: true } : t6), r6 ? Object.getOwnPropertyDescriptor(e7, o8) : void 0;
  })(t5, e6, o7);
}

// node_modules/@lit/reactive-element/decorators/base.js
var e4 = (e6, t5, c4) => (c4.configurable = true, c4.enumerable = true, Reflect.decorate && "object" != typeof t5 && Object.defineProperty(e6, t5, c4), c4);

// node_modules/@lit/reactive-element/decorators/query-assigned-elements.js
function o5(o7) {
  return (e6, n6) => {
    const { slot: r6, selector: s4 } = o7 ?? {}, c4 = "slot" + (r6 ? `[name=${r6}]` : ":not([name])");
    return e4(e6, n6, { get() {
      const t5 = this.renderRoot?.querySelector(c4), e7 = t5?.assignedElements(o7) ?? [];
      return void 0 === s4 ? e7 : e7.filter((t6) => t6.matches(s4));
    } });
  };
}

// node_modules/lit-html/directive.js
var t4 = { ATTRIBUTE: 1, CHILD: 2, PROPERTY: 3, BOOLEAN_ATTRIBUTE: 4, EVENT: 5, ELEMENT: 6 };
var e5 = (t5) => (...e6) => ({ _$litDirective$: t5, values: e6 });
var i4 = class {
  constructor(t5) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(t5, e6, i6) {
    this._$Ct = t5, this._$AM = e6, this._$Ci = i6;
  }
  _$AS(t5, e6) {
    return this.update(t5, e6);
  }
  update(t5, e6) {
    return this.render(...e6);
  }
};

// node_modules/lit-html/directives/style-map.js
var n5 = "important";
var i5 = " !" + n5;
var o6 = e5(class extends i4 {
  constructor(t5) {
    if (super(t5), t5.type !== t4.ATTRIBUTE || "style" !== t5.name || t5.strings?.length > 2)
      throw Error("The `styleMap` directive must be used in the `style` attribute and must be the only part in the attribute.");
  }
  render(t5) {
    return Object.keys(t5).reduce((e6, r6) => {
      const s4 = t5[r6];
      return null == s4 ? e6 : e6 + `${r6 = r6.includes("-") ? r6 : r6.replace(/(?:^(webkit|moz|ms|o)|)(?=[A-Z])/g, "-$&").toLowerCase()}:${s4};`;
    }, "");
  }
  update(e6, [r6]) {
    const { style: s4 } = e6.element;
    if (void 0 === this.ut)
      return this.ut = new Set(Object.keys(r6)), this.render(r6);
    for (const t5 of this.ut)
      null == r6[t5] && (this.ut.delete(t5), t5.includes("-") ? s4.removeProperty(t5) : s4[t5] = null);
    for (const t5 in r6) {
      const e7 = r6[t5];
      if (null != e7) {
        this.ut.add(t5);
        const r7 = "string" == typeof e7 && e7.endsWith(i5);
        t5.includes("-") || r7 ? s4.setProperty(t5, r7 ? e7.slice(0, -11) : e7, r7 ? n5 : "") : s4[t5] = e7;
      }
    }
    return w;
  }
});

// node_modules/@floating-ui/utils/dist/floating-ui.utils.mjs
var min = Math.min;
var max = Math.max;
var round = Math.round;
var floor = Math.floor;
var createCoords = (v2) => ({
  x: v2,
  y: v2
});
function evaluate(value, param) {
  return typeof value === "function" ? value(param) : value;
}
function getSide(placement) {
  return placement.split("-")[0];
}
function getAlignment(placement) {
  return placement.split("-")[1];
}
function getOppositeAxis(axis) {
  return axis === "x" ? "y" : "x";
}
function getAxisLength(axis) {
  return axis === "y" ? "height" : "width";
}
function getSideAxis(placement) {
  return ["top", "bottom"].includes(getSide(placement)) ? "y" : "x";
}
function getAlignmentAxis(placement) {
  return getOppositeAxis(getSideAxis(placement));
}
function rectToClientRect(rect) {
  return {
    ...rect,
    top: rect.y,
    left: rect.x,
    right: rect.x + rect.width,
    bottom: rect.y + rect.height
  };
}

// node_modules/@floating-ui/core/dist/floating-ui.core.mjs
function computeCoordsFromPlacement(_ref, placement, rtl) {
  let {
    reference,
    floating
  } = _ref;
  const sideAxis = getSideAxis(placement);
  const alignmentAxis = getAlignmentAxis(placement);
  const alignLength = getAxisLength(alignmentAxis);
  const side = getSide(placement);
  const isVertical = sideAxis === "y";
  const commonX = reference.x + reference.width / 2 - floating.width / 2;
  const commonY = reference.y + reference.height / 2 - floating.height / 2;
  const commonAlign = reference[alignLength] / 2 - floating[alignLength] / 2;
  let coords;
  switch (side) {
    case "top":
      coords = {
        x: commonX,
        y: reference.y - floating.height
      };
      break;
    case "bottom":
      coords = {
        x: commonX,
        y: reference.y + reference.height
      };
      break;
    case "right":
      coords = {
        x: reference.x + reference.width,
        y: commonY
      };
      break;
    case "left":
      coords = {
        x: reference.x - floating.width,
        y: commonY
      };
      break;
    default:
      coords = {
        x: reference.x,
        y: reference.y
      };
  }
  switch (getAlignment(placement)) {
    case "start":
      coords[alignmentAxis] -= commonAlign * (rtl && isVertical ? -1 : 1);
      break;
    case "end":
      coords[alignmentAxis] += commonAlign * (rtl && isVertical ? -1 : 1);
      break;
  }
  return coords;
}
var computePosition = async (reference, floating, config) => {
  const {
    placement = "bottom",
    strategy = "absolute",
    middleware = [],
    platform: platform2
  } = config;
  const validMiddleware = middleware.filter(Boolean);
  const rtl = await (platform2.isRTL == null ? void 0 : platform2.isRTL(floating));
  let rects = await platform2.getElementRects({
    reference,
    floating,
    strategy
  });
  let {
    x: x2,
    y: y3
  } = computeCoordsFromPlacement(rects, placement, rtl);
  let statefulPlacement = placement;
  let middlewareData = {};
  let resetCount = 0;
  for (let i6 = 0; i6 < validMiddleware.length; i6++) {
    const {
      name,
      fn
    } = validMiddleware[i6];
    const {
      x: nextX,
      y: nextY,
      data,
      reset
    } = await fn({
      x: x2,
      y: y3,
      initialPlacement: placement,
      placement: statefulPlacement,
      strategy,
      middlewareData,
      rects,
      platform: platform2,
      elements: {
        reference,
        floating
      }
    });
    x2 = nextX != null ? nextX : x2;
    y3 = nextY != null ? nextY : y3;
    middlewareData = {
      ...middlewareData,
      [name]: {
        ...middlewareData[name],
        ...data
      }
    };
    if (reset && resetCount <= 50) {
      resetCount++;
      if (typeof reset === "object") {
        if (reset.placement) {
          statefulPlacement = reset.placement;
        }
        if (reset.rects) {
          rects = reset.rects === true ? await platform2.getElementRects({
            reference,
            floating,
            strategy
          }) : reset.rects;
        }
        ({
          x: x2,
          y: y3
        } = computeCoordsFromPlacement(rects, statefulPlacement, rtl));
      }
      i6 = -1;
      continue;
    }
  }
  return {
    x: x2,
    y: y3,
    placement: statefulPlacement,
    strategy,
    middlewareData
  };
};
async function convertValueToCoords(state, options) {
  const {
    placement,
    platform: platform2,
    elements
  } = state;
  const rtl = await (platform2.isRTL == null ? void 0 : platform2.isRTL(elements.floating));
  const side = getSide(placement);
  const alignment = getAlignment(placement);
  const isVertical = getSideAxis(placement) === "y";
  const mainAxisMulti = ["left", "top"].includes(side) ? -1 : 1;
  const crossAxisMulti = rtl && isVertical ? -1 : 1;
  const rawValue = evaluate(options, state);
  let {
    mainAxis,
    crossAxis,
    alignmentAxis
  } = typeof rawValue === "number" ? {
    mainAxis: rawValue,
    crossAxis: 0,
    alignmentAxis: null
  } : {
    mainAxis: 0,
    crossAxis: 0,
    alignmentAxis: null,
    ...rawValue
  };
  if (alignment && typeof alignmentAxis === "number") {
    crossAxis = alignment === "end" ? alignmentAxis * -1 : alignmentAxis;
  }
  return isVertical ? {
    x: crossAxis * crossAxisMulti,
    y: mainAxis * mainAxisMulti
  } : {
    x: mainAxis * mainAxisMulti,
    y: crossAxis * crossAxisMulti
  };
}
var offset = function(options) {
  if (options === void 0) {
    options = 0;
  }
  return {
    name: "offset",
    options,
    async fn(state) {
      var _middlewareData$offse, _middlewareData$arrow;
      const {
        x: x2,
        y: y3,
        placement,
        middlewareData
      } = state;
      const diffCoords = await convertValueToCoords(state, options);
      if (placement === ((_middlewareData$offse = middlewareData.offset) == null ? void 0 : _middlewareData$offse.placement) && (_middlewareData$arrow = middlewareData.arrow) != null && _middlewareData$arrow.alignmentOffset) {
        return {};
      }
      return {
        x: x2 + diffCoords.x,
        y: y3 + diffCoords.y,
        data: {
          ...diffCoords,
          placement
        }
      };
    }
  };
};

// node_modules/@floating-ui/utils/dom/dist/floating-ui.utils.dom.mjs
function getNodeName(node) {
  if (isNode(node)) {
    return (node.nodeName || "").toLowerCase();
  }
  return "#document";
}
function getWindow(node) {
  var _node$ownerDocument;
  return (node == null ? void 0 : (_node$ownerDocument = node.ownerDocument) == null ? void 0 : _node$ownerDocument.defaultView) || window;
}
function getDocumentElement(node) {
  var _ref;
  return (_ref = (isNode(node) ? node.ownerDocument : node.document) || window.document) == null ? void 0 : _ref.documentElement;
}
function isNode(value) {
  return value instanceof Node || value instanceof getWindow(value).Node;
}
function isElement(value) {
  return value instanceof Element || value instanceof getWindow(value).Element;
}
function isHTMLElement(value) {
  return value instanceof HTMLElement || value instanceof getWindow(value).HTMLElement;
}
function isShadowRoot(value) {
  if (typeof ShadowRoot === "undefined") {
    return false;
  }
  return value instanceof ShadowRoot || value instanceof getWindow(value).ShadowRoot;
}
function isOverflowElement(element) {
  const {
    overflow,
    overflowX,
    overflowY,
    display
  } = getComputedStyle(element);
  return /auto|scroll|overlay|hidden|clip/.test(overflow + overflowY + overflowX) && !["inline", "contents"].includes(display);
}
function isTableElement(element) {
  return ["table", "td", "th"].includes(getNodeName(element));
}
function isContainingBlock(element) {
  const webkit = isWebKit();
  const css = getComputedStyle(element);
  return css.transform !== "none" || css.perspective !== "none" || (css.containerType ? css.containerType !== "normal" : false) || !webkit && (css.backdropFilter ? css.backdropFilter !== "none" : false) || !webkit && (css.filter ? css.filter !== "none" : false) || ["transform", "perspective", "filter"].some((value) => (css.willChange || "").includes(value)) || ["paint", "layout", "strict", "content"].some((value) => (css.contain || "").includes(value));
}
function getContainingBlock(element) {
  let currentNode = getParentNode(element);
  while (isHTMLElement(currentNode) && !isLastTraversableNode(currentNode)) {
    if (isContainingBlock(currentNode)) {
      return currentNode;
    } else {
      currentNode = getParentNode(currentNode);
    }
  }
  return null;
}
function isWebKit() {
  if (typeof CSS === "undefined" || !CSS.supports)
    return false;
  return CSS.supports("-webkit-backdrop-filter", "none");
}
function isLastTraversableNode(node) {
  return ["html", "body", "#document"].includes(getNodeName(node));
}
function getComputedStyle(element) {
  return getWindow(element).getComputedStyle(element);
}
function getNodeScroll(element) {
  if (isElement(element)) {
    return {
      scrollLeft: element.scrollLeft,
      scrollTop: element.scrollTop
    };
  }
  return {
    scrollLeft: element.pageXOffset,
    scrollTop: element.pageYOffset
  };
}
function getParentNode(node) {
  if (getNodeName(node) === "html") {
    return node;
  }
  const result = (
    // Step into the shadow DOM of the parent of a slotted node.
    node.assignedSlot || // DOM Element detected.
    node.parentNode || // ShadowRoot detected.
    isShadowRoot(node) && node.host || // Fallback.
    getDocumentElement(node)
  );
  return isShadowRoot(result) ? result.host : result;
}
function getNearestOverflowAncestor(node) {
  const parentNode = getParentNode(node);
  if (isLastTraversableNode(parentNode)) {
    return node.ownerDocument ? node.ownerDocument.body : node.body;
  }
  if (isHTMLElement(parentNode) && isOverflowElement(parentNode)) {
    return parentNode;
  }
  return getNearestOverflowAncestor(parentNode);
}
function getOverflowAncestors(node, list, traverseIframes) {
  var _node$ownerDocument2;
  if (list === void 0) {
    list = [];
  }
  if (traverseIframes === void 0) {
    traverseIframes = true;
  }
  const scrollableAncestor = getNearestOverflowAncestor(node);
  const isBody = scrollableAncestor === ((_node$ownerDocument2 = node.ownerDocument) == null ? void 0 : _node$ownerDocument2.body);
  const win = getWindow(scrollableAncestor);
  if (isBody) {
    return list.concat(win, win.visualViewport || [], isOverflowElement(scrollableAncestor) ? scrollableAncestor : [], win.frameElement && traverseIframes ? getOverflowAncestors(win.frameElement) : []);
  }
  return list.concat(scrollableAncestor, getOverflowAncestors(scrollableAncestor, [], traverseIframes));
}

// node_modules/@floating-ui/dom/dist/floating-ui.dom.mjs
function getCssDimensions(element) {
  const css = getComputedStyle(element);
  let width = parseFloat(css.width) || 0;
  let height = parseFloat(css.height) || 0;
  const hasOffset = isHTMLElement(element);
  const offsetWidth = hasOffset ? element.offsetWidth : width;
  const offsetHeight = hasOffset ? element.offsetHeight : height;
  const shouldFallback = round(width) !== offsetWidth || round(height) !== offsetHeight;
  if (shouldFallback) {
    width = offsetWidth;
    height = offsetHeight;
  }
  return {
    width,
    height,
    $: shouldFallback
  };
}
function unwrapElement(element) {
  return !isElement(element) ? element.contextElement : element;
}
function getScale(element) {
  const domElement = unwrapElement(element);
  if (!isHTMLElement(domElement)) {
    return createCoords(1);
  }
  const rect = domElement.getBoundingClientRect();
  const {
    width,
    height,
    $: $2
  } = getCssDimensions(domElement);
  let x2 = ($2 ? round(rect.width) : rect.width) / width;
  let y3 = ($2 ? round(rect.height) : rect.height) / height;
  if (!x2 || !Number.isFinite(x2)) {
    x2 = 1;
  }
  if (!y3 || !Number.isFinite(y3)) {
    y3 = 1;
  }
  return {
    x: x2,
    y: y3
  };
}
var noOffsets = /* @__PURE__ */ createCoords(0);
function getVisualOffsets(element) {
  const win = getWindow(element);
  if (!isWebKit() || !win.visualViewport) {
    return noOffsets;
  }
  return {
    x: win.visualViewport.offsetLeft,
    y: win.visualViewport.offsetTop
  };
}
function shouldAddVisualOffsets(element, isFixed, floatingOffsetParent) {
  if (isFixed === void 0) {
    isFixed = false;
  }
  if (!floatingOffsetParent || isFixed && floatingOffsetParent !== getWindow(element)) {
    return false;
  }
  return isFixed;
}
function getBoundingClientRect(element, includeScale, isFixedStrategy, offsetParent) {
  if (includeScale === void 0) {
    includeScale = false;
  }
  if (isFixedStrategy === void 0) {
    isFixedStrategy = false;
  }
  const clientRect = element.getBoundingClientRect();
  const domElement = unwrapElement(element);
  let scale = createCoords(1);
  if (includeScale) {
    if (offsetParent) {
      if (isElement(offsetParent)) {
        scale = getScale(offsetParent);
      }
    } else {
      scale = getScale(element);
    }
  }
  const visualOffsets = shouldAddVisualOffsets(domElement, isFixedStrategy, offsetParent) ? getVisualOffsets(domElement) : createCoords(0);
  let x2 = (clientRect.left + visualOffsets.x) / scale.x;
  let y3 = (clientRect.top + visualOffsets.y) / scale.y;
  let width = clientRect.width / scale.x;
  let height = clientRect.height / scale.y;
  if (domElement) {
    const win = getWindow(domElement);
    const offsetWin = offsetParent && isElement(offsetParent) ? getWindow(offsetParent) : offsetParent;
    let currentIFrame = win.frameElement;
    while (currentIFrame && offsetParent && offsetWin !== win) {
      const iframeScale = getScale(currentIFrame);
      const iframeRect = currentIFrame.getBoundingClientRect();
      const css = getComputedStyle(currentIFrame);
      const left = iframeRect.left + (currentIFrame.clientLeft + parseFloat(css.paddingLeft)) * iframeScale.x;
      const top = iframeRect.top + (currentIFrame.clientTop + parseFloat(css.paddingTop)) * iframeScale.y;
      x2 *= iframeScale.x;
      y3 *= iframeScale.y;
      width *= iframeScale.x;
      height *= iframeScale.y;
      x2 += left;
      y3 += top;
      currentIFrame = getWindow(currentIFrame).frameElement;
    }
  }
  return rectToClientRect({
    width,
    height,
    x: x2,
    y: y3
  });
}
function convertOffsetParentRelativeRectToViewportRelativeRect(_ref) {
  let {
    rect,
    offsetParent,
    strategy
  } = _ref;
  const isOffsetParentAnElement = isHTMLElement(offsetParent);
  const documentElement = getDocumentElement(offsetParent);
  if (offsetParent === documentElement) {
    return rect;
  }
  let scroll = {
    scrollLeft: 0,
    scrollTop: 0
  };
  let scale = createCoords(1);
  const offsets = createCoords(0);
  if (isOffsetParentAnElement || !isOffsetParentAnElement && strategy !== "fixed") {
    if (getNodeName(offsetParent) !== "body" || isOverflowElement(documentElement)) {
      scroll = getNodeScroll(offsetParent);
    }
    if (isHTMLElement(offsetParent)) {
      const offsetRect = getBoundingClientRect(offsetParent);
      scale = getScale(offsetParent);
      offsets.x = offsetRect.x + offsetParent.clientLeft;
      offsets.y = offsetRect.y + offsetParent.clientTop;
    }
  }
  return {
    width: rect.width * scale.x,
    height: rect.height * scale.y,
    x: rect.x * scale.x - scroll.scrollLeft * scale.x + offsets.x,
    y: rect.y * scale.y - scroll.scrollTop * scale.y + offsets.y
  };
}
function getClientRects(element) {
  return Array.from(element.getClientRects());
}
function getWindowScrollBarX(element) {
  return getBoundingClientRect(getDocumentElement(element)).left + getNodeScroll(element).scrollLeft;
}
function getDocumentRect(element) {
  const html = getDocumentElement(element);
  const scroll = getNodeScroll(element);
  const body = element.ownerDocument.body;
  const width = max(html.scrollWidth, html.clientWidth, body.scrollWidth, body.clientWidth);
  const height = max(html.scrollHeight, html.clientHeight, body.scrollHeight, body.clientHeight);
  let x2 = -scroll.scrollLeft + getWindowScrollBarX(element);
  const y3 = -scroll.scrollTop;
  if (getComputedStyle(body).direction === "rtl") {
    x2 += max(html.clientWidth, body.clientWidth) - width;
  }
  return {
    width,
    height,
    x: x2,
    y: y3
  };
}
function getViewportRect(element, strategy) {
  const win = getWindow(element);
  const html = getDocumentElement(element);
  const visualViewport = win.visualViewport;
  let width = html.clientWidth;
  let height = html.clientHeight;
  let x2 = 0;
  let y3 = 0;
  if (visualViewport) {
    width = visualViewport.width;
    height = visualViewport.height;
    const visualViewportBased = isWebKit();
    if (!visualViewportBased || visualViewportBased && strategy === "fixed") {
      x2 = visualViewport.offsetLeft;
      y3 = visualViewport.offsetTop;
    }
  }
  return {
    width,
    height,
    x: x2,
    y: y3
  };
}
function getInnerBoundingClientRect(element, strategy) {
  const clientRect = getBoundingClientRect(element, true, strategy === "fixed");
  const top = clientRect.top + element.clientTop;
  const left = clientRect.left + element.clientLeft;
  const scale = isHTMLElement(element) ? getScale(element) : createCoords(1);
  const width = element.clientWidth * scale.x;
  const height = element.clientHeight * scale.y;
  const x2 = left * scale.x;
  const y3 = top * scale.y;
  return {
    width,
    height,
    x: x2,
    y: y3
  };
}
function getClientRectFromClippingAncestor(element, clippingAncestor, strategy) {
  let rect;
  if (clippingAncestor === "viewport") {
    rect = getViewportRect(element, strategy);
  } else if (clippingAncestor === "document") {
    rect = getDocumentRect(getDocumentElement(element));
  } else if (isElement(clippingAncestor)) {
    rect = getInnerBoundingClientRect(clippingAncestor, strategy);
  } else {
    const visualOffsets = getVisualOffsets(element);
    rect = {
      ...clippingAncestor,
      x: clippingAncestor.x - visualOffsets.x,
      y: clippingAncestor.y - visualOffsets.y
    };
  }
  return rectToClientRect(rect);
}
function hasFixedPositionAncestor(element, stopNode) {
  const parentNode = getParentNode(element);
  if (parentNode === stopNode || !isElement(parentNode) || isLastTraversableNode(parentNode)) {
    return false;
  }
  return getComputedStyle(parentNode).position === "fixed" || hasFixedPositionAncestor(parentNode, stopNode);
}
function getClippingElementAncestors(element, cache) {
  const cachedResult = cache.get(element);
  if (cachedResult) {
    return cachedResult;
  }
  let result = getOverflowAncestors(element, [], false).filter((el) => isElement(el) && getNodeName(el) !== "body");
  let currentContainingBlockComputedStyle = null;
  const elementIsFixed = getComputedStyle(element).position === "fixed";
  let currentNode = elementIsFixed ? getParentNode(element) : element;
  while (isElement(currentNode) && !isLastTraversableNode(currentNode)) {
    const computedStyle = getComputedStyle(currentNode);
    const currentNodeIsContaining = isContainingBlock(currentNode);
    if (!currentNodeIsContaining && computedStyle.position === "fixed") {
      currentContainingBlockComputedStyle = null;
    }
    const shouldDropCurrentNode = elementIsFixed ? !currentNodeIsContaining && !currentContainingBlockComputedStyle : !currentNodeIsContaining && computedStyle.position === "static" && !!currentContainingBlockComputedStyle && ["absolute", "fixed"].includes(currentContainingBlockComputedStyle.position) || isOverflowElement(currentNode) && !currentNodeIsContaining && hasFixedPositionAncestor(element, currentNode);
    if (shouldDropCurrentNode) {
      result = result.filter((ancestor) => ancestor !== currentNode);
    } else {
      currentContainingBlockComputedStyle = computedStyle;
    }
    currentNode = getParentNode(currentNode);
  }
  cache.set(element, result);
  return result;
}
function getClippingRect(_ref) {
  let {
    element,
    boundary,
    rootBoundary,
    strategy
  } = _ref;
  const elementClippingAncestors = boundary === "clippingAncestors" ? getClippingElementAncestors(element, this._c) : [].concat(boundary);
  const clippingAncestors = [...elementClippingAncestors, rootBoundary];
  const firstClippingAncestor = clippingAncestors[0];
  const clippingRect = clippingAncestors.reduce((accRect, clippingAncestor) => {
    const rect = getClientRectFromClippingAncestor(element, clippingAncestor, strategy);
    accRect.top = max(rect.top, accRect.top);
    accRect.right = min(rect.right, accRect.right);
    accRect.bottom = min(rect.bottom, accRect.bottom);
    accRect.left = max(rect.left, accRect.left);
    return accRect;
  }, getClientRectFromClippingAncestor(element, firstClippingAncestor, strategy));
  return {
    width: clippingRect.right - clippingRect.left,
    height: clippingRect.bottom - clippingRect.top,
    x: clippingRect.left,
    y: clippingRect.top
  };
}
function getDimensions(element) {
  return getCssDimensions(element);
}
function getRectRelativeToOffsetParent(element, offsetParent, strategy) {
  const isOffsetParentAnElement = isHTMLElement(offsetParent);
  const documentElement = getDocumentElement(offsetParent);
  const isFixed = strategy === "fixed";
  const rect = getBoundingClientRect(element, true, isFixed, offsetParent);
  let scroll = {
    scrollLeft: 0,
    scrollTop: 0
  };
  const offsets = createCoords(0);
  if (isOffsetParentAnElement || !isOffsetParentAnElement && !isFixed) {
    if (getNodeName(offsetParent) !== "body" || isOverflowElement(documentElement)) {
      scroll = getNodeScroll(offsetParent);
    }
    if (isOffsetParentAnElement) {
      const offsetRect = getBoundingClientRect(offsetParent, true, isFixed, offsetParent);
      offsets.x = offsetRect.x + offsetParent.clientLeft;
      offsets.y = offsetRect.y + offsetParent.clientTop;
    } else if (documentElement) {
      offsets.x = getWindowScrollBarX(documentElement);
    }
  }
  return {
    x: rect.left + scroll.scrollLeft - offsets.x,
    y: rect.top + scroll.scrollTop - offsets.y,
    width: rect.width,
    height: rect.height
  };
}
function getTrueOffsetParent(element, polyfill) {
  if (!isHTMLElement(element) || getComputedStyle(element).position === "fixed") {
    return null;
  }
  if (polyfill) {
    return polyfill(element);
  }
  return element.offsetParent;
}
function getOffsetParent(element, polyfill) {
  const window2 = getWindow(element);
  if (!isHTMLElement(element)) {
    return window2;
  }
  let offsetParent = getTrueOffsetParent(element, polyfill);
  while (offsetParent && isTableElement(offsetParent) && getComputedStyle(offsetParent).position === "static") {
    offsetParent = getTrueOffsetParent(offsetParent, polyfill);
  }
  if (offsetParent && (getNodeName(offsetParent) === "html" || getNodeName(offsetParent) === "body" && getComputedStyle(offsetParent).position === "static" && !isContainingBlock(offsetParent))) {
    return window2;
  }
  return offsetParent || getContainingBlock(element) || window2;
}
var getElementRects = async function(_ref) {
  let {
    reference,
    floating,
    strategy
  } = _ref;
  const getOffsetParentFn = this.getOffsetParent || getOffsetParent;
  const getDimensionsFn = this.getDimensions;
  return {
    reference: getRectRelativeToOffsetParent(reference, await getOffsetParentFn(floating), strategy),
    floating: {
      x: 0,
      y: 0,
      ...await getDimensionsFn(floating)
    }
  };
};
function isRTL(element) {
  return getComputedStyle(element).direction === "rtl";
}
var platform = {
  convertOffsetParentRelativeRectToViewportRelativeRect,
  getDocumentElement,
  getClippingRect,
  getOffsetParent,
  getElementRects,
  getClientRects,
  getDimensions,
  getScale,
  isElement,
  isRTL
};
function observeMove(element, onMove) {
  let io = null;
  let timeoutId;
  const root = getDocumentElement(element);
  function cleanup() {
    clearTimeout(timeoutId);
    io && io.disconnect();
    io = null;
  }
  function refresh(skip, threshold) {
    if (skip === void 0) {
      skip = false;
    }
    if (threshold === void 0) {
      threshold = 1;
    }
    cleanup();
    const {
      left,
      top,
      width,
      height
    } = element.getBoundingClientRect();
    if (!skip) {
      onMove();
    }
    if (!width || !height) {
      return;
    }
    const insetTop = floor(top);
    const insetRight = floor(root.clientWidth - (left + width));
    const insetBottom = floor(root.clientHeight - (top + height));
    const insetLeft = floor(left);
    const rootMargin = -insetTop + "px " + -insetRight + "px " + -insetBottom + "px " + -insetLeft + "px";
    const options = {
      rootMargin,
      threshold: max(0, min(1, threshold)) || 1
    };
    let isFirstUpdate = true;
    function handleObserve(entries) {
      const ratio = entries[0].intersectionRatio;
      if (ratio !== threshold) {
        if (!isFirstUpdate) {
          return refresh();
        }
        if (!ratio) {
          timeoutId = setTimeout(() => {
            refresh(false, 1e-7);
          }, 100);
        } else {
          refresh(false, ratio);
        }
      }
      isFirstUpdate = false;
    }
    try {
      io = new IntersectionObserver(handleObserve, {
        ...options,
        // Handle <iframe>s
        root: root.ownerDocument
      });
    } catch (e6) {
      io = new IntersectionObserver(handleObserve, options);
    }
    io.observe(element);
  }
  refresh(true);
  return cleanup;
}
function autoUpdate(reference, floating, update, options) {
  if (options === void 0) {
    options = {};
  }
  const {
    ancestorScroll = true,
    ancestorResize = true,
    elementResize = typeof ResizeObserver === "function",
    layoutShift = typeof IntersectionObserver === "function",
    animationFrame = false
  } = options;
  const referenceEl = unwrapElement(reference);
  const ancestors = ancestorScroll || ancestorResize ? [...referenceEl ? getOverflowAncestors(referenceEl) : [], ...getOverflowAncestors(floating)] : [];
  ancestors.forEach((ancestor) => {
    ancestorScroll && ancestor.addEventListener("scroll", update, {
      passive: true
    });
    ancestorResize && ancestor.addEventListener("resize", update);
  });
  const cleanupIo = referenceEl && layoutShift ? observeMove(referenceEl, update) : null;
  let reobserveFrame = -1;
  let resizeObserver = null;
  if (elementResize) {
    resizeObserver = new ResizeObserver((_ref) => {
      let [firstEntry] = _ref;
      if (firstEntry && firstEntry.target === referenceEl && resizeObserver) {
        resizeObserver.unobserve(floating);
        cancelAnimationFrame(reobserveFrame);
        reobserveFrame = requestAnimationFrame(() => {
          resizeObserver && resizeObserver.observe(floating);
        });
      }
      update();
    });
    if (referenceEl && !animationFrame) {
      resizeObserver.observe(referenceEl);
    }
    resizeObserver.observe(floating);
  }
  let frameId;
  let prevRefRect = animationFrame ? getBoundingClientRect(reference) : null;
  if (animationFrame) {
    frameLoop();
  }
  function frameLoop() {
    const nextRefRect = getBoundingClientRect(reference);
    if (prevRefRect && (nextRefRect.x !== prevRefRect.x || nextRefRect.y !== prevRefRect.y || nextRefRect.width !== prevRefRect.width || nextRefRect.height !== prevRefRect.height)) {
      update();
    }
    prevRefRect = nextRefRect;
    frameId = requestAnimationFrame(frameLoop);
  }
  update();
  return () => {
    ancestors.forEach((ancestor) => {
      ancestorScroll && ancestor.removeEventListener("scroll", update);
      ancestorResize && ancestor.removeEventListener("resize", update);
    });
    cleanupIo && cleanupIo();
    resizeObserver && resizeObserver.disconnect();
    resizeObserver = null;
    if (animationFrame) {
      cancelAnimationFrame(frameId);
    }
  };
}
var computePosition2 = (reference, floating, options) => {
  const cache = /* @__PURE__ */ new Map();
  const mergedOptions = {
    platform,
    ...options
  };
  const platformWithCache = {
    ...mergedOptions.platform,
    _c: cache
  };
  return computePosition(reference, floating, {
    ...mergedOptions,
    platform: platformWithCache
  });
};

// assets/components/popover.ts
var PopoverElement = class extends s3 {
  constructor() {
    super(...arguments);
    this.open = false;
    this.trigger = "";
    this.placement = "bottom";
    this.offset = 12;
  }
  firstUpdated() {
    const triggered = () => this.open ? this.destroy() : this.setup();
    document.querySelector(this.trigger)?.addEventListener("click", triggered);
    document.addEventListener("click", (e6) => {
      if (!this.open) {
        return;
      }
      if (document.querySelector(this.trigger)?.contains(e6.target)) {
        return;
      }
      if (!this.contains(e6.target)) {
        this.open = false;
      }
    });
  }
  setup() {
    this.open = true;
    const triggerEl = document.querySelector(this.trigger);
    if (!triggerEl) {
      throw new Error("Trigger element not found.");
    }
    if (this.floatingEl.length == 0) {
      throw new Error("Empty slot.");
    }
    autoUpdate(triggerEl, this.floatingEl[0], () => {
      computePosition2(triggerEl, this.floatingEl[0], {
        placement: this.placement,
        middleware: [offset(this.offset)]
      }).then(({ x: x2, y: y3 }) => {
        Object.assign(this.floatingEl[0].style, {
          left: `${x2}px`,
          top: `${y3}px`
        });
      });
    });
  }
  destroy() {
    this.open = false;
  }
  render() {
    const styles = o6({
      display: this.open ? "block" : "none"
    });
    return x`
            <slot style="${styles}"></slot>`;
  }
};
__decorateClass([
  n4({ reflect: true, type: Boolean })
], PopoverElement.prototype, "open", 2);
__decorateClass([
  n4()
], PopoverElement.prototype, "trigger", 2);
__decorateClass([
  o5({ selector: "*:first-child" })
], PopoverElement.prototype, "floatingEl", 2);
__decorateClass([
  n4()
], PopoverElement.prototype, "placement", 2);
__decorateClass([
  n4({ type: Number })
], PopoverElement.prototype, "offset", 2);
PopoverElement = __decorateClass([
  t3("o-popover")
], PopoverElement);

// node_modules/notyf/notyf.es.js
var __assign = function() {
  __assign = Object.assign || function __assign2(t5) {
    for (var s4, i6 = 1, n6 = arguments.length; i6 < n6; i6++) {
      s4 = arguments[i6];
      for (var p3 in s4)
        if (Object.prototype.hasOwnProperty.call(s4, p3))
          t5[p3] = s4[p3];
    }
    return t5;
  };
  return __assign.apply(this, arguments);
};
var NotyfNotification = (
  /** @class */
  function() {
    function NotyfNotification2(options) {
      this.options = options;
      this.listeners = {};
    }
    NotyfNotification2.prototype.on = function(eventType, cb) {
      var callbacks = this.listeners[eventType] || [];
      this.listeners[eventType] = callbacks.concat([cb]);
    };
    NotyfNotification2.prototype.triggerEvent = function(eventType, event) {
      var _this = this;
      var callbacks = this.listeners[eventType] || [];
      callbacks.forEach(function(cb) {
        return cb({ target: _this, event });
      });
    };
    return NotyfNotification2;
  }()
);
var NotyfArrayEvent;
(function(NotyfArrayEvent2) {
  NotyfArrayEvent2[NotyfArrayEvent2["Add"] = 0] = "Add";
  NotyfArrayEvent2[NotyfArrayEvent2["Remove"] = 1] = "Remove";
})(NotyfArrayEvent || (NotyfArrayEvent = {}));
var NotyfArray = (
  /** @class */
  function() {
    function NotyfArray2() {
      this.notifications = [];
    }
    NotyfArray2.prototype.push = function(elem) {
      this.notifications.push(elem);
      this.updateFn(elem, NotyfArrayEvent.Add, this.notifications);
    };
    NotyfArray2.prototype.splice = function(index, num) {
      var elem = this.notifications.splice(index, num)[0];
      this.updateFn(elem, NotyfArrayEvent.Remove, this.notifications);
      return elem;
    };
    NotyfArray2.prototype.indexOf = function(elem) {
      return this.notifications.indexOf(elem);
    };
    NotyfArray2.prototype.onUpdate = function(fn) {
      this.updateFn = fn;
    };
    return NotyfArray2;
  }()
);
var NotyfEvent;
(function(NotyfEvent2) {
  NotyfEvent2["Dismiss"] = "dismiss";
  NotyfEvent2["Click"] = "click";
})(NotyfEvent || (NotyfEvent = {}));
var DEFAULT_OPTIONS = {
  types: [
    {
      type: "success",
      className: "notyf__toast--success",
      backgroundColor: "#3dc763",
      icon: {
        className: "notyf__icon--success",
        tagName: "i"
      }
    },
    {
      type: "error",
      className: "notyf__toast--error",
      backgroundColor: "#ed3d3d",
      icon: {
        className: "notyf__icon--error",
        tagName: "i"
      }
    }
  ],
  duration: 2e3,
  ripple: true,
  position: {
    x: "right",
    y: "bottom"
  },
  dismissible: false
};
var NotyfView = (
  /** @class */
  function() {
    function NotyfView2() {
      this.notifications = [];
      this.events = {};
      this.X_POSITION_FLEX_MAP = {
        left: "flex-start",
        center: "center",
        right: "flex-end"
      };
      this.Y_POSITION_FLEX_MAP = {
        top: "flex-start",
        center: "center",
        bottom: "flex-end"
      };
      var docFrag = document.createDocumentFragment();
      var notyfContainer = this._createHTMLElement({ tagName: "div", className: "notyf" });
      docFrag.appendChild(notyfContainer);
      document.body.appendChild(docFrag);
      this.container = notyfContainer;
      this.animationEndEventName = this._getAnimationEndEventName();
      this._createA11yContainer();
    }
    NotyfView2.prototype.on = function(event, cb) {
      var _a;
      this.events = __assign(__assign({}, this.events), (_a = {}, _a[event] = cb, _a));
    };
    NotyfView2.prototype.update = function(notification, type) {
      if (type === NotyfArrayEvent.Add) {
        this.addNotification(notification);
      } else if (type === NotyfArrayEvent.Remove) {
        this.removeNotification(notification);
      }
    };
    NotyfView2.prototype.removeNotification = function(notification) {
      var _this = this;
      var renderedNotification = this._popRenderedNotification(notification);
      var node;
      if (!renderedNotification) {
        return;
      }
      node = renderedNotification.node;
      node.classList.add("notyf__toast--disappear");
      var handleEvent;
      node.addEventListener(this.animationEndEventName, handleEvent = function(event) {
        if (event.target === node) {
          node.removeEventListener(_this.animationEndEventName, handleEvent);
          _this.container.removeChild(node);
        }
      });
    };
    NotyfView2.prototype.addNotification = function(notification) {
      var node = this._renderNotification(notification);
      this.notifications.push({ notification, node });
      this._announce(notification.options.message || "Notification");
    };
    NotyfView2.prototype._renderNotification = function(notification) {
      var _a;
      var card = this._buildNotificationCard(notification);
      var className = notification.options.className;
      if (className) {
        (_a = card.classList).add.apply(_a, className.split(" "));
      }
      this.container.appendChild(card);
      return card;
    };
    NotyfView2.prototype._popRenderedNotification = function(notification) {
      var idx = -1;
      for (var i6 = 0; i6 < this.notifications.length && idx < 0; i6++) {
        if (this.notifications[i6].notification === notification) {
          idx = i6;
        }
      }
      if (idx !== -1) {
        return this.notifications.splice(idx, 1)[0];
      }
      return;
    };
    NotyfView2.prototype.getXPosition = function(options) {
      var _a;
      return ((_a = options === null || options === void 0 ? void 0 : options.position) === null || _a === void 0 ? void 0 : _a.x) || "right";
    };
    NotyfView2.prototype.getYPosition = function(options) {
      var _a;
      return ((_a = options === null || options === void 0 ? void 0 : options.position) === null || _a === void 0 ? void 0 : _a.y) || "bottom";
    };
    NotyfView2.prototype.adjustContainerAlignment = function(options) {
      var align = this.X_POSITION_FLEX_MAP[this.getXPosition(options)];
      var justify = this.Y_POSITION_FLEX_MAP[this.getYPosition(options)];
      var style = this.container.style;
      style.setProperty("justify-content", justify);
      style.setProperty("align-items", align);
    };
    NotyfView2.prototype._buildNotificationCard = function(notification) {
      var _this = this;
      var options = notification.options;
      var iconOpts = options.icon;
      this.adjustContainerAlignment(options);
      var notificationElem = this._createHTMLElement({ tagName: "div", className: "notyf__toast" });
      var ripple = this._createHTMLElement({ tagName: "div", className: "notyf__ripple" });
      var wrapper = this._createHTMLElement({ tagName: "div", className: "notyf__wrapper" });
      var message = this._createHTMLElement({ tagName: "div", className: "notyf__message" });
      message.innerHTML = options.message || "";
      var mainColor = options.background || options.backgroundColor;
      if (iconOpts) {
        var iconContainer = this._createHTMLElement({ tagName: "div", className: "notyf__icon" });
        if (typeof iconOpts === "string" || iconOpts instanceof String)
          iconContainer.innerHTML = new String(iconOpts).valueOf();
        if (typeof iconOpts === "object") {
          var _a = iconOpts.tagName, tagName = _a === void 0 ? "i" : _a, className_1 = iconOpts.className, text = iconOpts.text, _b = iconOpts.color, color = _b === void 0 ? mainColor : _b;
          var iconElement = this._createHTMLElement({ tagName, className: className_1, text });
          if (color)
            iconElement.style.color = color;
          iconContainer.appendChild(iconElement);
        }
        wrapper.appendChild(iconContainer);
      }
      wrapper.appendChild(message);
      notificationElem.appendChild(wrapper);
      if (mainColor) {
        if (options.ripple) {
          ripple.style.background = mainColor;
          notificationElem.appendChild(ripple);
        } else {
          notificationElem.style.background = mainColor;
        }
      }
      if (options.dismissible) {
        var dismissWrapper = this._createHTMLElement({ tagName: "div", className: "notyf__dismiss" });
        var dismissButton = this._createHTMLElement({
          tagName: "button",
          className: "notyf__dismiss-btn"
        });
        dismissWrapper.appendChild(dismissButton);
        wrapper.appendChild(dismissWrapper);
        notificationElem.classList.add("notyf__toast--dismissible");
        dismissButton.addEventListener("click", function(event) {
          var _a2, _b2;
          (_b2 = (_a2 = _this.events)[NotyfEvent.Dismiss]) === null || _b2 === void 0 ? void 0 : _b2.call(_a2, { target: notification, event });
          event.stopPropagation();
        });
      }
      notificationElem.addEventListener("click", function(event) {
        var _a2, _b2;
        return (_b2 = (_a2 = _this.events)[NotyfEvent.Click]) === null || _b2 === void 0 ? void 0 : _b2.call(_a2, { target: notification, event });
      });
      var className = this.getYPosition(options) === "top" ? "upper" : "lower";
      notificationElem.classList.add("notyf__toast--" + className);
      return notificationElem;
    };
    NotyfView2.prototype._createHTMLElement = function(_a) {
      var tagName = _a.tagName, className = _a.className, text = _a.text;
      var elem = document.createElement(tagName);
      if (className) {
        elem.className = className;
      }
      elem.textContent = text || null;
      return elem;
    };
    NotyfView2.prototype._createA11yContainer = function() {
      var a11yContainer = this._createHTMLElement({ tagName: "div", className: "notyf-announcer" });
      a11yContainer.setAttribute("aria-atomic", "true");
      a11yContainer.setAttribute("aria-live", "polite");
      a11yContainer.style.border = "0";
      a11yContainer.style.clip = "rect(0 0 0 0)";
      a11yContainer.style.height = "1px";
      a11yContainer.style.margin = "-1px";
      a11yContainer.style.overflow = "hidden";
      a11yContainer.style.padding = "0";
      a11yContainer.style.position = "absolute";
      a11yContainer.style.width = "1px";
      a11yContainer.style.outline = "0";
      document.body.appendChild(a11yContainer);
      this.a11yContainer = a11yContainer;
    };
    NotyfView2.prototype._announce = function(message) {
      var _this = this;
      this.a11yContainer.textContent = "";
      setTimeout(function() {
        _this.a11yContainer.textContent = message;
      }, 100);
    };
    NotyfView2.prototype._getAnimationEndEventName = function() {
      var el = document.createElement("_fake");
      var transitions = {
        MozTransition: "animationend",
        OTransition: "oAnimationEnd",
        WebkitTransition: "webkitAnimationEnd",
        transition: "animationend"
      };
      var t5;
      for (t5 in transitions) {
        if (el.style[t5] !== void 0) {
          return transitions[t5];
        }
      }
      return "animationend";
    };
    return NotyfView2;
  }()
);
var Notyf = (
  /** @class */
  function() {
    function Notyf2(opts) {
      var _this = this;
      this.dismiss = this._removeNotification;
      this.notifications = new NotyfArray();
      this.view = new NotyfView();
      var types = this.registerTypes(opts);
      this.options = __assign(__assign({}, DEFAULT_OPTIONS), opts);
      this.options.types = types;
      this.notifications.onUpdate(function(elem, type) {
        return _this.view.update(elem, type);
      });
      this.view.on(NotyfEvent.Dismiss, function(_a) {
        var target = _a.target, event = _a.event;
        _this._removeNotification(target);
        target["triggerEvent"](NotyfEvent.Dismiss, event);
      });
      this.view.on(NotyfEvent.Click, function(_a) {
        var target = _a.target, event = _a.event;
        return target["triggerEvent"](NotyfEvent.Click, event);
      });
    }
    Notyf2.prototype.error = function(payload) {
      var options = this.normalizeOptions("error", payload);
      return this.open(options);
    };
    Notyf2.prototype.success = function(payload) {
      var options = this.normalizeOptions("success", payload);
      return this.open(options);
    };
    Notyf2.prototype.open = function(options) {
      var defaultOpts = this.options.types.find(function(_a) {
        var type = _a.type;
        return type === options.type;
      }) || {};
      var config = __assign(__assign({}, defaultOpts), options);
      this.assignProps(["ripple", "position", "dismissible"], config);
      var notification = new NotyfNotification(config);
      this._pushNotification(notification);
      return notification;
    };
    Notyf2.prototype.dismissAll = function() {
      while (this.notifications.splice(0, 1))
        ;
    };
    Notyf2.prototype.assignProps = function(props, config) {
      var _this = this;
      props.forEach(function(prop) {
        config[prop] = config[prop] == null ? _this.options[prop] : config[prop];
      });
    };
    Notyf2.prototype._pushNotification = function(notification) {
      var _this = this;
      this.notifications.push(notification);
      var duration = notification.options.duration !== void 0 ? notification.options.duration : this.options.duration;
      if (duration) {
        setTimeout(function() {
          return _this._removeNotification(notification);
        }, duration);
      }
    };
    Notyf2.prototype._removeNotification = function(notification) {
      var index = this.notifications.indexOf(notification);
      if (index !== -1) {
        this.notifications.splice(index, 1);
      }
    };
    Notyf2.prototype.normalizeOptions = function(type, payload) {
      var options = { type };
      if (typeof payload === "string") {
        options.message = payload;
      } else if (typeof payload === "object") {
        options = __assign(__assign({}, options), payload);
      }
      return options;
    };
    Notyf2.prototype.registerTypes = function(opts) {
      var incomingTypes = (opts && opts.types || []).slice();
      var finalDefaultTypes = DEFAULT_OPTIONS.types.map(function(defaultType) {
        var userTypeIdx = -1;
        incomingTypes.forEach(function(t5, idx) {
          if (t5.type === defaultType.type)
            userTypeIdx = idx;
        });
        var userType = userTypeIdx !== -1 ? incomingTypes.splice(userTypeIdx, 1)[0] : {};
        return __assign(__assign({}, defaultType), userType);
      });
      return finalDefaultTypes.concat(incomingTypes);
    };
    return Notyf2;
  }()
);

// assets/components/toasts.ts
var toast = new Notyf({
  position: { x: "center", y: "bottom" },
  ripple: false,
  duration: 3e3,
  dismissible: true
});
var ToastsElement = class extends s3 {
  constructor() {
    super(...arguments);
    this.duration = 3e3;
    this.toast = null;
  }
  firstUpdated() {
    this.toast = new Notyf({
      position: { x: "center", y: "bottom" },
      ripple: false,
      duration: this.duration,
      dismissible: true
    });
    this.displayPendingToasts();
  }
  connectedCallback() {
    super.connectedCallback();
    document.addEventListener("toast", this.onToast.bind(this));
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener("toast", this.onToast.bind(this));
  }
  displayPendingToasts() {
    const toasts = JSON.parse(this.textContent || "[]");
    toasts.forEach((toast2) => this.display(toast2));
  }
  show(message, category = "success") {
    this.display({ message, category });
  }
  display(toast2) {
    this.toast?.open({
      type: toast2.category,
      message: toast2.message
    });
  }
  onToast(e6) {
    this.display(e6.detail);
  }
  render() {
    return null;
  }
};
__decorateClass([
  n4({ type: Number })
], ToastsElement.prototype, "duration", 2);
ToastsElement = __decorateClass([
  t3("o-toasts")
], ToastsElement);

// assets/components/modals.ts
var Modals = class extends s3 {
};
Modals = __decorateClass([
  t3("o-modals")
], Modals);
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/custom-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/property.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/state.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/event-options.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/base.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-all.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-async.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/directive.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/directives/style-map.js:
  (**
   * @license
   * Copyright 2018 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

notyf/notyf.es.js:
  (*! *****************************************************************************
  Copyright (c) Microsoft Corporation.
  
  Permission to use, copy, modify, and/or distribute this software for any
  purpose with or without fee is hereby granted.
  
  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
  REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
  AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
  INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
  LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
  OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
  PERFORMANCE OF THIS SOFTWARE.
  ***************************************************************************** *)
*/
//# sourceMappingURL=main.js.map
