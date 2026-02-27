({ lat, lng }) => {
    const map = document.querySelector('[data-map]') ||
               document.querySelector('#map') ||
               document.querySelector('.map');
    if (!map) return false;

    // تلاش برای یافتن نمونه Google Maps
    const mapsInstance = google.maps.Map.getMap(map) ||
                        map.__gm ||
                        map._map;

    if (mapsInstance) {
        const latLng = new google.maps.LatLng(lat, lng);
        mapsInstance.setCenter(latLng);
        mapsInstance.setZoom(15);

        // شبیه‌سازی رویداد کلیک
        google.maps.event.trigger(mapsInstance, 'click', {
            latLng: latLng,
            pixel: mapsInstance.getProjection().fromLatLngToPoint(latLng)
        });
        return true;
    }
    return false;
}
