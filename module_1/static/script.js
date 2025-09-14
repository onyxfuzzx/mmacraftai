// Update slider values in real-time
document.addEventListener('DOMContentLoaded', function() {
    // Get all sliders
    const ageSlider = document.getElementById('age');
    const heightSlider = document.getElementById('height');
    const weightSlider = document.getElementById('weight');
    
    // Get all value displays
    const ageValue = document.getElementById('age-value');
    const heightValue = document.getElementById('height-value');
    const weightValue = document.getElementById('weight-value');
    
    // Update values on input
    ageSlider.addEventListener('input', function() {
        ageValue.textContent = this.value;
        calculateBMI();
    });
    
    heightSlider.addEventListener('input', function() {
        heightValue.textContent = this.value;
        calculateBMI();
    });
    
    weightSlider.addEventListener('input', function() {
        weightValue.textContent = this.value;
        calculateBMI();
    });
    
    // Calculate BMI function
    function calculateBMI() {
        const height = parseInt(heightSlider.value) / 100; // convert to meters
        const weight = parseInt(weightSlider.value);
        const bmi = weight / (height * height);
        
        document.getElementById('bmi-value').textContent = bmi.toFixed(1);
        
        // Update BMI bar
        let bmiPercentage;
        if (bmi < 18.5) {
            bmiPercentage = (bmi / 18.5) * 25;
        } else if (bmi < 25) {
            bmiPercentage = 25 + ((bmi - 18.5) / 6.5) * 25;
        } else if (bmi < 30) {
            bmiPercentage = 50 + ((bmi - 25) / 5) * 25;
        } else {
            bmiPercentage = 75 + Math.min(((bmi - 30) / 10) * 25, 25);
        }
        
        document.getElementById('bmi-fill').style.width = `${bmiPercentage}%`;
    }
    
    // Form submission
    document.getElementById('prediction-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get values from the new dropdowns
        const experience = document.getElementById('experience').value;
        const goal = document.getElementById('goal').value;
        const injury_history = document.getElementById('injury_history').value;
        
        // Validate that all dropdowns have values
        if (!experience || !goal || !injury_history) {
            alert('Please select values for all dropdown fields');
            return;
        }
        
        // Show loading state
        const submitBtn = document.querySelector('.submit-btn');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        submitBtn.disabled = true;
        
        // Get form data
        const formData = {
            age: document.getElementById('age').value,
            height: document.getElementById('height').value,
            weight: document.getElementById('weight').value,
            experience: experience,
            goal: goal,
            injury_history: injury_history
        };
        
        // Send AJAX request
        fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            // Display results
            document.getElementById('result-bmi').textContent = data.bmi;
            document.getElementById('result-cardio').textContent = data.cardio + ' sessions/month';
            document.getElementById('result-skill').textContent = data.skill + ' sessions/month';
            document.getElementById('result-strength').textContent = data.strength + ' sessions/month';
            document.getElementById('result-agility').textContent = data.agility + ' sessions/month';
            document.getElementById('result-recovery').textContent = data.recovery + ' sessions/month';
            document.getElementById('result-duration').textContent = data.duration + ' months';
            
            // Show results card
            document.getElementById('results').style.display = 'block';
            
            // Scroll to results
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
            
            // Reset button
            submitBtn.innerHTML = '<i class="fas fa-dumbbell"></i> Generate Training Plan';
            submitBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            
            // Reset button
            submitBtn.innerHTML = '<i class="fas fa-dumbbell"></i> Generate Training Plan';
            submitBtn.disabled = false;
        });
    });
    
    // Initial BMI calculation
    calculateBMI();
});

// Reset form function
function resetForm() {
    // Reset dropdowns to their first option
    const dropdowns = document.querySelectorAll('.custom-dropdown');
    dropdowns.forEach(dropdown => {
        const firstOption = dropdown.querySelector('.dropdown-option');
        if (firstOption) {
            firstOption.click();
        }
    });
    
    document.getElementById('results').style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}