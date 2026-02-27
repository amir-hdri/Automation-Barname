({ selector, lat, lng }) => {
    const mapElement = document.querySelector(selector);
    if (!mapElement) return false;

    // یافتن نمونه Leaflet
    const map = mapElement._leaflet_map ||
               window.map ||
               L.Map.getMap(selector);

    if (map) {
        const latLng = L.latLng(lat, lng);
        map.setView(latLng, 15);

        // شبیه‌سازی کلیک
        const containerPoint = map.latLngToContainerPoint(latLng);
        const layerPoint = map.latLngToLayerPoint(latLng);

        map.fire('click', {
            latlng: latLng,
            layerPoint: layerPoint,
            containerPoint: containerPoint
        });
        return true;
    }
    return false;
}
