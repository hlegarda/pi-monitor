from flask import Flask, render_template_string, jsonify
import psutil
import subprocess
import time
import os

app = Flask(__name__)

last_net = psutil.net_io_counters()
last_time = time.time()

HTML = """
<!doctype html>
<html>
<head>
    <title>Hanzel's Cloud Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1e1e2f;
            color: #eee;
            margin: 0;
            padding: 0;
        }
        h1 {
            color: #4cafef;
            text-align: center;
            margin: 15px 0 5px;
        }
        #statusIndicator {
            text-align: center;
            font-size: 1.3rem;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .status-green { color: lime; }
        .status-yellow { color: orange; }
        .status-red { color: red; }
        .summary-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            padding: 15px 20px;
            max-width: 1400px;
            margin: auto;
        }
        .summary-card {
            background: #2e2e40;
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .summary-title {
            font-size: 0.9rem;
            color: #bbb;
            margin-bottom: 5px;
        }
        .summary-value {
            font-size: 1.4rem;
            font-weight: bold;
            transition: color 0.3s;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: auto;
        }
        .chart-card {
            background: #2e2e40;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        canvas {
            width: 100% !important;
            height: 250px !important;
        }
    </style>
</head>
<body>
    <h1>Hanzel's Cloud Monitor</h1>
    <div id="statusIndicator" class="status-green">🟢 Healthy</div>

    <div class="summary-bar">
        <div class="summary-card">
            <div class="summary-title">CPU Usage</div>
            <div class="summary-value" id="cpuSummary">--%</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">Temperature</div>
            <div class="summary-value" id="tempSummary">-- °C</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">Memory</div>
            <div class="summary-value" id="memSummary">--%</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">Disk</div>
            <div class="summary-value" id="diskSummary">--%</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">Net Upload</div>
            <div class="summary-value" id="netUpSummary">-- KB/s</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">Net Download</div>
            <div class="summary-value" id="netDownSummary">-- KB/s</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">USB / Secondary</div>
            <div class="summary-value" id="secondaryDisksSummary">--%</div>
        </div>
    </div>

    <div class="charts-grid">
        <div class="chart-card"><canvas id="cpuChart"></canvas></div>
        <div class="chart-card"><canvas id="tempChart"></canvas></div>
        <div class="chart-card"><canvas id="memChart"></canvas></div>
        <div class="chart-card"><canvas id="diskChart"></canvas></div>
        <div class="chart-card"><canvas id="netChart"></canvas></div>
        <div class="chart-card"><canvas id="secondaryDiskChart"></canvas></div>
    </div>

    <script>
        const labels = [];
        const cpuData = [], tempData = [], memData = [], diskData = [], netUpData = [], netDownData = [];
        const secondaryDiskData = {};

        function createChart(ctx, datasets) {
            return new Chart(ctx, {
                type: 'line',
                data: { labels: labels, datasets: datasets },
                options: {
                    responsive: true,
                    animation: false,
                    plugins: { legend: { labels: { color: '#eee' } } },
                    scales: {
                        x: { ticks: { color: '#bbb' }, grid: { color: '#444' } },
                        y: { beginAtZero: true, ticks: { color: '#bbb' }, grid: { color: '#444' } }
                    }
                }
            });
        }

        const cpuChart = createChart(document.getElementById('cpuChart'), [
            { label: "CPU (%)", data: cpuData, borderColor: 'cyan', backgroundColor: 'rgba(0,255,255,0.2)', fill: true, tension: 0.3 }
        ]);
        const tempChart = createChart(document.getElementById('tempChart'), [
            { label: "Temp (°C)", data: tempData, borderColor: 'orange', backgroundColor: 'rgba(255,165,0,0.2)', fill: true, tension: 0.3 }
        ]);
        const memChart = createChart(document.getElementById('memChart'), [
            { label: "Memory (%)", data: memData, borderColor: 'lime', backgroundColor: 'rgba(0,255,0,0.2)', fill: true, tension: 0.3 }
        ]);
        const diskChart = createChart(document.getElementById('diskChart'), [
            { label: "Disk (%)", data: diskData, borderColor: 'magenta', backgroundColor: 'rgba(255,0,255,0.2)', fill: true, tension: 0.3 }
        ]);
        const netChart = createChart(document.getElementById('netChart'), [
            { label: "Upload (KB/s)", data: netUpData, borderColor: 'red', backgroundColor: 'rgba(255,0,0,0.2)', fill: true, tension: 0.3 },
            { label: "Download (KB/s)", data: netDownData, borderColor: 'blue', backgroundColor: 'rgba(0,0,255,0.2)', fill: true, tension: 0.3 }
        ]);
        const secondaryDiskChartCtx = document.getElementById("secondaryDiskChart");
        let secondaryDiskChart = null;

        function setColor(element, value, type) {
            let color = "#4cafef"; // default
            if (type === "cpu" || type === "mem" || type === "disk") {
                if (value <= 60) color = "lime";
                else if (value <= 85) color = "orange";
                else color = "red";
            } else if (type === "temp") {
                if (value <= 60) color = "lime";
                else if (value <= 75) color = "orange";
                else color = "red";
            } else if (type === "net") {
                color = "deepskyblue";
            }
            element.style.color = color;
            return color;
        }

        function updateSecondaryDisks(disks) {
            const secondaryDisksEl = document.getElementById("secondaryDisksSummary");
            if (disks.length === 0) {
                secondaryDisksEl.innerText = "N/A";
                secondaryDisksEl.style.color = "#4cafef";
                return;
            }
            let display = disks.map(d => `${d.mount}: ${d.percent}%`).join(" | ");
            secondaryDisksEl.innerText = display;

            let maxUsage = Math.max(...disks.map(d => d.percent));
            if (maxUsage <= 60) secondaryDisksEl.style.color = "lime";
            else if (maxUsage <= 85) secondaryDisksEl.style.color = "orange";
            else secondaryDisksEl.style.color = "red";

            const timeLabel = new Date().toLocaleTimeString();

            // initialize chart
            if (!secondaryDiskChart) {
                disks.forEach(d => secondaryDiskData[d.mount] = []);
                const datasets = disks.map((d, i) => ({
                    label: d.mount,
                    data: secondaryDiskData[d.mount],
                    borderColor: `hsl(${i*60},70%,50%)`,
                    backgroundColor: `hsla(${i*60},70%,50%,0.2)`,
                    fill: true,
                    tension: 0.3
                }));
                secondaryDiskChart = new Chart(secondaryDiskChartCtx, {
                    type: 'line',
                    data: { labels: [], datasets: datasets },
                    options: {
                        responsive: true,
                        animation: false,
                        plugins: { legend: { labels: { color: '#eee' } } },
                        scales: {
                            x: { ticks: { color: '#bbb' }, grid: { color: '#444' } },
                            y: { beginAtZero: true, ticks: { color: '#bbb' }, grid: { color: '#444' } }
                        }
                    }
                });
            }

            if (secondaryDiskChart.data.labels.length > 30) {
                secondaryDiskChart.data.labels.shift();
                Object.values(secondaryDiskData).forEach(arr => arr.shift());
            }
            secondaryDiskChart.data.labels.push(timeLabel);

            disks.forEach((d, i) => {
                if (!(d.mount in secondaryDiskData)) secondaryDiskData[d.mount] = [];
                secondaryDiskData[d.mount].push(d.percent);
                secondaryDiskChart.data.datasets[i].data = secondaryDiskData[d.mount];
            });

            secondaryDiskChart.update();
        }

        async function fetchData() {
            const res = await fetch('/stats');
            const data = await res.json();
            const timeLabel = new Date().toLocaleTimeString();

            if (labels.length > 30) {
                labels.shift();
                cpuData.shift(); tempData.shift(); memData.shift();
                diskData.shift(); netUpData.shift(); netDownData.shift();
            }

            labels.push(timeLabel);
            cpuData.push(data.cpu_usage);
            tempData.push(data.temperature);
            memData.push(data.mem_percent);
            diskData.push(data.disk_percent);
            netUpData.push(data.net_upload);
            netDownData.push(data.net_download);

            cpuChart.update(); tempChart.update(); memChart.update();
            diskChart.update(); netChart.update();

            const cpuEl = document.getElementById("cpuSummary");
            const tempEl = document.getElementById("tempSummary");
            const memEl = document.getElementById("memSummary");
            const diskEl = document.getElementById("diskSummary");
            const netUpEl = document.getElementById("netUpSummary");
            const netDownEl = document.getElementById("netDownSummary");

            let colors = [];
            colors.push(setColor(cpuEl, data.cpu_usage, "cpu"));
            colors.push(setColor(tempEl, data.temperature, "temp"));
            colors.push(setColor(memEl, data.mem_percent, "mem"));
            colors.push(setColor(diskEl, data.disk_percent, "disk"));
            setColor(netUpEl, data.net_upload, "net");
            setColor(netDownEl, data.net_download, "net");

            cpuEl.innerText = data.cpu_usage + "%";
            tempEl.innerText = data.temperature + " °C";
            memEl.innerText = data.mem_percent + "%";
            diskEl.innerText = data.disk_percent + "%";
            netUpEl.innerText = data.net_upload + " KB/s";
            netDownEl.innerText = data.net_download + " KB/s";

            // --- Update secondary disks ---
            updateSecondaryDisks(data.secondary_disks);

            // --- Update status indicator ---
            const statusEl = document.getElementById("statusIndicator");
            if (colors.includes("red")) {
                statusEl.innerHTML = "🔴 Critical";
                statusEl.className = "status-red";
            } else if (colors.includes("orange")) {
                statusEl.innerHTML = "🟡 Under Load";
                statusEl.className = "status-yellow";
            } else {
                statusEl.innerHTML = "🟢 Healthy";
                statusEl.className = "status-green";
            }
        }

        setInterval(fetchData, 2000);
    </script>
</body>
</html>
"""

def get_temperature():
    try:
        output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(output.replace("temp=", "").replace("'C\n", ""))
    except Exception:
        temps = psutil.sensors_temperatures()
        if "cpu_thermal" in temps:
            return temps["cpu_thermal"][0].current
        return None

def get_secondary_disks():
    """Return usage stats for all mounted drives under /mnt."""
    disks = []
    if os.path.exists("/mnt"):
        for entry in os.scandir("/mnt"):
            if entry.is_dir(follow_symlinks=False):
                mountpoint = entry.path
                try:
                    usage = psutil.disk_usage(mountpoint)
                    disks.append({
                        "mount": mountpoint,
                        "percent": usage.percent
                    })
                except PermissionError:
                    continue  # skip if inaccessible
    return disks

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/stats")
def stats():
    global last_net, last_time
    cpu_usage = psutil.cpu_percent(interval=0.5)
    temp = get_temperature() or 0
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    current_net = psutil.net_io_counters()
    current_time = time.time()
    elapsed = current_time - last_time

    upload_speed = (current_net.bytes_sent - last_net.bytes_sent) / 1024 / elapsed
    download_speed = (current_net.bytes_recv - last_net.bytes_recv) / 1024 / elapsed

    last_net = current_net
    last_time = current_time

    secondary_disks = get_secondary_disks()

    return jsonify(
        cpu_usage=round(cpu_usage, 1),
        temperature=round(temp, 1),
        mem_percent=mem.percent,
        disk_percent=disk.percent,
        net_upload=round(upload_speed, 1),
        net_download=round(download_speed, 1),
        secondary_disks=secondary_disks,
        timestamp=time.time()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=False)
