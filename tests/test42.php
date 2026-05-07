<?php
// INTENTIONALLY VULNERABLE — AI / training fixture only.
session_start();
if (isset($_GET['sid'])) {
    session_id($_GET['sid']);
    session_start();
}
