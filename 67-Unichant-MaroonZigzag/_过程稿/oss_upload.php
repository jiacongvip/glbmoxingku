<?php
$file = $argv[1] ?? '';
if ($file === '' || !is_file($file)) { fwrite(STDERR, "missing file\n"); exit(1); }
require '/app/vendor/autoload.php';
$mysqli = new mysqli('tpdaxiangshop_mysql', 'root', 'root123456', 'tpdaxiangshop');
if ($mysqli->connect_errno) { fwrite(STDERR, $mysqli->connect_error."\n"); exit(2); }
$res = $mysqli->query("SELECT value FROM ddwx_sysset WHERE name='remote' LIMIT 1");
$row = $res->fetch_row();
$sys = json_decode($row[0], true);
$q = $sys['qiniu'] ?? [];
$ak = $q['accesskey'] ?? ''; $sk = $q['secretkey'] ?? ''; $bucket = $q['bucket'] ?? '';
$domain = rtrim($q['url'] ?? ($q['domain'] ?? ''), '/');
if ($ak===''||$sk===''||$bucket===''||$domain==='') { fwrite(STDERR, "qiniu incomplete\n"); exit(3); }
$ext = pathinfo($file, PATHINFO_EXTENSION) ?: 'png';
$object = 'upload/'.date('Ym').'/'.date('d_His').mt_rand(1000,9999).'.'.$ext;
$auth = new Qiniu\Auth($ak, $sk);
$token = $auth->uploadToken($bucket);
$uploadMgr = new Qiniu\Storage\UploadManager();
list($ret, $err) = $uploadMgr->putFile($token, $object, $file);
if ($err !== null) {
  $msg = method_exists($err,'message') ? $err->message() : json_encode($err);
  fwrite(STDERR, "upload fail: $msg\n"); exit(4);
}
echo $domain.'/'.$object."\n";
