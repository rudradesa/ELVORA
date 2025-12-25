    <?php

require 'conn.php'; // Make sure you have the proper connection settings in this file.



$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

if(isset($_POST['submit'])){
    $user_id = intval($_POST['user_id']);
    $url = $_POST['url'];
    $hours = intval($_POST['hours']);
    $minutes = intval($_POST['minutes']);
    
    
    $total_seconds = ($hours * 3600) + ($minutes * 60);
    
    
    $daily_limit = date('Y-m-d H:i:s', strtotime("2000-01-01 00:00:00 + $total_seconds seconds"));
    
    
    $today = date('Y-m-d');
    $sql = "SELECT * FROM user_usage WHERE ul_id=$user_id AND url='$url' AND DATE(last_reset)='$today'";
    $result = $conn->query($sql);
    
    if($result->num_rows > 0){
        $conn->query("UPDATE user_usage SET daily_limit='$daily_limit' WHERE ul_id=$user_id AND url='$url' AND DATE(last_reset)='$today'");
    } else {
        $now = date('Y-m-d H:i:s');
        $conn->query("INSERT INTO user_usage (ul_id, url, current_usage, last_reset, daily_limit) VALUES ($user_id,'$url','2000-01-01 00:00:00','$now','$daily_limit')");
    }
    
    echo "Daily limit set successfully!";
}

?>

<form method="POST">
    User ID: <input type="number" name="user_id" required><br>
    URL: <input type="text" name="url" required><br>
    Hours: <input type="number" name="hours" min="0" value="0"><br>
    Minutes: <input type="number" name="minutes" min="0" max="59" value="30"><br>
    <input type="submit" name="submit" value="Set Daily Limit">
</form>