// INTENTIONALLY VULNERABLE — AI / training fixture only.
const { exec } = require('child_process');

function runTool(arg) {
  exec(`convert ${arg} out.png`, (err, stdout) => console.log(stdout));
}

module.exports = { runTool };
