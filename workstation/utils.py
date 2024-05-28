import os
import numpy as np
import json

from libemg.streamers import sifibridge_streamer, myo_streamer, emager_streamer
from libemg.data_handler import OnlineDataHandler
from libemg.filtering import Filter


from models import EmgCNN
import globals as g


def get_most_recent_checkpoint(lightning_logs_path: str = "./lightning_logs") -> str:
    max = 0
    for folder in os.listdir(lightning_logs_path):
        if "version" not in folder:
            continue

        with open(f"{lightning_logs_path}/{folder}/hparams.yaml", "r") as f:
            text = f.readline()
            if text.startswith("{}"):
                continue

        num = int(folder.split("_")[1])
        if num > max:
            max = num
    ckpt_name = os.listdir(f"{lightning_logs_path}/version_{max}/checkpoints")[0]
    model_ckpt_path = f"{lightning_logs_path}/version_{max}/checkpoints/{ckpt_name}"

    return model_ckpt_path


def get_filter(
    sampling_rate: float,
    bandpass_freqs: float | list = [20, 350],
    notch_freq: int = 50,
):
    if isinstance(bandpass_freqs, float) or isinstance(bandpass_freqs, int):
        bandpass_freqs = [bandpass_freqs]

    # Create some filters
    fi = Filter(sampling_frequency=sampling_rate)
    fi.install_filters({"name": "notch", "cutoff": notch_freq, "bandwidth": 3})
    if len(bandpass_freqs) == 2 and sampling_rate > bandpass_freqs[1] * 2:
        fi.install_filters(
            filter_dictionary={"name": "bandpass", "cutoff": bandpass_freqs, "order": 4}
        )
    else:
        fi.install_filters(
            {"name": "highpass", "cutoff": bandpass_freqs[0], "order": 2}
        )
    return fi


def get_model(finetune: bool = False, num_classes: int = 5):
    """
    Load the most recent model checkpoint and return it
    """
    model_ckpt = get_most_recent_checkpoint()
    print("Loading model from:", model_ckpt)
    model = EmgCNN.load_from_checkpoint(checkpoint_path=model_ckpt)
    model.set_finetune(finetune, num_classes=num_classes)
    return model


def map_class_to_gestures(data_dir: str):
    """
    g.LIBEMG_GESTURE_IDS define which gestures to download for training.
    ScreenGuidedTraining does not map the gestures to model Class in order
    """
    with open(data_dir + "metadata.json", "r") as f:
        metadata: dict = json.load(f)
    class_to_name = {}
    for val in metadata.values():
        if not isinstance(val, dict):
            continue
        if "class_idx" not in val and "class_name" not in val:
            continue
        class_to_name[val["class_idx"]] = val["class_name"]
    return class_to_name


def setup_streamer(device: str = "myo", notch_freq: int = 50):
    # Setup the streamers
    if device == "myo":
        # Create Myo Streamer
        return myo_streamer(filtered=False, imu=True)
    elif device == "bioarmband":
        return sifibridge_streamer(
            version="1_1",
            emg=True,
            imu=True,
            notch_on=True,
            notch_freq=notch_freq,
        )
    elif device == "emager":
        return emager_streamer()
    else:
        raise ValueError(f"Unknown device: {device}")


def get_online_data_handler(
    sampling_rate: float,
    bandpass_freqs: float | list = [20, 350],
    notch_freq: int = 50,
    **kwargs,
) -> OnlineDataHandler:
    if not isinstance(bandpass_freqs, list) or isinstance(bandpass_freqs, tuple):
        bandpass_freqs = [bandpass_freqs]

    # Create Online Data Handler - This listens for data
    odh = OnlineDataHandler(imu_arr=True, **kwargs)
    odh.install_filter(get_filter(sampling_rate, bandpass_freqs, notch_freq))
    odh.start_listening()
    return odh


def process_data(data: np.ndarray, device: str = "myo") -> np.ndarray:
    # Assumes data is prefiltered

    # rectify
    data = np.abs(data)
    # data = tke(data)
    data = moving_average(data, g.EMG_RUNNING_MEAN_LEN)

    # normalize
    if device == "myo":
        return (data / 128.0).astype(np.float32)

    return (data / (5 * 10e-3)).astype(np.float32)


def moving_average(x: np.ndarray, N: int):
    orig_shape = x.shape
    x = x.reshape(-1, np.prod(x.shape[1:]))

    for c in range(x.shape[1]):
        x[:, c] = np.convolve(x[:, c], np.ones(N) / N, mode="same")
    return x.reshape(orig_shape)


def tke(data):
    data = np.vstack((data[0:1], data))
    data = np.vstack((data, data[-1:]))
    data = data[1:-1] ** 2 - data[:-2] * data[2:]
    return data


def visualize(device: str, sampling_rate: int, notch_freq: int = 50):
    """
    Visualize the data stream in real time. Takes care of setting up the streamer.
    """
    p = setup_streamer(device, notch_freq)
    odh = get_online_data_handler(sampling_rate, notch_freq=notch_freq, use_imu=False)
    odh.visualize_channels(list(range(8)), 3 * sampling_rate)
    return p


if __name__ == "__main__":
    p = visualize()

    # p = get_most_recent_checkpoint()
    # print(p)