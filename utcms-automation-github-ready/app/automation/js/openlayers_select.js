({ selector, lat, lng }) => {
    const mapElement = document.querySelector(selector);
    if (!mapElement) return false;

    // یافتن نمونه OpenLayers
    const map = mapElement._map ||
               ol.Map.getMapById(selector) ||
               window.map;

    if (map) {
        const coordinate = ol.proj.fromLonLat([lng, lat]);
        map.getView().setCenter(coordinate);
        map.getView().setZoom(15);

        // شبیه‌سازی کلیک
        const pixel = map.getPixelFromCoordinate(coordinate);
        map.dispatchEvent({
            type: 'click',
            coordinate: coordinate,
            pixel: pixel
        });
        return true;
    }
    return false;
}
