def in_rectangle(ship, rect):
    """
    判斷船舶是否位於矩形範圍內。
    ship: 可為 dict（含 'lat'/'lon' 或 'LAT'/'LON'）或具有屬性的物件（例如 ORM instance）。
    rect: dict，需包含 keys: 'min_lat', 'max_lat', 'min_lon', 'max_lon'
    回傳 True/False
    """
    try:
        if isinstance(ship, dict):
            lat = float(ship.get('lat') or ship.get('LAT') or 0)
            lon = float(ship.get('lon') or ship.get('LON') or 0)
        else:
            lat = float(getattr(ship, 'lat', getattr(ship, 'LAT', 0)))
            lon = float(getattr(ship, 'lon', getattr(ship, 'LON', 0)))
    except (TypeError, ValueError):
        return False

    try:
        return (rect['min_lat'] <= lat <= rect['max_lat'] and
                rect['min_lon'] <= lon <= rect['max_lon'])
    except Exception:
        return False