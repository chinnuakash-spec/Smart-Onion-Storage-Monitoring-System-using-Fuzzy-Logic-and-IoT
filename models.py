from django.db import models


class SensorData(models.Model):
    """
    Stores real-time readings received from Raspberry Pi sensor node.
    Maps to the SQLite database table 'smartstorage_sensordata'.
    """
    device_id    = models.CharField(max_length=100, default="Device 1")
    temperature  = models.FloatField(help_text="Temperature in °C")
    humidity     = models.FloatField(help_text="Relative humidity in %")
    gas_ppm      = models.FloatField(help_text="Gas concentration in ppm (MQ135)")
    shelf_life   = models.FloatField(help_text="Estimated shelf life in months (fuzzy output)")
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"[{self.device_id}] {self.timestamp:%Y-%m-%d %H:%M} | "
            f"T={self.temperature}°C H={self.humidity}% "
            f"Gas={self.gas_ppm}ppm SL={self.shelf_life}mo"
        )

    @property
    def condition(self) -> str:
        """Classify storage condition based on fuzzy shelf life output."""
        if self.shelf_life >= 4:
            return "Good"
        elif self.shelf_life >= 2:
            return "Average"
        return "Poor"
