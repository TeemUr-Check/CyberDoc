// INTENTIONALLY VULNERABLE — AI / training fixture only.
const { MongoClient } = require('mongodb');

async function login(db, username, password) {
  const q = { username: username, password: password };
  return db.collection('users').findOne(q);
}

module.exports = { login };
