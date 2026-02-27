() => {
    // تلاش برای Google Maps
    if (typeof google !== 'undefined' && google.maps) {
        const map = document.querySelector('#map');
        if (map && map._map) {
            const center = map._map.getCenter();
            return {
                lat: center.lat(),
                lng: center.lng()
            };
        }
    }

    // تلاش برای استخراج از URL
    const url = window.location.href;
    const match = url.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
    if (match) {
        return {
            lat: parseFloat(match[1]),
            lng: parseFloat(match[2])
        };
    }

    return null;
}
