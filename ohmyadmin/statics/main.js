var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i4 = decorators.length - 1, decorator; i4 >= 0; i4--)
    if (decorator = decorators[i4])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result)
    __defProp(target, key, result);
  return result;
};

// assets/node_modules/@lit/reactive-element/css-tag.js
var t = window;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var n = /* @__PURE__ */ new WeakMap();
var o = class {
  constructor(t3, e7, n6) {
    if (this._$cssResult$ = true, n6 !== s)
      throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t3, this.t = e7;
  }
  get styleSheet() {
    let t3 = this.o;
    const s5 = this.t;
    if (e && void 0 === t3) {
      const e7 = void 0 !== s5 && 1 === s5.length;
      e7 && (t3 = n.get(s5)), void 0 === t3 && ((this.o = t3 = new CSSStyleSheet()).replaceSync(this.cssText), e7 && n.set(s5, t3));
    }
    return t3;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t3) => new o("string" == typeof t3 ? t3 : t3 + "", void 0, s);
var i = (t3, ...e7) => {
  const n6 = 1 === t3.length ? t3[0] : e7.reduce((e8, s5, n7) => e8 + ((t4) => {
    if (true === t4._$cssResult$)
      return t4.cssText;
    if ("number" == typeof t4)
      return t4;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t4 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s5) + t3[n7 + 1], t3[0]);
  return new o(n6, t3, s);
};
var S = (s5, n6) => {
  e ? s5.adoptedStyleSheets = n6.map((t3) => t3 instanceof CSSStyleSheet ? t3 : t3.styleSheet) : n6.forEach((e7) => {
    const n7 = document.createElement("style"), o6 = t.litNonce;
    void 0 !== o6 && n7.setAttribute("nonce", o6), n7.textContent = e7.cssText, s5.appendChild(n7);
  });
};
var c = e ? (t3) => t3 : (t3) => t3 instanceof CSSStyleSheet ? ((t4) => {
  let e7 = "";
  for (const s5 of t4.cssRules)
    e7 += s5.cssText;
  return r(e7);
})(t3) : t3;

// assets/node_modules/@lit/reactive-element/reactive-element.js
var s2;
var e2 = window;
var r2 = e2.trustedTypes;
var h = r2 ? r2.emptyScript : "";
var o2 = e2.reactiveElementPolyfillSupport;
var n2 = { toAttribute(t3, i4) {
  switch (i4) {
    case Boolean:
      t3 = t3 ? h : null;
      break;
    case Object:
    case Array:
      t3 = null == t3 ? t3 : JSON.stringify(t3);
  }
  return t3;
}, fromAttribute(t3, i4) {
  let s5 = t3;
  switch (i4) {
    case Boolean:
      s5 = null !== t3;
      break;
    case Number:
      s5 = null === t3 ? null : Number(t3);
      break;
    case Object:
    case Array:
      try {
        s5 = JSON.parse(t3);
      } catch (t4) {
        s5 = null;
      }
  }
  return s5;
} };
var a = (t3, i4) => i4 !== t3 && (i4 == i4 || t3 == t3);
var l = { attribute: true, type: String, converter: n2, reflect: false, hasChanged: a };
var d = class extends HTMLElement {
  constructor() {
    super(), this._$Ei = /* @__PURE__ */ new Map(), this.isUpdatePending = false, this.hasUpdated = false, this._$El = null, this.u();
  }
  static addInitializer(t3) {
    var i4;
    this.finalize(), (null !== (i4 = this.h) && void 0 !== i4 ? i4 : this.h = []).push(t3);
  }
  static get observedAttributes() {
    this.finalize();
    const t3 = [];
    return this.elementProperties.forEach((i4, s5) => {
      const e7 = this._$Ep(s5, i4);
      void 0 !== e7 && (this._$Ev.set(e7, s5), t3.push(e7));
    }), t3;
  }
  static createProperty(t3, i4 = l) {
    if (i4.state && (i4.attribute = false), this.finalize(), this.elementProperties.set(t3, i4), !i4.noAccessor && !this.prototype.hasOwnProperty(t3)) {
      const s5 = "symbol" == typeof t3 ? Symbol() : "__" + t3, e7 = this.getPropertyDescriptor(t3, s5, i4);
      void 0 !== e7 && Object.defineProperty(this.prototype, t3, e7);
    }
  }
  static getPropertyDescriptor(t3, i4, s5) {
    return { get() {
      return this[i4];
    }, set(e7) {
      const r4 = this[t3];
      this[i4] = e7, this.requestUpdate(t3, r4, s5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t3) {
    return this.elementProperties.get(t3) || l;
  }
  static finalize() {
    if (this.hasOwnProperty("finalized"))
      return false;
    this.finalized = true;
    const t3 = Object.getPrototypeOf(this);
    if (t3.finalize(), void 0 !== t3.h && (this.h = [...t3.h]), this.elementProperties = new Map(t3.elementProperties), this._$Ev = /* @__PURE__ */ new Map(), this.hasOwnProperty("properties")) {
      const t4 = this.properties, i4 = [...Object.getOwnPropertyNames(t4), ...Object.getOwnPropertySymbols(t4)];
      for (const s5 of i4)
        this.createProperty(s5, t4[s5]);
    }
    return this.elementStyles = this.finalizeStyles(this.styles), true;
  }
  static finalizeStyles(i4) {
    const s5 = [];
    if (Array.isArray(i4)) {
      const e7 = new Set(i4.flat(1 / 0).reverse());
      for (const i5 of e7)
        s5.unshift(c(i5));
    } else
      void 0 !== i4 && s5.push(c(i4));
    return s5;
  }
  static _$Ep(t3, i4) {
    const s5 = i4.attribute;
    return false === s5 ? void 0 : "string" == typeof s5 ? s5 : "string" == typeof t3 ? t3.toLowerCase() : void 0;
  }
  u() {
    var t3;
    this._$E_ = new Promise((t4) => this.enableUpdating = t4), this._$AL = /* @__PURE__ */ new Map(), this._$Eg(), this.requestUpdate(), null === (t3 = this.constructor.h) || void 0 === t3 || t3.forEach((t4) => t4(this));
  }
  addController(t3) {
    var i4, s5;
    (null !== (i4 = this._$ES) && void 0 !== i4 ? i4 : this._$ES = []).push(t3), void 0 !== this.renderRoot && this.isConnected && (null === (s5 = t3.hostConnected) || void 0 === s5 || s5.call(t3));
  }
  removeController(t3) {
    var i4;
    null === (i4 = this._$ES) || void 0 === i4 || i4.splice(this._$ES.indexOf(t3) >>> 0, 1);
  }
  _$Eg() {
    this.constructor.elementProperties.forEach((t3, i4) => {
      this.hasOwnProperty(i4) && (this._$Ei.set(i4, this[i4]), delete this[i4]);
    });
  }
  createRenderRoot() {
    var t3;
    const s5 = null !== (t3 = this.shadowRoot) && void 0 !== t3 ? t3 : this.attachShadow(this.constructor.shadowRootOptions);
    return S(s5, this.constructor.elementStyles), s5;
  }
  connectedCallback() {
    var t3;
    void 0 === this.renderRoot && (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), null === (t3 = this._$ES) || void 0 === t3 || t3.forEach((t4) => {
      var i4;
      return null === (i4 = t4.hostConnected) || void 0 === i4 ? void 0 : i4.call(t4);
    });
  }
  enableUpdating(t3) {
  }
  disconnectedCallback() {
    var t3;
    null === (t3 = this._$ES) || void 0 === t3 || t3.forEach((t4) => {
      var i4;
      return null === (i4 = t4.hostDisconnected) || void 0 === i4 ? void 0 : i4.call(t4);
    });
  }
  attributeChangedCallback(t3, i4, s5) {
    this._$AK(t3, s5);
  }
  _$EO(t3, i4, s5 = l) {
    var e7;
    const r4 = this.constructor._$Ep(t3, s5);
    if (void 0 !== r4 && true === s5.reflect) {
      const h3 = (void 0 !== (null === (e7 = s5.converter) || void 0 === e7 ? void 0 : e7.toAttribute) ? s5.converter : n2).toAttribute(i4, s5.type);
      this._$El = t3, null == h3 ? this.removeAttribute(r4) : this.setAttribute(r4, h3), this._$El = null;
    }
  }
  _$AK(t3, i4) {
    var s5;
    const e7 = this.constructor, r4 = e7._$Ev.get(t3);
    if (void 0 !== r4 && this._$El !== r4) {
      const t4 = e7.getPropertyOptions(r4), h3 = "function" == typeof t4.converter ? { fromAttribute: t4.converter } : void 0 !== (null === (s5 = t4.converter) || void 0 === s5 ? void 0 : s5.fromAttribute) ? t4.converter : n2;
      this._$El = r4, this[r4] = h3.fromAttribute(i4, t4.type), this._$El = null;
    }
  }
  requestUpdate(t3, i4, s5) {
    let e7 = true;
    void 0 !== t3 && (((s5 = s5 || this.constructor.getPropertyOptions(t3)).hasChanged || a)(this[t3], i4) ? (this._$AL.has(t3) || this._$AL.set(t3, i4), true === s5.reflect && this._$El !== t3 && (void 0 === this._$EC && (this._$EC = /* @__PURE__ */ new Map()), this._$EC.set(t3, s5))) : e7 = false), !this.isUpdatePending && e7 && (this._$E_ = this._$Ej());
  }
  async _$Ej() {
    this.isUpdatePending = true;
    try {
      await this._$E_;
    } catch (t4) {
      Promise.reject(t4);
    }
    const t3 = this.scheduleUpdate();
    return null != t3 && await t3, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var t3;
    if (!this.isUpdatePending)
      return;
    this.hasUpdated, this._$Ei && (this._$Ei.forEach((t4, i5) => this[i5] = t4), this._$Ei = void 0);
    let i4 = false;
    const s5 = this._$AL;
    try {
      i4 = this.shouldUpdate(s5), i4 ? (this.willUpdate(s5), null === (t3 = this._$ES) || void 0 === t3 || t3.forEach((t4) => {
        var i5;
        return null === (i5 = t4.hostUpdate) || void 0 === i5 ? void 0 : i5.call(t4);
      }), this.update(s5)) : this._$Ek();
    } catch (t4) {
      throw i4 = false, this._$Ek(), t4;
    }
    i4 && this._$AE(s5);
  }
  willUpdate(t3) {
  }
  _$AE(t3) {
    var i4;
    null === (i4 = this._$ES) || void 0 === i4 || i4.forEach((t4) => {
      var i5;
      return null === (i5 = t4.hostUpdated) || void 0 === i5 ? void 0 : i5.call(t4);
    }), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t3)), this.updated(t3);
  }
  _$Ek() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$E_;
  }
  shouldUpdate(t3) {
    return true;
  }
  update(t3) {
    void 0 !== this._$EC && (this._$EC.forEach((t4, i4) => this._$EO(i4, this[i4], t4)), this._$EC = void 0), this._$Ek();
  }
  updated(t3) {
  }
  firstUpdated(t3) {
  }
};
d.finalized = true, d.elementProperties = /* @__PURE__ */ new Map(), d.elementStyles = [], d.shadowRootOptions = { mode: "open" }, null == o2 || o2({ ReactiveElement: d }), (null !== (s2 = e2.reactiveElementVersions) && void 0 !== s2 ? s2 : e2.reactiveElementVersions = []).push("1.5.0");

// assets/node_modules/lit-html/lit-html.js
var t2;
var i2 = window;
var s3 = i2.trustedTypes;
var e3 = s3 ? s3.createPolicy("lit-html", { createHTML: (t3) => t3 }) : void 0;
var o3 = `lit$${(Math.random() + "").slice(9)}$`;
var n3 = "?" + o3;
var l2 = `<${n3}>`;
var h2 = document;
var r3 = (t3 = "") => h2.createComment(t3);
var d2 = (t3) => null === t3 || "object" != typeof t3 && "function" != typeof t3;
var u = Array.isArray;
var c2 = (t3) => u(t3) || "function" == typeof (null == t3 ? void 0 : t3[Symbol.iterator]);
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var a2 = /-->/g;
var f = />/g;
var _ = RegExp(`>|[ 	
\f\r](?:([^\\s"'>=/]+)([ 	
\f\r]*=[ 	
\f\r]*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var m = /'/g;
var p = /"/g;
var $ = /^(?:script|style|textarea|title)$/i;
var g = (t3) => (i4, ...s5) => ({ _$litType$: t3, strings: i4, values: s5 });
var y = g(1);
var w = g(2);
var x = Symbol.for("lit-noChange");
var b = Symbol.for("lit-nothing");
var T = /* @__PURE__ */ new WeakMap();
var A = h2.createTreeWalker(h2, 129, null, false);
var E = (t3, i4) => {
  const s5 = t3.length - 1, n6 = [];
  let h3, r4 = 2 === i4 ? "<svg>" : "", d3 = v;
  for (let i5 = 0; i5 < s5; i5++) {
    const s6 = t3[i5];
    let e7, u3, c3 = -1, g2 = 0;
    for (; g2 < s6.length && (d3.lastIndex = g2, u3 = d3.exec(s6), null !== u3); )
      g2 = d3.lastIndex, d3 === v ? "!--" === u3[1] ? d3 = a2 : void 0 !== u3[1] ? d3 = f : void 0 !== u3[2] ? ($.test(u3[2]) && (h3 = RegExp("</" + u3[2], "g")), d3 = _) : void 0 !== u3[3] && (d3 = _) : d3 === _ ? ">" === u3[0] ? (d3 = null != h3 ? h3 : v, c3 = -1) : void 0 === u3[1] ? c3 = -2 : (c3 = d3.lastIndex - u3[2].length, e7 = u3[1], d3 = void 0 === u3[3] ? _ : '"' === u3[3] ? p : m) : d3 === p || d3 === m ? d3 = _ : d3 === a2 || d3 === f ? d3 = v : (d3 = _, h3 = void 0);
    const y2 = d3 === _ && t3[i5 + 1].startsWith("/>") ? " " : "";
    r4 += d3 === v ? s6 + l2 : c3 >= 0 ? (n6.push(e7), s6.slice(0, c3) + "$lit$" + s6.slice(c3) + o3 + y2) : s6 + o3 + (-2 === c3 ? (n6.push(void 0), i5) : y2);
  }
  const u2 = r4 + (t3[s5] || "<?>") + (2 === i4 ? "</svg>" : "");
  if (!Array.isArray(t3) || !t3.hasOwnProperty("raw"))
    throw Error("invalid template strings array");
  return [void 0 !== e3 ? e3.createHTML(u2) : u2, n6];
};
var C = class _C {
  constructor({ strings: t3, _$litType$: i4 }, e7) {
    let l5;
    this.parts = [];
    let h3 = 0, d3 = 0;
    const u2 = t3.length - 1, c3 = this.parts, [v2, a3] = E(t3, i4);
    if (this.el = _C.createElement(v2, e7), A.currentNode = this.el.content, 2 === i4) {
      const t4 = this.el.content, i5 = t4.firstChild;
      i5.remove(), t4.append(...i5.childNodes);
    }
    for (; null !== (l5 = A.nextNode()) && c3.length < u2; ) {
      if (1 === l5.nodeType) {
        if (l5.hasAttributes()) {
          const t4 = [];
          for (const i5 of l5.getAttributeNames())
            if (i5.endsWith("$lit$") || i5.startsWith(o3)) {
              const s5 = a3[d3++];
              if (t4.push(i5), void 0 !== s5) {
                const t5 = l5.getAttribute(s5.toLowerCase() + "$lit$").split(o3), i6 = /([.?@])?(.*)/.exec(s5);
                c3.push({ type: 1, index: h3, name: i6[2], strings: t5, ctor: "." === i6[1] ? M : "?" === i6[1] ? k : "@" === i6[1] ? H : S2 });
              } else
                c3.push({ type: 6, index: h3 });
            }
          for (const i5 of t4)
            l5.removeAttribute(i5);
        }
        if ($.test(l5.tagName)) {
          const t4 = l5.textContent.split(o3), i5 = t4.length - 1;
          if (i5 > 0) {
            l5.textContent = s3 ? s3.emptyScript : "";
            for (let s5 = 0; s5 < i5; s5++)
              l5.append(t4[s5], r3()), A.nextNode(), c3.push({ type: 2, index: ++h3 });
            l5.append(t4[i5], r3());
          }
        }
      } else if (8 === l5.nodeType)
        if (l5.data === n3)
          c3.push({ type: 2, index: h3 });
        else {
          let t4 = -1;
          for (; -1 !== (t4 = l5.data.indexOf(o3, t4 + 1)); )
            c3.push({ type: 7, index: h3 }), t4 += o3.length - 1;
        }
      h3++;
    }
  }
  static createElement(t3, i4) {
    const s5 = h2.createElement("template");
    return s5.innerHTML = t3, s5;
  }
};
function P(t3, i4, s5 = t3, e7) {
  var o6, n6, l5, h3;
  if (i4 === x)
    return i4;
  let r4 = void 0 !== e7 ? null === (o6 = s5._$Co) || void 0 === o6 ? void 0 : o6[e7] : s5._$Cl;
  const u2 = d2(i4) ? void 0 : i4._$litDirective$;
  return (null == r4 ? void 0 : r4.constructor) !== u2 && (null === (n6 = null == r4 ? void 0 : r4._$AO) || void 0 === n6 || n6.call(r4, false), void 0 === u2 ? r4 = void 0 : (r4 = new u2(t3), r4._$AT(t3, s5, e7)), void 0 !== e7 ? (null !== (l5 = (h3 = s5)._$Co) && void 0 !== l5 ? l5 : h3._$Co = [])[e7] = r4 : s5._$Cl = r4), void 0 !== r4 && (i4 = P(t3, r4._$AS(t3, i4.values), r4, e7)), i4;
}
var V = class {
  constructor(t3, i4) {
    this.u = [], this._$AN = void 0, this._$AD = t3, this._$AM = i4;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  v(t3) {
    var i4;
    const { el: { content: s5 }, parts: e7 } = this._$AD, o6 = (null !== (i4 = null == t3 ? void 0 : t3.creationScope) && void 0 !== i4 ? i4 : h2).importNode(s5, true);
    A.currentNode = o6;
    let n6 = A.nextNode(), l5 = 0, r4 = 0, d3 = e7[0];
    for (; void 0 !== d3; ) {
      if (l5 === d3.index) {
        let i5;
        2 === d3.type ? i5 = new N(n6, n6.nextSibling, this, t3) : 1 === d3.type ? i5 = new d3.ctor(n6, d3.name, d3.strings, this, t3) : 6 === d3.type && (i5 = new I(n6, this, t3)), this.u.push(i5), d3 = e7[++r4];
      }
      l5 !== (null == d3 ? void 0 : d3.index) && (n6 = A.nextNode(), l5++);
    }
    return o6;
  }
  p(t3) {
    let i4 = 0;
    for (const s5 of this.u)
      void 0 !== s5 && (void 0 !== s5.strings ? (s5._$AI(t3, s5, i4), i4 += s5.strings.length - 2) : s5._$AI(t3[i4])), i4++;
  }
};
var N = class _N {
  constructor(t3, i4, s5, e7) {
    var o6;
    this.type = 2, this._$AH = b, this._$AN = void 0, this._$AA = t3, this._$AB = i4, this._$AM = s5, this.options = e7, this._$Cm = null === (o6 = null == e7 ? void 0 : e7.isConnected) || void 0 === o6 || o6;
  }
  get _$AU() {
    var t3, i4;
    return null !== (i4 = null === (t3 = this._$AM) || void 0 === t3 ? void 0 : t3._$AU) && void 0 !== i4 ? i4 : this._$Cm;
  }
  get parentNode() {
    let t3 = this._$AA.parentNode;
    const i4 = this._$AM;
    return void 0 !== i4 && 11 === t3.nodeType && (t3 = i4.parentNode), t3;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t3, i4 = this) {
    t3 = P(this, t3, i4), d2(t3) ? t3 === b || null == t3 || "" === t3 ? (this._$AH !== b && this._$AR(), this._$AH = b) : t3 !== this._$AH && t3 !== x && this.g(t3) : void 0 !== t3._$litType$ ? this.$(t3) : void 0 !== t3.nodeType ? this.T(t3) : c2(t3) ? this.k(t3) : this.g(t3);
  }
  O(t3, i4 = this._$AB) {
    return this._$AA.parentNode.insertBefore(t3, i4);
  }
  T(t3) {
    this._$AH !== t3 && (this._$AR(), this._$AH = this.O(t3));
  }
  g(t3) {
    this._$AH !== b && d2(this._$AH) ? this._$AA.nextSibling.data = t3 : this.T(h2.createTextNode(t3)), this._$AH = t3;
  }
  $(t3) {
    var i4;
    const { values: s5, _$litType$: e7 } = t3, o6 = "number" == typeof e7 ? this._$AC(t3) : (void 0 === e7.el && (e7.el = C.createElement(e7.h, this.options)), e7);
    if ((null === (i4 = this._$AH) || void 0 === i4 ? void 0 : i4._$AD) === o6)
      this._$AH.p(s5);
    else {
      const t4 = new V(o6, this), i5 = t4.v(this.options);
      t4.p(s5), this.T(i5), this._$AH = t4;
    }
  }
  _$AC(t3) {
    let i4 = T.get(t3.strings);
    return void 0 === i4 && T.set(t3.strings, i4 = new C(t3)), i4;
  }
  k(t3) {
    u(this._$AH) || (this._$AH = [], this._$AR());
    const i4 = this._$AH;
    let s5, e7 = 0;
    for (const o6 of t3)
      e7 === i4.length ? i4.push(s5 = new _N(this.O(r3()), this.O(r3()), this, this.options)) : s5 = i4[e7], s5._$AI(o6), e7++;
    e7 < i4.length && (this._$AR(s5 && s5._$AB.nextSibling, e7), i4.length = e7);
  }
  _$AR(t3 = this._$AA.nextSibling, i4) {
    var s5;
    for (null === (s5 = this._$AP) || void 0 === s5 || s5.call(this, false, true, i4); t3 && t3 !== this._$AB; ) {
      const i5 = t3.nextSibling;
      t3.remove(), t3 = i5;
    }
  }
  setConnected(t3) {
    var i4;
    void 0 === this._$AM && (this._$Cm = t3, null === (i4 = this._$AP) || void 0 === i4 || i4.call(this, t3));
  }
};
var S2 = class {
  constructor(t3, i4, s5, e7, o6) {
    this.type = 1, this._$AH = b, this._$AN = void 0, this.element = t3, this.name = i4, this._$AM = e7, this.options = o6, s5.length > 2 || "" !== s5[0] || "" !== s5[1] ? (this._$AH = Array(s5.length - 1).fill(new String()), this.strings = s5) : this._$AH = b;
  }
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3, i4 = this, s5, e7) {
    const o6 = this.strings;
    let n6 = false;
    if (void 0 === o6)
      t3 = P(this, t3, i4, 0), n6 = !d2(t3) || t3 !== this._$AH && t3 !== x, n6 && (this._$AH = t3);
    else {
      const e8 = t3;
      let l5, h3;
      for (t3 = o6[0], l5 = 0; l5 < o6.length - 1; l5++)
        h3 = P(this, e8[s5 + l5], i4, l5), h3 === x && (h3 = this._$AH[l5]), n6 || (n6 = !d2(h3) || h3 !== this._$AH[l5]), h3 === b ? t3 = b : t3 !== b && (t3 += (null != h3 ? h3 : "") + o6[l5 + 1]), this._$AH[l5] = h3;
    }
    n6 && !e7 && this.j(t3);
  }
  j(t3) {
    t3 === b ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, null != t3 ? t3 : "");
  }
};
var M = class extends S2 {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t3) {
    this.element[this.name] = t3 === b ? void 0 : t3;
  }
};
var R = s3 ? s3.emptyScript : "";
var k = class extends S2 {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t3) {
    t3 && t3 !== b ? this.element.setAttribute(this.name, R) : this.element.removeAttribute(this.name);
  }
};
var H = class extends S2 {
  constructor(t3, i4, s5, e7, o6) {
    super(t3, i4, s5, e7, o6), this.type = 5;
  }
  _$AI(t3, i4 = this) {
    var s5;
    if ((t3 = null !== (s5 = P(this, t3, i4, 0)) && void 0 !== s5 ? s5 : b) === x)
      return;
    const e7 = this._$AH, o6 = t3 === b && e7 !== b || t3.capture !== e7.capture || t3.once !== e7.once || t3.passive !== e7.passive, n6 = t3 !== b && (e7 === b || o6);
    o6 && this.element.removeEventListener(this.name, this, e7), n6 && this.element.addEventListener(this.name, this, t3), this._$AH = t3;
  }
  handleEvent(t3) {
    var i4, s5;
    "function" == typeof this._$AH ? this._$AH.call(null !== (s5 = null === (i4 = this.options) || void 0 === i4 ? void 0 : i4.host) && void 0 !== s5 ? s5 : this.element, t3) : this._$AH.handleEvent(t3);
  }
};
var I = class {
  constructor(t3, i4, s5) {
    this.element = t3, this.type = 6, this._$AN = void 0, this._$AM = i4, this.options = s5;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3) {
    P(this, t3);
  }
};
var z = i2.litHtmlPolyfillSupport;
null == z || z(C, N), (null !== (t2 = i2.litHtmlVersions) && void 0 !== t2 ? t2 : i2.litHtmlVersions = []).push("2.5.0");
var Z = (t3, i4, s5) => {
  var e7, o6;
  const n6 = null !== (e7 = null == s5 ? void 0 : s5.renderBefore) && void 0 !== e7 ? e7 : i4;
  let l5 = n6._$litPart$;
  if (void 0 === l5) {
    const t4 = null !== (o6 = null == s5 ? void 0 : s5.renderBefore) && void 0 !== o6 ? o6 : null;
    n6._$litPart$ = l5 = new N(i4.insertBefore(r3(), t4), t4, void 0, null != s5 ? s5 : {});
  }
  return l5._$AI(t3), l5;
};

// assets/node_modules/lit-element/lit-element.js
var l3;
var o4;
var s4 = class extends d {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var t3, e7;
    const i4 = super.createRenderRoot();
    return null !== (t3 = (e7 = this.renderOptions).renderBefore) && void 0 !== t3 || (e7.renderBefore = i4.firstChild), i4;
  }
  update(t3) {
    const i4 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t3), this._$Do = Z(i4, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var t3;
    super.connectedCallback(), null === (t3 = this._$Do) || void 0 === t3 || t3.setConnected(true);
  }
  disconnectedCallback() {
    var t3;
    super.disconnectedCallback(), null === (t3 = this._$Do) || void 0 === t3 || t3.setConnected(false);
  }
  render() {
    return x;
  }
};
s4.finalized = true, s4._$litElement$ = true, null === (l3 = globalThis.litElementHydrateSupport) || void 0 === l3 || l3.call(globalThis, { LitElement: s4 });
var n4 = globalThis.litElementPolyfillSupport;
null == n4 || n4({ LitElement: s4 });
(null !== (o4 = globalThis.litElementVersions) && void 0 !== o4 ? o4 : globalThis.litElementVersions = []).push("3.2.2");

// assets/node_modules/@lit/reactive-element/decorators/custom-element.js
var e4 = (e7) => (n6) => "function" == typeof n6 ? ((e8, n7) => (customElements.define(e8, n7), n7))(e7, n6) : ((e8, n7) => {
  const { kind: t3, elements: s5 } = n7;
  return { kind: t3, elements: s5, finisher(n8) {
    customElements.define(e8, n8);
  } };
})(e7, n6);

// assets/node_modules/@lit/reactive-element/decorators/property.js
var i3 = (i4, e7) => "method" === e7.kind && e7.descriptor && !("value" in e7.descriptor) ? { ...e7, finisher(n6) {
  n6.createProperty(e7.key, i4);
} } : { kind: "field", key: Symbol(), placement: "own", descriptor: {}, originalKey: e7.key, initializer() {
  "function" == typeof e7.initializer && (this[e7.key] = e7.initializer.call(this));
}, finisher(n6) {
  n6.createProperty(e7.key, i4);
} };
function e5(e7) {
  return (n6, t3) => void 0 !== t3 ? ((i4, e8, n7) => {
    e8.constructor.createProperty(n7, i4);
  })(e7, n6, t3) : i3(e7, n6);
}

// assets/node_modules/@lit/reactive-element/decorators/base.js
var o5 = ({ finisher: e7, descriptor: t3 }) => (o6, n6) => {
  var r4;
  if (void 0 === n6) {
    const n7 = null !== (r4 = o6.originalKey) && void 0 !== r4 ? r4 : o6.key, i4 = null != t3 ? { kind: "method", placement: "prototype", key: n7, descriptor: t3(o6.key) } : { ...o6, key: n7 };
    return null != e7 && (i4.finisher = function(t4) {
      e7(t4, n7);
    }), i4;
  }
  {
    const r5 = o6.constructor;
    void 0 !== t3 && Object.defineProperty(o6, n6, t3(n6)), null == e7 || e7(r5, n6);
  }
};

// assets/node_modules/@lit/reactive-element/decorators/query-assigned-elements.js
var n5;
var e6 = null != (null === (n5 = window.HTMLSlotElement) || void 0 === n5 ? void 0 : n5.prototype.assignedElements) ? (o6, n6) => o6.assignedElements(n6) : (o6, n6) => o6.assignedNodes(n6).filter((o7) => o7.nodeType === Node.ELEMENT_NODE);
function l4(n6) {
  const { slot: l5, selector: t3 } = null != n6 ? n6 : {};
  return o5({ descriptor: (o6) => ({ get() {
    var o7;
    const r4 = "slot" + (l5 ? `[name=${l5}]` : ":not([name])"), i4 = null === (o7 = this.renderRoot) || void 0 === o7 ? void 0 : o7.querySelector(r4), s5 = null != i4 ? e6(i4, n6) : [];
    return t3 ? s5.filter((o8) => o8.matches(t3)) : s5;
  }, enumerable: true, configurable: true }) });
}

// node_modules/@floating-ui/utils/dist/floating-ui.utils.mjs
var sides = ["top", "right", "bottom", "left"];
var alignments = ["start", "end"];
var placements = /* @__PURE__ */ sides.reduce((acc, side) => acc.concat(side, side + "-" + alignments[0], side + "-" + alignments[1]), []);
var min = Math.min;
var max = Math.max;
var round = Math.round;
var floor = Math.floor;
var createCoords = (v2) => ({
  x: v2,
  y: v2
});
var oppositeSideMap = {
  left: "right",
  right: "left",
  bottom: "top",
  top: "bottom"
};
var oppositeAlignmentMap = {
  start: "end",
  end: "start"
};
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
function getAlignmentSides(placement, rects, rtl) {
  if (rtl === void 0) {
    rtl = false;
  }
  const alignment = getAlignment(placement);
  const alignmentAxis = getAlignmentAxis(placement);
  const length = getAxisLength(alignmentAxis);
  let mainAlignmentSide = alignmentAxis === "x" ? alignment === (rtl ? "end" : "start") ? "right" : "left" : alignment === "start" ? "bottom" : "top";
  if (rects.reference[length] > rects.floating[length]) {
    mainAlignmentSide = getOppositePlacement(mainAlignmentSide);
  }
  return [mainAlignmentSide, getOppositePlacement(mainAlignmentSide)];
}
function getOppositeAlignmentPlacement(placement) {
  return placement.replace(/start|end/g, (alignment) => oppositeAlignmentMap[alignment]);
}
function getOppositePlacement(placement) {
  return placement.replace(/left|right|bottom|top/g, (side) => oppositeSideMap[side]);
}
function expandPaddingObject(padding) {
  return {
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    ...padding
  };
}
function getPaddingObject(padding) {
  return typeof padding !== "number" ? expandPaddingObject(padding) : {
    top: padding,
    right: padding,
    bottom: padding,
    left: padding
  };
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
    y: y2
  } = computeCoordsFromPlacement(rects, placement, rtl);
  let statefulPlacement = placement;
  let middlewareData = {};
  let resetCount = 0;
  for (let i4 = 0; i4 < validMiddleware.length; i4++) {
    const {
      name,
      fn
    } = validMiddleware[i4];
    const {
      x: nextX,
      y: nextY,
      data,
      reset
    } = await fn({
      x: x2,
      y: y2,
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
    y2 = nextY != null ? nextY : y2;
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
          y: y2
        } = computeCoordsFromPlacement(rects, statefulPlacement, rtl));
      }
      i4 = -1;
      continue;
    }
  }
  return {
    x: x2,
    y: y2,
    placement: statefulPlacement,
    strategy,
    middlewareData
  };
};
async function detectOverflow(state, options) {
  var _await$platform$isEle;
  if (options === void 0) {
    options = {};
  }
  const {
    x: x2,
    y: y2,
    platform: platform2,
    rects,
    elements,
    strategy
  } = state;
  const {
    boundary = "clippingAncestors",
    rootBoundary = "viewport",
    elementContext = "floating",
    altBoundary = false,
    padding = 0
  } = evaluate(options, state);
  const paddingObject = getPaddingObject(padding);
  const altContext = elementContext === "floating" ? "reference" : "floating";
  const element = elements[altBoundary ? altContext : elementContext];
  const clippingClientRect = rectToClientRect(await platform2.getClippingRect({
    element: ((_await$platform$isEle = await (platform2.isElement == null ? void 0 : platform2.isElement(element))) != null ? _await$platform$isEle : true) ? element : element.contextElement || await (platform2.getDocumentElement == null ? void 0 : platform2.getDocumentElement(elements.floating)),
    boundary,
    rootBoundary,
    strategy
  }));
  const rect = elementContext === "floating" ? {
    ...rects.floating,
    x: x2,
    y: y2
  } : rects.reference;
  const offsetParent = await (platform2.getOffsetParent == null ? void 0 : platform2.getOffsetParent(elements.floating));
  const offsetScale = await (platform2.isElement == null ? void 0 : platform2.isElement(offsetParent)) ? await (platform2.getScale == null ? void 0 : platform2.getScale(offsetParent)) || {
    x: 1,
    y: 1
  } : {
    x: 1,
    y: 1
  };
  const elementClientRect = rectToClientRect(platform2.convertOffsetParentRelativeRectToViewportRelativeRect ? await platform2.convertOffsetParentRelativeRectToViewportRelativeRect({
    rect,
    offsetParent,
    strategy
  }) : rect);
  return {
    top: (clippingClientRect.top - elementClientRect.top + paddingObject.top) / offsetScale.y,
    bottom: (elementClientRect.bottom - clippingClientRect.bottom + paddingObject.bottom) / offsetScale.y,
    left: (clippingClientRect.left - elementClientRect.left + paddingObject.left) / offsetScale.x,
    right: (elementClientRect.right - clippingClientRect.right + paddingObject.right) / offsetScale.x
  };
}
function getPlacementList(alignment, autoAlignment, allowedPlacements) {
  const allowedPlacementsSortedByAlignment = alignment ? [...allowedPlacements.filter((placement) => getAlignment(placement) === alignment), ...allowedPlacements.filter((placement) => getAlignment(placement) !== alignment)] : allowedPlacements.filter((placement) => getSide(placement) === placement);
  return allowedPlacementsSortedByAlignment.filter((placement) => {
    if (alignment) {
      return getAlignment(placement) === alignment || (autoAlignment ? getOppositeAlignmentPlacement(placement) !== placement : false);
    }
    return true;
  });
}
var autoPlacement = function(options) {
  if (options === void 0) {
    options = {};
  }
  return {
    name: "autoPlacement",
    options,
    async fn(state) {
      var _middlewareData$autoP, _middlewareData$autoP2, _placementsThatFitOnE;
      const {
        rects,
        middlewareData,
        placement,
        platform: platform2,
        elements
      } = state;
      const {
        crossAxis = false,
        alignment,
        allowedPlacements = placements,
        autoAlignment = true,
        ...detectOverflowOptions
      } = evaluate(options, state);
      const placements$1 = alignment !== void 0 || allowedPlacements === placements ? getPlacementList(alignment || null, autoAlignment, allowedPlacements) : allowedPlacements;
      const overflow = await detectOverflow(state, detectOverflowOptions);
      const currentIndex = ((_middlewareData$autoP = middlewareData.autoPlacement) == null ? void 0 : _middlewareData$autoP.index) || 0;
      const currentPlacement = placements$1[currentIndex];
      if (currentPlacement == null) {
        return {};
      }
      const alignmentSides = getAlignmentSides(currentPlacement, rects, await (platform2.isRTL == null ? void 0 : platform2.isRTL(elements.floating)));
      if (placement !== currentPlacement) {
        return {
          reset: {
            placement: placements$1[0]
          }
        };
      }
      const currentOverflows = [overflow[getSide(currentPlacement)], overflow[alignmentSides[0]], overflow[alignmentSides[1]]];
      const allOverflows = [...((_middlewareData$autoP2 = middlewareData.autoPlacement) == null ? void 0 : _middlewareData$autoP2.overflows) || [], {
        placement: currentPlacement,
        overflows: currentOverflows
      }];
      const nextPlacement = placements$1[currentIndex + 1];
      if (nextPlacement) {
        return {
          data: {
            index: currentIndex + 1,
            overflows: allOverflows
          },
          reset: {
            placement: nextPlacement
          }
        };
      }
      const placementsSortedByMostSpace = allOverflows.map((d3) => {
        const alignment2 = getAlignment(d3.placement);
        return [d3.placement, alignment2 && crossAxis ? (
          // Check along the mainAxis and main crossAxis side.
          d3.overflows.slice(0, 2).reduce((acc, v2) => acc + v2, 0)
        ) : (
          // Check only the mainAxis.
          d3.overflows[0]
        ), d3.overflows];
      }).sort((a3, b2) => a3[1] - b2[1]);
      const placementsThatFitOnEachSide = placementsSortedByMostSpace.filter((d3) => d3[2].slice(
        0,
        // Aligned placements should not check their opposite crossAxis
        // side.
        getAlignment(d3[0]) ? 2 : 3
      ).every((v2) => v2 <= 0));
      const resetPlacement = ((_placementsThatFitOnE = placementsThatFitOnEachSide[0]) == null ? void 0 : _placementsThatFitOnE[0]) || placementsSortedByMostSpace[0][0];
      if (resetPlacement !== placement) {
        return {
          data: {
            index: currentIndex + 1,
            overflows: allOverflows
          },
          reset: {
            placement: resetPlacement
          }
        };
      }
      return {};
    }
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
        y: y2,
        placement,
        middlewareData
      } = state;
      const diffCoords = await convertValueToCoords(state, options);
      if (placement === ((_middlewareData$offse = middlewareData.offset) == null ? void 0 : _middlewareData$offse.placement) && (_middlewareData$arrow = middlewareData.arrow) != null && _middlewareData$arrow.alignmentOffset) {
        return {};
      }
      return {
        x: x2 + diffCoords.x,
        y: y2 + diffCoords.y,
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
  let y2 = ($2 ? round(rect.height) : rect.height) / height;
  if (!x2 || !Number.isFinite(x2)) {
    x2 = 1;
  }
  if (!y2 || !Number.isFinite(y2)) {
    y2 = 1;
  }
  return {
    x: x2,
    y: y2
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
  let y2 = (clientRect.top + visualOffsets.y) / scale.y;
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
      y2 *= iframeScale.y;
      width *= iframeScale.x;
      height *= iframeScale.y;
      x2 += left;
      y2 += top;
      currentIFrame = getWindow(currentIFrame).frameElement;
    }
  }
  return rectToClientRect({
    width,
    height,
    x: x2,
    y: y2
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
  const y2 = -scroll.scrollTop;
  if (getComputedStyle(body).direction === "rtl") {
    x2 += max(html.clientWidth, body.clientWidth) - width;
  }
  return {
    width,
    height,
    x: x2,
    y: y2
  };
}
function getViewportRect(element, strategy) {
  const win = getWindow(element);
  const html = getDocumentElement(element);
  const visualViewport = win.visualViewport;
  let width = html.clientWidth;
  let height = html.clientHeight;
  let x2 = 0;
  let y2 = 0;
  if (visualViewport) {
    width = visualViewport.width;
    height = visualViewport.height;
    const visualViewportBased = isWebKit();
    if (!visualViewportBased || visualViewportBased && strategy === "fixed") {
      x2 = visualViewport.offsetLeft;
      y2 = visualViewport.offsetTop;
    }
  }
  return {
    width,
    height,
    x: x2,
    y: y2
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
  const y2 = top * scale.y;
  return {
    width,
    height,
    x: x2,
    y: y2
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
    } catch (e7) {
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
var PopoverElement = class extends s4 {
  constructor() {
    super(...arguments);
    this.open = false;
    this.trigger = "";
    this.placement = "bottom";
    this.offsetMainAxis = 8;
    this.offsetCrossAxis = 0;
    this.offsetAlignmentAxis = 0;
  }
  firstUpdated() {
    const triggered = () => this.open ? this.destroy() : this.setup();
    this.addEventListener("close", () => this.close());
    document.querySelector(this.trigger)?.addEventListener("click", triggered);
    document.addEventListener("click", (e7) => {
      if (!this.open) {
        return;
      }
      if (document.querySelector(this.trigger)?.contains(e7.target)) {
        return;
      }
      if (!this.contains(e7.target)) {
        this.open = false;
      }
    });
    this.renderRoot.querySelectorAll(".list-menu-item").forEach((el) => {
      el.addEventListener("click", () => {
        console.log("clicked");
        setTimeout(this.close, 40);
      });
    });
  }
  close() {
    this.open = false;
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
        middleware: [
          offset({
            crossAxis: this.offsetCrossAxis,
            mainAxis: this.offsetMainAxis,
            alignmentAxis: this.offsetAlignmentAxis
          }),
          autoPlacement({
            allowedPlacements: [this.placement]
          })
        ]
      }).then(({ x: x2, y: y2 }) => {
        Object.assign(this.floatingEl[0].style, {
          left: `${x2}px`,
          top: `${y2}px`
        });
      });
    });
  }
  destroy() {
    this.open = false;
  }
  render() {
    this.floatingEl.forEach((el) => el.style.display = this.open ? "block" : "none");
    return y`
            <slot></slot>`;
  }
};
__decorateClass([
  e5({ reflect: true, type: Boolean })
], PopoverElement.prototype, "open", 2);
__decorateClass([
  e5()
], PopoverElement.prototype, "trigger", 2);
__decorateClass([
  l4({ selector: "*:first-child" })
], PopoverElement.prototype, "floatingEl", 2);
__decorateClass([
  e5()
], PopoverElement.prototype, "placement", 2);
__decorateClass([
  e5({ type: Number, attribute: "offset-main-axis" })
], PopoverElement.prototype, "offsetMainAxis", 2);
__decorateClass([
  e5({ type: Number, attribute: "offset-cross-axis" })
], PopoverElement.prototype, "offsetCrossAxis", 2);
__decorateClass([
  e5({ type: Number, attribute: "offset-alignment-axis" })
], PopoverElement.prototype, "offsetAlignmentAxis", 2);
PopoverElement = __decorateClass([
  e4("o-popover")
], PopoverElement);

// assets/node_modules/notyf/notyf.es.js
var __assign = function() {
  __assign = Object.assign || function __assign2(t3) {
    for (var s5, i4 = 1, n6 = arguments.length; i4 < n6; i4++) {
      s5 = arguments[i4];
      for (var p2 in s5)
        if (Object.prototype.hasOwnProperty.call(s5, p2))
          t3[p2] = s5[p2];
    }
    return t3;
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
      for (var i4 = 0; i4 < this.notifications.length && idx < 0; i4++) {
        if (this.notifications[i4].notification === notification) {
          idx = i4;
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
      var t3;
      for (t3 in transitions) {
        if (el.style[t3] !== void 0) {
          return transitions[t3];
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
        incomingTypes.forEach(function(t3, idx) {
          if (t3.type === defaultType.type)
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
var ToastsElement = class extends s4 {
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
    const toasts2 = JSON.parse(this.textContent || "[]");
    toasts2.forEach((toast2) => this.display(toast2));
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
  onToast(e7) {
    this.display(e7.detail);
  }
  render() {
    return null;
  }
};
__decorateClass([
  e5({ type: Number })
], ToastsElement.prototype, "duration", 2);
ToastsElement = __decorateClass([
  e4("o-toasts")
], ToastsElement);
var toasts = {
  success(message) {
    document.dispatchEvent(new CustomEvent("toast", {
      bubbles: true,
      detail: { message, category: "success" }
    }));
  },
  error(message) {
    document.dispatchEvent(new CustomEvent("toast", {
      bubbles: true,
      detail: { message, category: "error" }
    }));
  }
};

// assets/components/modals.ts
var ModalsElement = class extends s4 {
  render() {
    return y`
            <slot></slot>`;
  }
  firstUpdated() {
    window.addEventListener("modals-close", this.closeActiveModal.bind(this));
    document.body.addEventListener("htmx:afterSettle", (e7) => {
      if (!(e7 instanceof CustomEvent)) {
        return;
      }
      const target = e7.target;
      const dialog = target.querySelector("dialog[data-autoopen]");
      if (dialog) {
        dialog.addEventListener("close", () => dialog.remove());
        dialog.showModal();
      }
    });
  }
  closeActiveModal() {
    this.dialogs.forEach((el) => el.remove());
  }
};
ModalsElement.styles = i`:host {
        display: block
    }`;
__decorateClass([
  l4({ selector: "dialog" })
], ModalsElement.prototype, "dialogs", 2);
ModalsElement = __decorateClass([
  e4("o-modals")
], ModalsElement);
var modals = {
  closeActive() {
    window.dispatchEvent(new CustomEvent("modals-close"));
  }
};

// assets/js/events.ts
var events = {
  REFRESH: "refresh",
  // refresh data table
  FILTER_CHANGE: "filterchange"
  // emitted when list filter changes
};

// assets/main.ts
var admin = {
  modals,
  toasts,
  events
};
window.ohmyadmin = admin;
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

@lit/reactive-element/decorators/base.js:
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
