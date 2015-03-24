<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SayIt :: Modern parliament debates</title>
    <meta property="og:image" content="//nrsr.sk.sayit.parldata.eu/static/speeches/img/apple-touch-icon-152x152.png">
    <meta property="og:image:type" content="image/png">
    <meta property="og:image:width" content="152">
    <meta property="og:image:height" content="152">
    <link href='//fonts.googleapis.com/css?family=Source+Sans+Pro:400,300&subset=latin,latin-ext' rel='stylesheet' type='text/css'>
    <style>
        body {
            text-align: center;
            line-height: 150%;
            font-family: "Source Sans Pro", "Helvetica Neue", Arial, "Helvetica", Helvetica, sans-serif;
            color: #222;
        }
        h1 { font-weight: 300; font-size: 36px; margin-top: 1em; }
        a { text-decoration: none; color: #e14a55; }
        p { margin: 1em 0 1.5em }
        .instance-list { list-style-type: none; padding-left: 0 }
    </style>
</head>

<body>

<h1>Modern parliament debates</h1>

<p class="description">
Transcripts of parliament debates for 21<sup>st</sup> century.<br>
Readable, searchable, linkable.<br>
Thanks to <a href="//sayit.mysociety.org">SayIt</a>.
</p>

<?php
$subdomains_dir = '/home/projects/sayit/subdomains';
$dir = new DirectoryIterator($subdomains_dir);
foreach ($dir as $fileinfo) {
    if (!$fileinfo->isDot()) {
        $files[] = $fileinfo->getFilename();
    }
}

sort($files);

echo "<ul class=\"instance-list\">\n";

foreach ($files as $file) {
    if ($file[0] == '_') continue;
    $content = file_get_contents($subdomains_dir.'/'.$file);
    preg_match("/COUNTRY_CODE\\s*=\\s*['\"](.*)['\"]/u", $content, $ccode);
    preg_match("/PARLIAMENT_CODE\\s*=\\s*['\"](.*)['\"]/u", $content, $pcode);
    preg_match("/PARLIAMENT_NAME\\s*=\\s*['\"](.*)['\"]/u", $content, $pname);
    echo "\t<li><a href=\"//{$pcode[1]}.{$ccode[1]}.sayit.parldata.eu\">${pname[1]}</a></li>\n";
}

echo "</ul>\n";
?>

</body>
</html>
