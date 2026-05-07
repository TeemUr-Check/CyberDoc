<?php
// INTENTIONALLY VULNERABLE — AI / training fixture only.
if ($_FILES['f']) {
    move_uploaded_file($_FILES['f']['tmp_name'], '/var/www/uploads/' . $_FILES['f']['name']);
}
