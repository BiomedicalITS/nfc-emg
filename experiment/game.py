from threading import Lock, Thread
import os

import socket
import time

from libemg.emg_classifier import EMGClassifier, OnlineEMGClassifier

from nfc_emg.utils import get_online_data_handler
from nfc_emg import models

from config import Config
import memory_manager
import adapt_manager
import super_classi


class Game:
    def __init__(self, config: Config):
        self.classifier_port = 12347
        self.mem_manager_server_port = 12348
        self.adap_manager_port = 12349
        self.unity_port = 12350

        self.config = config
        self.paths = config.paths
        self.sensor = config.sensor
        self.features = config.features

        self.odh = get_online_data_handler(
            config.sensor,
            imu=False,
            timestamps=True,
            file=True,
            file_path=self.paths.get_live(),
        )

        classi = EMGClassifier()
        classi.classifier = config.model
        # classi.add_majority_vote(self.sensor.maj_vote_n)
        # classi.add_rejection()

        self.oclassi = OnlineEMGClassifier(
            classi,
            self.sensor.window_size,
            self.sensor.window_increment,
            self.odh,
            self.features,
            port=self.classifier_port,
        )
        self.model_lock = Lock()

        # Delete old data if applicable
        for f in os.listdir(self.paths.get_experiment_dir()):
            if not f.startswith("live_"):
                continue
            os.remove(f"{self.paths.get_experiment_dir()}{f}")

    def run(self):
        print("Waiting for Unity to send 'READY'...")

        self.sensor.start_streamer()

        unity_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        unity_sock.bind(("localhost", self.unity_port))
        while True:
            unity_packet, addr = unity_sock.recvfrom(1024)
            print(f"Received: {unity_packet.decode()} from {addr}")
            if unity_packet.decode() == "READY":
                # global_timer = time.perf_counter()
                logs_path = f"{os.getcwd()}/{self.config.paths.get_experiment_dir()}"
                unity_sock.sendto(logs_path.encode(), addr)
                print(f"Sent: {logs_path} to {addr}")
                time.sleep(1)
                unity_sock.close()
                break

        print("Starting the Python Game Stage!")

        Thread(
            target=super_classi.run_classifier,
            args=(
                self.oclassi,
                self.paths.get_live() + "preds.csv",
                self.model_lock,
            ),
            daemon=True,
        ).start()

        Thread(
            target=memory_manager.run_memory_manager,
            args=(
                self.config,
                self.unity_port,
                self.mem_manager_server_port,
            ),
            daemon=True,
        ).start()

        adapt_manager.run_adaptation_manager(
            self.config,
            self.model_lock,
            self.mem_manager_server_port,
            self.oclassi,
        )

        # because we are running daemon processes they die as main process dies
        models.save_nn(self.config.model, self.paths.get_model())
