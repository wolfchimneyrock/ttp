import io, avro.io, time
def _get_timestamp(datestr):
    format = "%Y-%m-%d %H:%M:%S.%f"
    return int(time.mktime(time.strptime(datestr, format)))

class MovementEvent:
    def __init__(self, event_id, timestamp, site_id, camera, movement_type, location_type, plate_text, plate_confidence, partition):
        self.event_id = event_id
        self.timestamp = timestamp
        self.site_id = site_id
        self.camera = camera
        self.movement_type = movement_type
        self.location_type = location_type
        self.plate_text = plate_text
        self.plate_confidence = plate_confidence
        self.partition = partition
    @classmethod
    def from_api(cls, config, event_id, eventvalue, eventtime, deviceid):
        value = [x.strip() for x in eventvalue.split(',')]
        plate_text = value[0]
        plate_confidence = value[2]
        timestamp = _get_timestamp(eventtime)
        location_type = config["Fields"]["locationtype"]
        if deviceid <= 2:
            movement_type = "exit"
        else:
            movement_type = "entry"

        partition = deviceid - 1

        site_id = config["Fields"]["siteid"]
        camera={"id": deviceid, 
                "latitude": float(config["Fields"]["latitude"]),
                "longitude": float(config["Fields"]["longitude"])
                }
        return cls(event_id, timestamp, site_id, camera, movement_type, location_type, plate_text, plate_confidence, partition)

    def to_kafka(self, schema_writer):
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        schema_writer.write({
            "id":               self.event_id,
            "timestamp":        self.timestamp,
            "site_id":          self.site_id,
            "camera":           self.camera,
            "movement_type":    self.movement_type,
            "location_type":    self.location_type,
            "plate_text":       self.plate_text,
            "plate_confidence": self.plate_confidence
            }, encoder)
        return bytes_writer.getvalue()
        

    def key(self, timestamp):
        return self.site_id + '.' + self.camera['id'] + '.' + timestamp
