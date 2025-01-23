let map;
let marker;
let geocoder;

// Initialize Map for Profile Page
async function initMapTwo() {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    geocoder = new google.maps.Geocoder();
    const initialAddress = initialLocation;
    geocoder.geocode({ 'address': initialAddress }, function(results, status) {
        if (status === 'OK') {
            const location = results[0].geometry.location;
            map = new google.maps.Map(document.getElementById('map'), {
                center: location,
                zoom: 14,
                mapId: 'YOUR_MAP_ID'  // Replace with your actual Map ID
            });
            marker = new AdvancedMarkerElement({
                position: location,
                map: map,
                gmpDraggable: true
            });

            document.getElementById('location').value = results[0].formatted_address;

            // Update address input when marker is dragged
            marker.addListener('dragend', function() {
                geocoder.geocode({ 'location': marker.position }, function(results, status) {
                    if (status === 'OK') {
                        if (results[0]) {
                            document.getElementById('location').value = results[0].formatted_address;
                        }
                    }
                });
            });

            // Allow clicking on the map to move the marker
            map.addListener('click', function(event) {
                marker.position = event.latLng;
                geocoder.geocode({ 'location': event.latLng }, function(results, status) {
                    if (status === 'OK') {
                        if (results[0]) {
                            document.getElementById('location').value = results[0].formatted_address;
                        }
                    }
                });
            });
        } else {
            alert('Geocode was not successful for the following reason: ' + status);
        }
    });
}
