from lightning.pytorch import seed_everything

from nfc_emg import models, utils
from nfc_emg.sensors import EmgSensorType

from config import Config, ExperimentStage
from familiarization import Familiarization
from game import Game


def main(subject_id, sensor, features, step, adaptation, sample_data):
    config = Config(
        subject_id=subject_id,
        sensor_type=sensor,
        features=features,
        stage=step,
        adaptation=adaptation,
    )

    if config.stage == ExperimentStage.FAMILIARIZATION:
        fam = Familiarization(config, False)
        fam.run()
    elif config.stage == ExperimentStage.VISUALIZE_CLASSIFIER:
        fam = Familiarization(config, True)
        fam.run()
    elif config.stage == ExperimentStage.SG_TRAIN:
        models.main_train_nn(
            config.model,
            config.sensor,
            sample_data,
            config.features,
            config.gesture_ids,
            config.paths.gestures,
            config.paths.get_train(),
            config.paths.get_model(),
            config.reps,
            config.rep_time,
        )
    elif config.stage == ExperimentStage.SG_PRE_TEST:
        config.paths.test = config.paths.test.replace("test", "pre_test")
        results = models.main_test_nn(
            config.model,
            config.sensor,
            sample_data,
            config.features,
            config.gesture_ids,
            config.paths.gestures,
            config.paths.get_test(),
        )
        results_file = config.paths.get_results().replace(".csv", "_pre.json")
        utils.save_eval_results(results, results_file)
        utils.show_conf_mat(results, config.paths, config.gesture_ids)
    elif config.stage == ExperimentStage.GAME:
        config.paths.set_model("model_post")
        game = Game(config)
        game.run()
    elif config.stage == ExperimentStage.SG_POST_TEST:
        config.paths.test = config.paths.test.replace("test", "post_test")
        results = models.main_test_nn(
            config.model,
            config.sensor,
            sample_data,
            config.features,
            config.gesture_ids,
            config.paths.gestures,
            config.paths.get_test(),
        )
        results_file = config.paths.get_results().replace(".csv", "_post.json")
        utils.save_eval_results(results, results_file)
        utils.show_conf_mat(results, config.paths, config.gesture_ids)


if __name__ == "__main__":
    seed_everything(310)
    features = "TDPSD"

    subject = 0
    sensor = EmgSensorType.BioArmband

    # steps = [ExperimentStage.FAMILIARIZATION]
    # steps = [ExperimentStage.SG_TRAIN, ExperimentStage.SG_TEST]
    steps = [ExperimentStage.SG_PRE_TEST]
    # steps = [ExperimentStage.GAME]
    # steps = [ExperimentStage.SG_POST_TEST]

    adaptation = True
    sample_data = False

    for step in steps:
        print(f"Running step {step}")
        main(subject, sensor, features, step, adaptation, sample_data)

    print("Exiting experiment main thread.")
