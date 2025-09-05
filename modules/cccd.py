class CCCD():
    id: str
    side: str
    path: str
    processed: bool = True

    def __init__(self, side: str, path: str, id: str = "", processed: bool = True):
        self.side = side
        self.path = path
        self.id = id
        self.processed = processed

    def set_side(self, side):
        self.side = side

    def set_path(self, path):
        self.path = path

    def set_id(self, id):
        self.id = id

    def get_side(self):
        return self.side

    def get_path(self):
        return self.path

    def get_id(self):
        return self.id

    def is_processed(self):
        return self.processed

    def set_processed(self, processed: bool):
        self.processed = processed

    def __str__(self):
        return f"CCCD: {self.side}, {self.path}, {self.id}"
