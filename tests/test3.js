// INTENTIONALLY VULNERABLE — AI / training fixture only.
const express = require('express');
const app = express();

app.get('/hello', (req, res) => {
  const name = req.query.name || 'guest';
  res.send('<h1>Hello ' + name + '</h1>');
});

app.listen(3000);
