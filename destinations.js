$(document).ready(function() {
    function loadDestinations() {
        $.ajax({
            url: 'http://localhost:5000/api/destinations',
            method: 'GET',
            success: function(destinations) {
                const $select = $('#destination-select');
                $select.empty().append('<option value="">Destination</option>');
                
                destinations.forEach(function(destination) {
                    $select.append($('<option>', {
                        value: destination.id,
                        text: destination.name
                    }));
                });
            },
            error: function(xhr, status, error) {
                console.error('Error loading destinations:', error);
            }
        });
    }
    loadDestinations();
});

function subscribeToPromotion() {
    const email = prompt("Please enter your email to receive promotions:");
    
    if (email) {
        $.ajax({
            url: 'http://localhost:5000/queue/interesse-promocoes',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 
                email: email,
                timestamp: new Date().toISOString()
            }),
            success: function(response) {
                alert('Thank you! You have been subscribed to our promotions.');
            },
            error: function(xhr, status, error) {
                alert('Error subscribing: ' + error);
            }
        });
    }
}