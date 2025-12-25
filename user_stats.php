<?php
require 'conn.php'; // Make sure you have the proper connection settings in this file.
$user_id = 1;

$sql = "
SELECT 
    url,
    TIME_TO_SEC(TIMEDIFF(current_usage, '2000-01-01 00:00:00')) AS seconds
FROM user_usage
WHERE ul_id = $user_id
AND DATE(last_reset) = CURDATE()
";

$result = $conn->query($sql);

$labels = [];
$data = [];

while ($row = $result->fetch_assoc()) {
    $labels[] = parse_url($row['url'], PHP_URL_HOST);
    $data[] = round($row['seconds'] / 60, 2);
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>ELVORA – Screen Time Dashboard</title>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <!-- Google Font -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">

    <style>
        body {
            margin: 0;
            background: #0f172a;
            font-family: 'Poppins', sans-serif;
            color: #e5e7eb;
        }

        .container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 30px;
            background: #020617;
            border-radius: 16px;
            box-shadow: 0 0 40px rgba(0,0,0,0.8);
        }

        h2 {
            text-align: center;
            margin-bottom: 25px;
            font-weight: 600;
            color: #38bdf8;
        }

        canvas {
            padding: 20px;
        }

        footer {
            text-align: center;
            margin-top: 20px;
            font-size: 13px;
            color: #94a3b8;
        }
    </style>
</head>
<body>

<div class="container">
    <h2>📊 Today’s Screen Time Usage</h2>
    <canvas id="usageChart"></canvas>
    <footer>ELVORA – Smart Screen Time Monitor</footer>
</div>

<script>
const ctx = document.getElementById('usageChart').getContext('2d');

new Chart(ctx, {
    type: 'bar',
    data: {
        labels: <?php echo json_encode($labels); ?>,
        datasets: [{
            label: 'Time Spent (minutes)',
            data: <?php echo json_encode($data); ?>,
            backgroundColor: [
                '#38bdf8',
                '#fb7185',
                '#f97316',
                '#84cc16',
                '#a78bfa',
                '#22c55e'
            ],
            borderRadius: 12,
            barThickness: 50
        }]
    },
   options: {
    responsive: true,
    animation: {
        duration: 1500,
        easing: 'easeOutQuart'
    },
    plugins: {
        legend: {
            labels: {
                color: '#e5e7eb',
                font: { size: 14 }
            }
        },
        tooltip: {
            callbacks: {
                label: function(context) {
                    return context.parsed.y + " minutes";
                }
            }
        }
    },
    scales: {
        x: {
            ticks: {
                color: '#cbd5f5',
                font: { size: 13 }
            },
            grid: {
                display: false
            }
        },
        y: {
            beginAtZero: true,
            ticks: {
                color: '#cbd5f5',
                font: { size: 13 }
            },
            grid: {
                color: 'rgba(255,255,255,0.05)'
            }
        }
    }
}

});
</script>

</body>
</html>