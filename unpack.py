import os
import subprocess
import sys
import time
from pydub import AudioSegment  # pip install pydub
from io import BytesIO
import traceback
import requests
import zipfile
import io


this_directory = os.getcwd()


def download_and_extract_zip(zip_url, extract_to):
    try:
        # Step 1: Download the ZIP file into RAM
        response = requests.get(zip_url)
        response.raise_for_status()  # Ensure the request was successful

        # Step 2: Load the downloaded ZIP file into a BytesIO object (in memory)
        zip_data = io.BytesIO(response.content)

        # Step 3: Open the ZIP file in memory
        with zipfile.ZipFile(zip_data, "r") as zip_ref:
            # Step 4: Extract all files to the specified directory
            zip_ref.extractall(extract_to)
            print(f"All files have been extracted to '{extract_to}'.")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
    except zipfile.BadZipFile as e:
        print(f"Error reading the ZIP file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Define functions for specific file extensions
def function_for_mul(file_path):
    # Example: run executable1.exe on the .mul file
    executable = os.path.join(this_directory, "bin_dx3", "Gibbed.DeusEx3.Demux.exe")
    AudioSegment.converter = os.path.join(this_directory, "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe")
    # Ensure the file path is absolute
    file_path = os.path.abspath(file_path)

    # Change directory to the directory containing the file
    file_directory = os.path.dirname(file_path)
    os.chdir(file_directory)

    filename, extension = os.path.basename(file_path).split(".")
    fsb_left_file_path = os.path.join(file_directory, f"{filename}_0.fsb")
    fsb_right_file_path = os.path.join(file_directory, f"{filename}_1.fsb")
    mp3_file_path = os.path.join(file_directory, f"{filename}.mp3")
    try:
        # Run the executable
        if not os.path.isfile(fsb_left_file_path):
            subprocess.run([executable, file_path], check=True)
            print(f"Executed {executable} on {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with error: {e.returncode}")
        print(f"Error output: {e.output}")
    except Exception as e:
        print(f"An error occurred on unpack: {e}")

    vgstream_cli_path = os.path.join(this_directory, "vgmstream-win64", "vgmstream-cli.exe")
    if not os.path.isfile(mp3_file_path):
        # Convert to mp3
        if os.path.isfile(fsb_left_file_path) and os.path.isfile(fsb_right_file_path):
            try:
                # Get WAV data for the left channel
                convert_left_ch = [vgstream_cli_path, "-P", fsb_left_file_path]
                try:
                    left_proc = subprocess.Popen(convert_left_ch, stdout=subprocess.PIPE)
                    left_data = left_proc.stdout.read()
                    left_proc.stdout.close()
                    left_proc.terminate()
                except Exception as e:
                    raise RuntimeError(f"Failed to start left channel process: {str(e)}")

                # Get WAV data for the right channel
                convert_right_ch = [vgstream_cli_path, "-P", fsb_right_file_path]
                try:
                    right_proc = subprocess.Popen(convert_right_ch, stdout=subprocess.PIPE)
                    right_data = right_proc.stdout.read()
                    right_proc.stdout.close()
                    right_proc.terminate()
                except Exception as e:
                    raise RuntimeError(f"Failed to start right channel process: {str(e)}")

                if left_data and right_data:
                    # Load the left and right channel audio files as AudioSegment
                    left_channel = AudioSegment.from_raw(BytesIO(left_data), sample_width=2, frame_rate=44100, channels=1)  # 16-bit audio = 2 bytes per sample  # 44.1 kHz sample rate  # Mono
                    right_channel = AudioSegment.from_raw(BytesIO(right_data), sample_width=2, frame_rate=44100, channels=1)  # 16-bit audio = 2 bytes per sample  # 44.1 kHz sample rate  # Mono

                    # Ensure both channels are mono
                    if left_channel.channels != 1 or right_channel.channels != 1:
                        raise ValueError("Both input files must be mono.")

                    # Combine the two mono AudioSegments into a stereo AudioSegment
                    stereo_audio = AudioSegment.from_mono_audiosegments(left_channel, right_channel)

                    # Export the combined stereo audio as an MP3 file
                    stereo_audio.export(out_f=mp3_file_path, format="mp3")
                    os.remove(fsb_left_file_path)
                    os.remove(fsb_right_file_path)
            except Exception as e:
                print(f"convertsion to mp3 stereo failed: {str(e)}")
                print(traceback.format_exc())
                sys.exit()
        elif os.path.isfile(fsb_left_file_path):
            try:
                convert_to_wav = [vgstream_cli_path, "-P", fsb_left_file_path]
                try:
                    proc = subprocess.Popen(convert_to_wav, stdout=subprocess.PIPE)
                    audio_data = proc.stdout.read()
                    proc.stdout.close()
                    proc.terminate()
                except Exception as e:
                    raise RuntimeError(f"Failed to start mono channel process: {str(e)}")

                if audio_data:
                    audio_segment = AudioSegment.from_raw(BytesIO(audio_data), sample_width=2, frame_rate=44100, channels=1)  # Assuming 16-bit audio, adjust if necessary  # Assuming 44.1 kHz, adjust if necessary  # Mono audio

                    # Export the audio as an MP3 file
                    audio_segment.export(mp3_file_path, format="mp3", bitrate="192k")
                    os.remove(fsb_left_file_path)
            except Exception as e:
                print(f"convertsion to mp3 from mono failed: {str(e)}")
                print(traceback.format_exc())
                sys.exit()


def function_for_drm(file_path):
    # Example: run executable2.exe on the .drm file
    executable = os.path.join(this_directory, "bin_dx3", "Gibbed.DeusEx3.DRMUnpack.exe")
    # Ensure the file path is absolute
    file_path = os.path.abspath(file_path)

    # Change directory to the directory containing the file
    file_directory = os.path.dirname(file_path)
    os.chdir(file_directory)

    filename, extension = os.path.basename(file_path).split(".")
    dir_path = os.path.join(file_directory, f"{filename}_unpack")
    try:
        # Run the drm unpack
        if not os.path.isdir(dir_path):
            subprocess.run([executable, file_path], check=True)
            print(f"Executed {executable} on {file_path}")
            recurseDir(dir_path)
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with error: {e.returncode}")
        print(f"Error output: {e.output}")
    except Exception as e:
        print(f"An error occurred on drm unpack: {e}")
        print(file_path)


def function_for_unpack(file_path):
    # Example: run executable2.exe on the .drm file
    executable = os.path.join(this_directory, "bin_dx3", "Gibbed.DeusEx3.Unpack.exe")
    # Ensure the file path is absolute
    file_path = os.path.abspath(file_path)

    # Change directory to the directory containing the file
    file_directory = os.path.dirname(file_path)
    os.chdir(file_directory)

    filename, extension = os.path.basename(file_path).split(".")
    dir_path = os.path.join(file_directory, f"{filename}_unpack")
    try:
        # Run the drm unpack
        if not os.path.isdir(dir_path):
            subprocess.run([executable, file_path], check=True)
            print(f"Executed {executable} on {file_path}")
            recurseDir(dir_path)
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with error: {e.returncode}")
        print(f"Error output: {e.output}")
    except Exception as e:
        print(f"An error occurred on drm unpack: {e}")
        print(file_path)


# Map file extensions to functions
extension_function_map = {".mul": function_for_mul, ".drm": function_for_drm, ".cdrm": function_for_drm, ".000": function_for_unpack}


# Loop through the current directory and all subdirectories
def recurseDir(game_directory):
    for root, dirs, files in os.walk(game_directory):
        for file in files:
            # Get the file extension
            file_extension = os.path.splitext(file)[1]

            # Check if the file extension matches any in the map
            if file_extension in extension_function_map:
                # Get the full path to the file
                file_path = os.path.join(root, file)

                # Execute the corresponding function for the file extension
                selected_function = extension_function_map[file_extension]
                selected_function(file_path)

    print(f"Done processing files. {game_directory}")


if not os.path.isdir(os.path.join(this_directory, "vgmstream-win64")):
    print("Aquiring vgmstream...")
    os.makedirs(os.path.join(this_directory, "vgmstream-win64"), exist_ok=True)
    download_and_extract_zip("https://github.com/vgmstream/vgmstream/releases/latest/download/vgmstream-win64.zip", extract_to=os.path.join(this_directory, "vgmstream-win64"))

if not os.path.isdir(os.path.join(this_directory, "ffmpeg-master-latest-win64-gpl")):
    print("Aquiring ffmpeg...")
    download_and_extract_zip("https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip", extract_to=this_directory)

# set the directory of the game files
if os.path.isfile(os.path.join(this_directory, ".env")):
    with open(os.path.join(this_directory, ".env"), "rb") as file:
        file_lines = file.readlines()

    for file_line in file_lines:
        file_line = os.path.abspath(file_line.decode("utf-8").strip())
        if os.path.isdir(file_line):
            print(f"Rpocessing {file_line}")
            recurseDir(game_directory=file_line)
        else:
            print(file_line)
else:
    print("You need to create a .env file with the full path to the game folder per line.\nExample:\nc:\\path\\to\\somewhere\nc:\\path\\to\\another\\game")
