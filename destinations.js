document.addEventListener('DOMContentLoaded', function() {
    const destinationSelect = document.getElementById('destination-select');
    
    fetch('http://localhost:5000/api/destinations')
        .then(response => response.json())
        .then(destinations => {
            destinationSelect.innerHTML = '<option value="">Destination</option>';
            destinations.forEach(destination => {
                const option = document.createElement('option');
                option.value = destination.id;
                option.textContent = destination.name;
                destinationSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading destinations:', error));
    });