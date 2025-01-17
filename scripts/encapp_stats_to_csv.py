#!/usr/bin/env python3

import json
import argparse
import pandas as pd
import seaborn as sb
import matplotlib.pyplot as plt
import numpy as np
import encapp as ep

# pd.options.mode.chained_assignment = 'raise'

# "id": "encapp_3d989dae-2218-43a8-a96c-c4856f362c4b",
# "description": "surface encoder",
# "date": "Mon Jul 20 15:18:35 PDT 2020",
# "proctime": 842594344696070,
# "framecount": 294,
# "encodedfile": "encapp_3d989dae-2218-43a8-a96c-c4856f362c4b.mp4",
# "settings": {
#   "codec": "video/hevc",
#   "gop": 10,
#   "fps": 30,
#   "bitrate": 2000000,
#   "meanbitrate": 1905177,
#   "width": 1280,
#   "height": 720,
#   "encmode": "BITRATE_MODE_CBR",
#   "keyrate": 10,
#   "iframepreset": "UNLIMITED",
#   "colorformat": 2135033992,
#   "colorrange": 2,
#   "colorstandard": 4,
#   "colortransfer": 3,
#   "hierplayers": 0,
#   "ltrcount": 1
# },
# "frames": [
#   {
#   "frame": 0,
#   "iframe": 1,
#   "size": 31568,
#   "pts": 66666,
#   "proctime": 74273281
#   },


def parse_encoding_data(json, inputfile, debug=0):
    if debug > 0:
        print(f'Parse encoding data: {inputfile}')

    try:
        data = pd.DataFrame(json['frames'])

        data['source'] = inputfile
        data['codec'] = json['settings']['codec']
        data['description'] = json['description']
        data['camera'] = (json['testdefinition'].find(
            "filepath: \"camera\"")) > 0
        data['test'] = json['test']
        data['bitrate'] = ep.convert_to_bps(json['settings']['bitrate'])
        data['height'] = json['settings']['height']
        fps = json['settings']['fps']
        data['fps'] = fps
        data['duration_ms'] = round((data['pts'].shift(-1, axis='index',
                                     fill_value=0) - data['pts']) / 1000, 2)
        data['bitrate_per_frame_bps'] = (
            data['size'] * 8.0) / (data['duration_ms'] / 1000.0)
        data['average_bitrate'] = np.mean(data['bitrate_per_frame_bps'])
        data['stop-stop_ms'] = round(
            (data['stoptime'].shift(-1, axis='index', fill_value=0) -
             data['stoptime']) / 1000000, 2)
        data.loc[data['proctime'] < 0] = 0
        data.loc[data['duration_ms'] < 0] = 0
        data['fps'] = round(1000.0 / (data['duration_ms']), 2)
        data['proc_fps'] = round(1000.0 / (data['stop-stop_ms']), 2)
        # delete the last item
        data = data.loc[data['starttime'] > 0]
        start_ts = data.iloc[0]['starttime']
        data['rel_start_ms'] = round(
            (data['starttime'] - start_ts) / 1000000, 2)
        stop_ts = data.iloc[0]['stoptime']
        data['rel_stop_ms'] = round((data['stoptime'] - stop_ts) / 1000000, 2)

        data['start_pts_diff_ms'] = round(
            data['rel_start_ms'] - data['pts'] / 1000, 2)
        data['av_fps'] = data['fps'].rolling(
            fps, min_periods=fps, win_type=None).sum() / fps
        data['av_proc_fps'] = data['proc_fps'].rolling(
            fps, min_periods=fps, win_type=None).sum() / fps
        data['av_fps'].fillna(data['fps'], inplace=True)
        data['av_proc_fps'].fillna(data['proc_fps'], inplace=True)
        data.fillna(0, inplace=True)
        data, __ = calc_infligh(data, start_ts)
    except Exception as ex:
        print(f'parsing failed: {ex}')
        return None
    if debug > 2:
        print(f'{data}')
    return data


def parse_decoding_data(json, inputfile, debug=0):
    if debug > 0:
        print('Parse decoding data')
    decoded_data = None
    try:
        decoded_data = pd.DataFrame(json['decoded_frames'])
        decoded_data['source'] = inputfile
        fps = 30
        if (len(decoded_data) > 0):
            try:
                decoded_data['codec'] = json['decoder_media_format']['mime']
            except Exception:
                print('Failed to read decoder data')
                decoded_data['codec'] = 'unknown codec'
            try:
                decoded_data['height'] = json['decoder_media_format']['height']
            except Exception:
                print('Failed to read decoder data')
                decoded_data['height'] = 'unknown height'

            decoded_data = decoded_data.loc[decoded_data['proctime'] >= 0]

            # oh no we may have b frames...
            decoded_data['duration_ms'] = round(
                (decoded_data['pts'].shift(-1, axis='index', fill_value=0) -
                 decoded_data['pts']) / 1000, 2)

            decoded_data['fps'] = round(
                1000.0 / (decoded_data['duration_ms']), 2)
            decoded_data['stop-stop_ms'] = round(
                (decoded_data['stoptime'].shift(-1, axis='index',
                 fill_value=0) - decoded_data['stoptime']) / 1000000, 2)
            decoded_data['proc_fps'] = round(
                1000.0 / (decoded_data['stop-stop_ms']), 2)

            start_ts = decoded_data.iloc[0]['starttime']
            decoded_data['rel_start_ms'] = round(
                (decoded_data['starttime'] - start_ts) / 1000000, 2)
            stop_ts = decoded_data.iloc[0]['stoptime']
            decoded_data['rel_stop_ms'] = round(
                (decoded_data['stoptime'] - stop_ts) / 1000000, 2)

            decoded_data['start_pts_diff_ms'] = round(
                decoded_data['rel_start_ms'] - decoded_data['pts'] / 1000, 2)
            decoded_data['av_fps'] = decoded_data['fps'].rolling(
                fps, min_periods=fps, win_type=None).sum() / fps
            decoded_data['av_proc_fps'] = decoded_data['proc_fps'].rolling(
                fps, min_periods=fps, win_type=None).sum() / fps
            decoded_data['av_fps'].fillna(decoded_data['fps'], inplace=True)
            decoded_data['av_proc_fps'].fillna(
                decoded_data['proc_fps'], inplace=True)
            decoded_data.fillna(0)

    except Exception as ex:
        print(f'Failed to parse decode data for {inputfile}: {ex}')
        decoded_data = None

    return decoded_data


def parse_gpu_data(json, inputfile, debug=0):
    if debug > 0:
        print('Parse gpu data')
    gpu_data = None
    try:
        gpu_data = pd.DataFrame(json['gpu_data']['gpu_load_percentage'])
        if len(gpu_data) > 0:
            gpuclock_data = pd.DataFrame(json['gpu_data']['gpu_clock_freq'])
            gpu_max_clock = int(json['gpu_data']['gpu_max_clock'])
            gpu_data['clock_perc'] = (
                100.0 * gpuclock_data['clock_MHz'].astype(float) /
                gpu_max_clock)
            gpu_data = gpu_data.merge(gpuclock_data)
            gpu_model = json['gpu_data']['gpu_model']
            gpu_data['source'] = inputfile
            gpu_data['gpu_max_clock'] = gpu_max_clock
            gpu_data['gpu_model'] = gpu_model
            gpu_data.fillna(0)
    except Exception as ex:
        print(f'GPU parsing failed: {ex}')
        pass
    return gpu_data


def calc_infligh(frames, time_ref):
    ''' Calculate how many frames have start but not yet stopped
        during a certain period.
        Remove the offset using time_ref '''

    sources = pd.unique(frames['source'])
    coding = []
    for source in sources:
        # Calculate how many frames starts encoding before a frame has finished
        # relying on the accurace of the System.nanoTime()
        inflight = []
        filtered = frames.loc[frames['source'] == source]
        start = np.min(filtered['starttime'])
        stop = np.max(filtered['stoptime'])
        # Calculate a time where the start offset (if existing) does not
        # blur the numbers
        coding.append([source, start - time_ref, stop - time_ref])
        for row in filtered.iterrows():
            start = row[1]['starttime']
            stop = row[1]['stoptime']
            intime = (filtered.loc[(filtered['stoptime'] > start) &
                                   (filtered['starttime'] < stop)])
            count = len(intime)
            inflight.append(count)
        frames.loc[frames['source'] == source, 'inflight'] = inflight

    labels = ['source', 'starttime', 'stoptime']
    concurrent = pd.DataFrame.from_records(coding, columns=labels,
                                           coerce_float=True)

    # calculate how many new encoding are started before stoptime
    inflight = []
    for row in concurrent.iterrows():
        start = row[1]['starttime']
        stop = row[1]['stoptime']
        count = (len(concurrent.loc[(concurrent['stoptime'] > start) &
                                    (concurrent['starttime'] < stop)]))
        inflight.append(count)
    concurrent['conc'] = inflight
    return frames, concurrent


def clean_name(name, debug=0):
    ret = name.translate(str.maketrans({',': '_', ' ': '_'}))
    print(f'{name} -> {ret}')
    return ret


def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--debug', action='count',
                        dest='debug', default=0,
                        help='Increase verbosity (use many times for more)',)
    parser.add_argument('--quiet', action='store_const',
                        dest='debug', const=-1,
                        help='Zero verbosity',)
    parser.add_argument('file', nargs='?', help='file to analyze')
    parser.add_argument('--label', default='')

    options = parser.parse_args()

    return options


def main():
    """
        Calculate stats for videos based on parsing individual frames
        with ffprobe frame parser.
        Can output data for a single file or aggregated data for several files.
    """
    options = parse_args()

    with open(options.file) as json_file:
        alldata = json.load(json_file)

        encoding_data = parse_encoding_data(alldata, options.file,
                                            options.debug)

        if encoding_data is not None and len(encoding_data) > 0:
            encoding_data.to_csv(f'{options.file}_encoding_data.csv')

        decoded_data = parse_decoding_data(alldata, options.file,
                                           options.debug)
        if decoded_data is not None and len(decoded_data) > 0:
            decoded_data.to_csv(f'{options.file}_decoded_data.csv')

        gpu_data = parse_gpu_data(alldata, options.file, options.debug)
        if gpu_data is not None and len(gpu_data) > 0:
            gpu_data.to_csv(f'{options.file}_gpu_data.csv')


if __name__ == '__main__':
    main()
