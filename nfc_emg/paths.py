from dataclasses import dataclass


@dataclass
class NfcPaths:
    base: str = "data/"
    gestures: str = "gestures/"
    model: str = "model.pth"
    train: str = "train/"
    test: str = "test/"
    imu_calib: str = "imu_calib_data.npz"

    def __init__(self, base="data/"):
        self.set_base_dir(base)

    def set_base_dir(self, base_dir: str):
        if not base_dir.endswith("/"):
            base_dir += "/"
        self.base = base_dir
        self.gestures = self.base + "gestures/"
        self.model = self.base + "model.pth"
        self.train = self.base + "train/"
        self.test = self.base + "test/"
        self.imu_calib = self.base + "imu_calib_data.npz"


if __name__ == "__main__":
    paths = NfcPaths()
    print(paths.model)
    paths.set_base_dir("ffffff")
    print(paths.model)
