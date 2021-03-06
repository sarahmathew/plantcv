# Analyze reflectance signal data in an index

import os
import cv2
import numpy as np
import pandas as pd
from plantcv.plantcv import params
from plantcv.plantcv import outputs
from plantcv.plantcv import plot_image
from plantcv.plantcv import print_image
from plantcv.plantcv import fatal_error
from plotnine import ggplot, aes, geom_line, scale_x_continuous


def analyze_index(index_array, mask, histplot=False, bins=100, min_bin=None, max_bin=None):
    """This extracts the hyperspectral index statistics and writes the values  as observations out to
       the Outputs class.

    Inputs:
    index_array  = Instance of the Spectral_data class, usually the output from pcv.hyperspectral.extract_index
    mask         = Binary mask made from selected contours
    histplot     = if True plots histogram of intensity values
    bins         = optional, number of classes to divide spectrum into
    min_bin      = optional, minimum bin value
    max_bin      = optional, maximum bin value


    :param array: __main__.Spectral_data
    :param mask: numpy array
    :param histplot: bool
    :param bins: int
    :param max_bin: float
    :param min_bin: float
    :return analysis_image: list
    """
    params.device += 1

    debug = params.debug
    params.debug = None
    analysis_image = None

    if len(np.shape(mask)) > 2 or len(np.unique(mask)) > 2:
        fatal_error("Mask should be a binary image of 0 and nonzero values.")

    if len(np.shape(index_array.array_data)) > 2:
        fatal_error("index_array data should be a grayscale image.")

    # Mask data and collect statistics about pixels within the masked image
    masked_array = index_array.array_data[np.where(mask > 0)]
    index_mean = np.average(masked_array)
    index_median = np.median(masked_array)
    index_std = np.std(masked_array)

    maxval = round(np.amax(masked_array), 8) # Auto bins will detect maxval to use for calculating centers
    b = 0  # Auto bins will always start from 0


    if not max_bin == None:
        maxval = max_bin # If bin_max is defined then overwrite maxval variable
    if not min_bin == None:
        b = min_bin # If bin_min is defined then overwrite starting value

    # Calculate histogram
    hist_val = [float(l[0]) for l in cv2.calcHist([masked_array.astype(np.float32)], [0], None, [bins], [0, 1])]
    bin_width = (maxval - b) / float(bins)
    bin_labels = [float(b)]
    plotting_labels = [float(b)]
    for i in range(bins - 1):
        b += bin_width
        bin_labels.append(b)
        plotting_labels.append(round(b, 2))

    # Make hist percentage for plotting
    pixels = cv2.countNonZero(mask)
    hist_percent = [(p / float(pixels)) * 100 for p in hist_val]

    params.debug = debug

    if histplot is True:
        dataset = pd.DataFrame({'Index Reflectance': bin_labels,
                                'Proportion of pixels (%)': hist_percent})
        fig_hist = (ggplot(data=dataset,
                           mapping=aes(x='Index Reflectance',
                                       y='Proportion of pixels (%)'))
                    + geom_line(color='red')
                    + scale_x_continuous(breaks=bin_labels, labels=plotting_labels))
        analysis_image = fig_hist
        if params.debug == 'print':
            fig_hist.save(os.path.join(params.debug_outdir, str(params.device) +
                                                            index_array.array_type + "hist.png"))
        elif params.debug == 'plot':
            print(fig_hist)

    outputs.add_observation(variable='mean_' + index_array.array_type,
                            trait='Average ' + index_array.array_type + ' reflectance',
                            method='plantcv.plantcv.hyperspectral.analyze_index', scale='reflectance', datatype=float,
                            value=float(index_mean), label='none')

    outputs.add_observation(variable='med_' + index_array.array_type,
                            trait='Median ' + index_array.array_type + ' reflectance',
                            method='plantcv.plantcv.hyperspectral.analyze_index', scale='reflectance', datatype=float,
                            value=float(index_median), label='none')

    outputs.add_observation(variable='std_' + index_array.array_type,
                            trait='Standard deviation ' + index_array.array_type + ' reflectance',
                            method='plantcv.plantcv.hyperspectral.analyze_index', scale='reflectance', datatype=float,
                            value=float(index_std), label='none')

    outputs.add_observation(variable='index_frequencies_' + index_array.array_type, trait='index frequencies',
                            method='plantcv.plantcv.analyze_index', scale='frequency', datatype=list,
                            value=hist_percent, label=bin_labels)

    if params.debug == "plot":
        plot_image(masked_array)
    elif params.debug == "print":
        print_image(img=masked_array, filename=os.path.join(params.debug_outdir, str(params.device) +
                                                            index_array.array_type + ".png"))
    # Store images
    outputs.images.append(analysis_image)

    return analysis_image
