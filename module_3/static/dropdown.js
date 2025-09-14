// Custom dropdown functionality
document.addEventListener('DOMContentLoaded', function() {
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
            document.querySelectorAll('.dropdown-options').forEach(otherOptions => {
                if (otherOptions !== options) {
                    otherOptions.classList.remove('active');
                    otherOptions.previousElementSibling.classList.remove('active');
                }
            });
            options.classList.toggle('active');
            selected.classList.toggle('active');
            if (options.classList.contains('active') && searchInput) {
                setTimeout(() => searchInput.focus(), 100);
            }
        });

        // Select option
        optionItems.forEach(option => {
            option.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const text = this.textContent;
                selected.querySelector('span').textContent = text;
                hiddenInput.value = value;
                optionItems.forEach(item => item.classList.remove('selected'));
                this.classList.add('selected');
                options.classList.remove('active');
                selected.classList.remove('active');
            });
        });

        // Search filter
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                optionItems.forEach(option => {
                    const text = option.textContent.toLowerCase();
                    option.style.display = text.includes(searchTerm) ? "block" : "none";
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
    });
});
