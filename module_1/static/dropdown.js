// Custom dropdown functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dropdowns
    const dropdowns = document.querySelectorAll('.custom-dropdown');
    
    dropdowns.forEach(dropdown => {
        const selected = dropdown.querySelector('.dropdown-selected');
        const options = dropdown.querySelector('.dropdown-options');
        const hiddenInput = dropdown.querySelector('input[type="hidden"]');
        const searchInput = dropdown.querySelector('.dropdown-search');
        const optionItems = dropdown.querySelectorAll('.dropdown-option');
        
        // Toggle dropdown
        selected.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-options').forEach(otherOptions => {
                if (otherOptions !== options) {
                    otherOptions.classList.remove('active');
                    otherOptions.previousElementSibling.classList.remove('active');
                }
            });
            
            // Toggle this dropdown
            options.classList.toggle('active');
            selected.classList.toggle('active');
            
            // Focus on search input if available
            if (options.classList.contains('active') && searchInput) {
                setTimeout(() => {
                    searchInput.focus();
                }, 100);
            }
        });
        
        // Select option
        optionItems.forEach(option => {
            option.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const text = this.textContent;
                
                // Update selected text
                selected.querySelector('span').textContent = text;
                
                // Update hidden input value
                hiddenInput.value = value;
                
                // Mark as selected
                optionItems.forEach(item => item.classList.remove('selected'));
                this.classList.add('selected');
                
                // Close dropdown
                options.classList.remove('active');
                selected.classList.remove('active');
            });
        });
        
        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                
                optionItems.forEach(option => {
                    const text = option.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        option.style.display = 'block';
                    } else {
                        option.style.display = 'none';
                    }
                });
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target)) {
                options.classList.remove('active');
                selected.classList.remove('active');
            }
        });
        
        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && options.classList.contains('active')) {
                options.classList.remove('active');
                selected.classList.remove('active');
            }
        });
    });
    
    // Set default values if needed
    function setDefaultDropdownValues() {
        const experienceDropdown = document.getElementById('experience-dropdown');
        const goalDropdown = document.getElementById('goal-dropdown');
        const injuryDropdown = document.getElementById('injury-dropdown');
        
        // Set first option as default if exists
        if (experienceDropdown) {
            const firstOption = experienceDropdown.querySelector('.dropdown-option');
            if (firstOption) {
                firstOption.click();
            }
        }
        
        if (goalDropdown) {
            const firstOption = goalDropdown.querySelector('.dropdown-option');
            if (firstOption) {
                firstOption.click();
            }
        }
        
        if (injuryDropdown) {
            const firstOption = injuryDropdown.querySelector('.dropdown-option');
            if (firstOption) {
                firstOption.click();
            }
        }
    }
    
    // Set default values after a short delay to ensure DOM is fully loaded
    setTimeout(setDefaultDropdownValues, 100);
});