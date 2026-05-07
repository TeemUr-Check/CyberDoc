// INTENTIONALLY VULNERABLE — AI / training fixture only.
function merge(dst, src) {
  for (const k of Object.keys(src)) {
    if (typeof src[k] === 'object' && src[k] !== null && !Array.isArray(src[k])) {
      if (!dst[k]) dst[k] = {};
      merge(dst[k], src[k]);
    } else {
      dst[k] = src[k];
    }
  }
  return dst;
}

module.exports = { merge };
