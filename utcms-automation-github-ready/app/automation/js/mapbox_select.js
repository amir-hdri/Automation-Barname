({ lat, lng }) => {
    const map = window.map ||
               mapboxgl.getMap() ||
               document.querySelector('.mapboxgl-map')._map;

    if (map) {
        map.setCenter([lng, lat]);
        map.setZoom(15);

        // شبیه‌سازی کلیک
        map.fire('click', {
            lngLat: [lng, lat]
        });
        return true;
    }
    return false;
}
