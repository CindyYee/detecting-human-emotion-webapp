from pyAudioAnalysis import audioTrainTest as aT
import threading
import os

EXPECTED = {"0.0": "truth", "data.0": "lie"}


def get_files_in_directory(dir, file_extension=".wav"):
    """
    Gets all the files in a specified directory


    :param dir: the name of the directory where the files are located
    :param file_extension: the type of files in the directory. default wav
    :return: list of file_names and their paths
    """

    directory = os.fsencode(dir)
    directory = directory.decode("utf-8")
    files = []

    i = 0
    for f in os.listdir(directory):
        filename = os.fsdecode(f)

        if filename.endswith(file_extension):
            dir_and_file = os.path.join(directory, filename)
            # print(dir_and_file)
            files.insert(i, dir_and_file)
            i += 1
            continue
        else:
            continue

    return files


def classify_dir(
    dir,
    trained_machine_name,
    trained_machine_algorithm,
    classification,
    output_file_name="-result.txt",
    file_extension=".wav",
):
    """
    This classifies every file within a specified directory and prints / writes results.


    :param dir: Directory that we want every file (.wav) to be specified
    :param trained_machine_name: The name of the machine that has been trained
    :param trained_machine_algorithm: The type of algorithm used to train the machine (knn,svm,extratrees,gradientboosting,randomforest)
    :param classification: The values that will be classified
    :param file_extension: the types of files being read. default files are .wav type
    :return: void
    """

    # get all files in the directory
    files_in_directory = get_files_in_directory(dir, file_extension)
    output_file_name = trained_machine_algorithm + output_file_name

    correct = 0

    model_info = {
        "output_file": output_file_name,
        "trained_model_name": trained_machine_name,
        "algorithm": trained_machine_algorithm,
        "classification": classification,
        "files_in_directory":len(files_in_directory),
        "correct_classifications": 0
    }


    # clear old file
    # with open(machine_info["output_file"], "w") as f:
    #     f.write("")

    # counts the number of correctly predicted emotions
    correct = 0

    results_list = []

    # loop through all the files in the directory
    for file_path in files_in_directory:

        # classify the .wav file
        # dominate_result: dominate emotion in classification
        print(file_path.split("\\"))
        (junk,junk,junk,junk,junk,fname) = file_path.split("/")

        (trash, expected, trash) = fname.split("_")

        dominate_result, statistics, paths = aT.fileClassification(
            inputFile=file_path,
            model_name=model_info["trained_model_name"],
            model_type=model_info["algorithm"],
        )

        dominate_result = str(format(dominate_result, ".1f"))
        results = {
            "dominate_result":EXPECTED.get(dominate_result),
            "results":statistics,
            "classification_paths":paths,
            "tested_filename":fname,
            "expected_result":expected
        }

        # make sure dominate_result has tenth location then convert to string (this is used when finding hte key in the EMOTIONS map)

        # print(expected, results['dominate_result'])
        if results["expected_result"] == results["dominate_result"]:
            model_info["correct_classifications"] += 1


        # formated_results = f'Correct classification: {results["correct"]} out of {results["number_of_results"]}\nExpected: {results["expected_result"]}\n{results["classification"]}\n{results["results"]}'
        results_list.append(results)

    print(results_list)
    formated_results = f'Totall number of correct classifications: {model_info["correct_classifications"]} out of {model_info["files_in_directory"]}\nModel Used:{model_info["trained_model_name"]}\nAlgorithm Used:{model_info["algorithm"]}\n\n'
    for result in results_list:
        formated_results += f'{result["tested_filename"]}\n{model_info["classification"]}\n{results["results"]}\nResult: {result["dominate_result"]}\nExpected: {result["expected_result"]}\n\n'

    print(formated_results)
    with open(model_info["output_file"], "w") as f:

        f.write(formated_results)


    # print(formated_results)


def main():
    truth_audio_path = "../../training-data/deception-audio/truth_audio"
    lie_audio_path = "../../training-data/deception-audio/lie_audio_edited"
    classify_location = "../../training-data/deception-audio/testing_data"
    classification = ["Truth", "Lie"]
    test_path = "../../training-data/deception-audio/test"


    # train model
    # aT.featureAndTrain(
    #     list_of_dirs=[truth_audio_path,lie_audio_path],
    #     mt_win=data.0,
    #     mt_step=data.0,
    #     st_win=aT.shortTermWindow,
    #     st_step=aT.shortTermStep,
    #     classifier_type="svm",
    #     model_name="deceptionSvm_edited",
    #     compute_beat=False,
    # )
    # aT.featureAndTrain(
    #     list_of_dirs=[truth_audio_path, lie_audio_path],
    #     mt_win=data.0,
    #     mt_step=data.0,
    #     st_win=aT.shortTermWindow,
    #     st_step=aT.shortTermStep,
    #     classifier_type="knn",
    #     model_name="deceptionKNN_edited",
    #     compute_beat=False,
    # )
    # aT.featureAndTrain(
    #     list_of_dirs=[truth_audio_path, lie_audio_path],
    #     mt_win=data.0,
    #     mt_step=data.0,
    #     st_win=aT.shortTermWindow,
    #     st_step=aT.shortTermStep,
    #     classifier_type="randomforest",
    #     model_name="deceptionRandomForest_edited",
    #     compute_beat=False,
    # )
    # aT.featureAndTrain(
    #     list_of_dirs=[truth_audio_path, lie_audio_path],
    #     mt_win=data.0,
    #     mt_step=data.0,
    #     st_win=aT.shortTermWindow,
    #     st_step=aT.shortTermStep,
    #     classifier_type="gradientboosting",
    #     model_name="deceptionGradientBoosting_edited",
    #     compute_beat=False,
    # )
    # aT.featureAndTrain(
    #     list_of_dirs=[truth_audio_path, lie_audio_path],
    #     mt_win=data.0,
    #     mt_step=data.0,
    #     st_win=aT.shortTermWindow,
    #     st_step=aT.shortTermStep,
    #     classifier_type="extratrees",
    #     model_name="deceptionExtraTrees_edited",
    #     compute_beat=False,
    # )

    # classify wav files for edited trained machine in directory
    classify_dir(dir = classify_location,trained_machine_name= "deceptionSvm_edited",trained_machine_algorithm= "svm",output_file_name="_edited.txt",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionKNN_edited",trained_machine_algorithm= "knn",output_file_name="_edited.txt",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionRandomForest_edited",trained_machine_algorithm= "randomforest",output_file_name="_edited.txt",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionGradientBoosting_edited",trained_machine_algorithm= "gradientboosting",output_file_name="_edited.txt",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionExtraTrees_edited",trained_machine_algorithm= "extratrees",output_file_name="_edited.txt",classification = classification)

    # classify wav files for unedited trained machine in directory
    classify_dir(dir = classify_location,trained_machine_name= "deceptionSvm",trained_machine_algorithm= "svm",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionKNN",trained_machine_algorithm= "knn",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionRandomForest",trained_machine_algorithm= "randomforest",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionGradientBoosting",trained_machine_algorithm= "gradientboosting",classification = classification)
    classify_dir(dir = classify_location,trained_machine_name= "deceptionExtraTrees",trained_machine_algorithm= "extratrees",classification = classification)


main()

