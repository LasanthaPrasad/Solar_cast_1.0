function initMap() {
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 7,
        center: { lat: 7.873054, lng: 80.771797 }
    });

    forecastLocations.forEach(function(location) {
        var marker = new google.maps.Marker({
            position: { lat: location.latitude, lng: location.longitude },
            map: map,
            title: 'Forecast Location'
        });

        var infowindow = new google.maps.InfoWindow({
            content: `
                <h5>Forecast Location</h5>
                <p>GHI: ${parseFloat(location.next_hour_forecast.ghi).toFixed(2)}</p>
                <p>DNI: ${parseFloat(location.next_hour_forecast.dni).toFixed(2)}</p>
                <p>DHI: ${parseFloat(location.next_hour_forecast.dhi).toFixed(2)}</p>
            `
        });

        marker.addListener('click', function() {
            infowindow.open(map, marker);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initMap();
});