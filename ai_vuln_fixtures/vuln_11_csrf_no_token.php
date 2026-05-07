<?php
// INTENTIONALLY VULNERABLE — AI / training fixture only.
session_start();
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'] ?? '';
    mail($email, 'Reset', 'Click here to reset');
    echo 'Sent';
}
?>
<form method="post"><input name="email"><button>Send</button></form>
