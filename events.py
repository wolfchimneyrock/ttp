import io, avro.io
class MovementEvent:
    def __init__(self, timestamp, site_id, camera, movement_type, location_type, plate_text, plate_confidence):
        self.timestamp = timestamp
        self.site_id = site_id
        self.camera = camera
        self.movement_type = movement_type
        self.location_type = location_type
        self.plate_text = plate_text
        self.plate_confidence = plate_confidence

    @classmethod
    def from_api(cls, config, eventvalue, eventtime, deviceid):
        value = [x.strip() for x in eventvalue.split(',')]
        plate_text = value[0]
        plate_confidence = value[2]
        timestamp = _get_timestamp(eventtime)
        location_type = config["Fields"]["locationtype"]
        movement_type = "within"
        site_id = config["Fields"]["siteid"]
        camera={"id": deviceid, 
                "latitude": config["Fields"]["latitude"],
                "longitude": config["Fields"]["longitude"]
                }
        return cls(timestamp, site_id, camera, movement_type, location_type, plate_text, plate_confidence)

    def to_kafka(self, schema_writer):
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        schema_writer.write({
            "timestamp":        self.timestamp,
            "site_id":          self.site_id,
            "camera":           self.camera,
            "movement_type":    self.movement_type,
            "location_type":    self.location_type,
            "plate_text":       self.plate_text,
            "plate_confidence": self.plate_confidence
            }, encoder)
        return bytes_writer.getvalue()

        


