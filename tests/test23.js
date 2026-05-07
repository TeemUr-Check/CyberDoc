// INTENTIONALLY VULNERABLE — AI / training fixture only.
const crypto = require('crypto');

function sign(data, secret) {
  const h = crypto.createHash('md5');
  h.update(secret + data);
  return h.digest('hex');
}

module.exports = { sign };
