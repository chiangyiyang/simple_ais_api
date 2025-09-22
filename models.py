from datetime import datetime
from app import db

class ShipAIS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(200))
    ship_id = db.Column(db.String(50))
    shipname = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    speed = db.Column(db.Float)
    course = db.Column(db.Float)
    heading = db.Column(db.Float)
    rot = db.Column(db.Float)
    destination = db.Column(db.String(200))
    dwt = db.Column(db.String(50))
    flag = db.Column(db.String(50))
    shiptype = db.Column(db.String(50))
    gt_shiptype = db.Column(db.String(50))
    length = db.Column(db.String(50))
    width = db.Column(db.String(50))

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "ship_id": self.ship_id,
            "shipname": self.shipname,
            "lat": self.lat,
            "lon": self.lon,
            "speed": self.speed,
            "course": self.course,
            "heading": self.heading,
            "rot": self.rot,
            "destination": self.destination,
            "dwt": self.dwt,
            "flag": self.flag,
            "shiptype": self.shiptype,
            "gt_shiptype": self.gt_shiptype,
            "length": self.length,
            "width": self.width
        }