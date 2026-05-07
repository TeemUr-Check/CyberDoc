<?php
// INTENTIONALLY VULNERABLE — AI / training fixture only.
$id = $_GET['id'];
$mysqli->query("SELECT * FROM orders WHERE id = $id");
