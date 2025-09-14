let localStream = null;
let socket = null;
let statsInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const video = document.getElementById('video');
    const feedback = document.getElementById('feedback');
    
    // Connect to Socket.IO
    socket = io({
        query: {
            session_id: sessionId
        }
    });
    
    socket.on('connected', function(data) {
        console.log('Connected to server:', data);
        feedback.textContent = 'Connected to server';
        feedback.className = 'feedback-badge alert alert-success';
    });
    
    socket.on('processed_frame', function(data) {
        // Update video frame
        video.src = data.image;
        
        // Update stats
        updateStats(data.stats);
    });
    
    socket.on('disconnect', function() {
        feedback.textContent = 'Disconnected from server';
        feedback.className = 'feedback-badge alert alert-danger';
    });
    
    startButton.addEventListener('click', async function() {
        try {
            // Get user media
            localStream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 1280, height: 720 }, 
                audio: false 
            });
            
            video.srcObject = localStream;
            startButton.disabled = true;
            stopButton.disabled = false;
            feedback.textContent = 'Streaming started';
            feedback.className = 'feedback-badge alert alert-success';
            
            // Start sending frames
            startSendingFrames();
            
            // Start stats update interval
            statsInterval = setInterval(updateStatsFromServer, 1000);
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            feedback.textContent = 'Error accessing camera: ' + error.message;
            feedback.className = 'feedback-badge alert alert-danger';
        }
    });
    
    stopButton.addEventListener('click', function() {
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        
        if (statsInterval) {
            clearInterval(statsInterval);
            statsInterval = null;
        }
        
        startButton.disabled = false;
        stopButton.disabled = true;
        feedback.textContent = 'Streaming stopped';
        feedback.className = 'feedback-badge alert alert-warning';
    });
    
    // Handle page unload
    window.addEventListener('beforeunload', function() {
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }
        if (socket) {
            socket.disconnect();
        }
    });
});

function startSendingFrames() {
    const video = document.getElementById('video');
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = 640;  // Reduced resolution for performance
    canvas.height = 480;
    
    function captureFrame() {
        if (!localStream) return;
        
        try {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/jpeg', 0.7);
            
            // Send frame to server
            socket.emit('frame', { image: imageData });
            
            // Continue capturing
            requestAnimationFrame(captureFrame);
        } catch (error) {
            console.error('Error capturing frame:', error);
        }
    }
    
    // Start capturing frames
    captureFrame();
}

function updateStats(stats) {
    document.getElementById('total-punches').textContent = stats.total_punches;
    document.getElementById('accuracy').textContent = stats.accuracy + '%';
    document.getElementById('guard-warnings').textContent = stats.guard_warnings;
    document.getElementById('session-time').textContent = stats.session_duration + 's';
    document.getElementById('punch-rate').textContent = stats.punches_per_minute;
    
    document.getElementById('jab-count').textContent = stats.punch_counts.Jab;
    document.getElementById('cross-count').textContent = stats.punch_counts.Cross;
    document.getElementById('hook-count').textContent = stats.punch_counts.Hook;
    document.getElementById('uppercut-count').textContent = stats.punch_counts.Uppercut;
    
    // Highlight new punches
    if (stats.total_punches > parseInt(document.getElementById('total-punches').textContent || 0)) {
        document.getElementById('stats-container').classList.add('punch-highlight');
        setTimeout(() => {
            document.getElementById('stats-container').classList.remove('punch-highlight');
        }, 1000);
    }
}

function updateStatsFromServer() {
    fetch('/stats')
        .then(response => response.json())
        .then(updateStats)
        .catch(error => console.error('Error fetching stats:', error));
}
// Guard Perfection Chart - Gauge style
const guardCtx = document.getElementById('guardChart').getContext('2d');
new Chart(guardCtx, {
    type: 'doughnut',
    data: {
        labels: ['Perfect Guard', 'Needs Improvement'],
        datasets: [{
            data: [stats.guard_perfection, 100 - stats.guard_perfection],
            backgroundColor: ['#28a745', '#dc3545'],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
            legend: {
                position: 'bottom'
            },
            title: {
                display: true,
                text: `Guard Score: ${stats.guard_perfection}%`
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.label}: ${context.raw.toFixed(1)}%`;
                    }
                }
            }
        }
    }
});