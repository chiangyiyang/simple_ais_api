from shapely.geometry import Point, Polygon

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

def in_polygon(point, polygon):
    """
    判斷點是否在多邊形內（包含邊界）。
    point: (x, y) 座標
    polygon: 頂點清單 [(x1,y1), (x2,y2), ...]
    回傳 True/False（包含邊界視為在內）
    使用 shapely，若發生例外或輸入不合法回傳 False
    """
    try:
        # 基本結構與型別檢查
        if not (isinstance(point, (list, tuple)) and len(point) == 2):
            return False
        if not (isinstance(polygon, (list, tuple)) and len(polygon) >= 3):
            return False

        x, y = point
        px = float(x)
        py = float(y)

        poly = Polygon([(float(px_), float(py_)) for px_, py_ in polygon])
        if not poly.is_valid:
            # 若多邊形無效（例如自交），視為 False
            return False

        pt = Point(px, py)
        # 使用 covers 以包含邊界（contains 不包含邊界）
        return poly.covers(pt)
    except Exception:
        return False