import scipy.signal as sig
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import convolve
from scipy.datasets import electrocardiogram

ALPHA_S = 40  # atenuación en dB de la banda de rechazo
DELTA_F = 3  # Ancho de la ventana
ELECTROCARDIOGRAM_FREQUENCIES = [1, 50]  # Frecuencias de interés
LINE_FREQUENCY_50 = 50  # Notch
LINE_FREQUENCY_60 = 60  # Notch
SAMPLING_RATE = 400 # Frecuencia de muestreo
MAX_DELAY = 1  # segundos
MAX_NUM_TAPS = int(MAX_DELAY * SAMPLING_RATE)  # cantidad máxima de taps

# The electrocardiogram filter must preserve frecuencies between 0.05 and 100 Hz and remove the 50 Hz line noise
beta_kaiser = sig.kaiser_beta(ALPHA_S)
DeltaOmega = 2 * np.pi * DELTA_F / SAMPLING_RATE
Lh = np.ceil(1 + (ALPHA_S - 8) / (2.285 * DeltaOmega))  # cálculo del orden del filtro
Lh = int(Lh * 1.05)  # factor de seguridad correctivo
assert Lh <= MAX_NUM_TAPS, 'Ajuste los parámetros del filtro'  # toleramos una demora máxima de 1 segundos

window = ('kaiser', beta_kaiser)  # Ventana utilizada

Lh_line_supressor = Lh if Lh % 2 else Lh + 1
line_supressor_50_coefficients_fir = sig.firwin(Lh_line_supressor,
                                             [LINE_FREQUENCY_50 - DELTA_F / 2, LINE_FREQUENCY_50 + DELTA_F / 2],
                                             pass_zero='bandstop', fs=SAMPLING_RATE, window=window)
line_supressor_60_coefficients_fir = sig.firwin(Lh_line_supressor,
                                             [LINE_FREQUENCY_60 - DELTA_F / 2, LINE_FREQUENCY_60 + DELTA_F / 2],
                                             pass_zero='bandstop', fs=SAMPLING_RATE, window=window)
pass_band_ecg_coefficients_fir = sig.firwin(Lh, ELECTROCARDIOGRAM_FREQUENCIES, pass_zero=False, fs=SAMPLING_RATE,
                                            window=window)

# The Pan-Tompkins filter must preserve frecuencies between 5 and 15 Hz
pam_topkins_coefficients_iir = sig.iirfilter(2, [5, 15], 1, 20, 'bandpass', output='sos', fs=SAMPLING_RATE)


def plot_freq_response_dlti(filter_parameters, sampling_frecuency, input_type='ba',
                            plot_phase=False, zoom_area=None, title=None):
    sampling_time = 1 / sampling_frecuency
    if zoom_area:
        array_omega = 2 * np.pi * sampling_time * np.linspace(zoom_area[0], zoom_area[1], 10000)
    else:
        array_omega = None
    if input_type == 'sos':
        array_discrete_freq, freq_response = sig.sosfreqz(filter_parameters, worN=array_omega)
    elif input_type == 'ba' or input_type == 'zpk':
        sys_sig = sig.dlti(*filter_parameters)
        array_discrete_freq, freq_response = sys_sig.freqresp(array_omega)
    else:
        raise ValueError('imput_type must be "ba", "sos" or "zpk"')

    if plot_phase:
        fig_filter_response, ax_filter_response = plt.subplots(2, 1, figsize=(10, 10))
        ax_filter_response[0].plot(array_discrete_freq / (2 * np.pi * sampling_time),
                                   20 * np.log10(np.abs(freq_response)))
        ax_filter_response[0].set_ylabel("dB")
        ax_filter_response[0].set_xlabel("f", loc='right')
        ax_filter_response[0].grid()
        ax_filter_response[1].plot(array_discrete_freq / (2 * np.pi * sampling_time), np.angle(freq_response))
        ax_filter_response[1].set_ylabel(r"$\angle H(e^{j\Omega})$")
        ax_filter_response[1].set_yticks([-np.pi + i * np.pi / 4 for i in range(9)],
                                         ['$-\pi$', '$-\\frac{3}{4}\pi$', '$-\\frac{1}{2}\pi$',
                                          '$-\\frac{1}{4}\pi$', '$0$', '$\\frac{1}{4}\pi$',
                                          '$\\frac{1}{2}\pi$', '$\\frac{3}{4}\pi$', '$\pi$'])
        ax_filter_response[1].set_xlabel("f [Hz]", loc='right')
        ax_filter_response[1].grid()
    else:
        fig_filter_response, ax_filter_response = plt.subplots(1, 1, figsize=(10, 10))
        ax_filter_response.plot(array_discrete_freq / (2 * np.pi * sampling_time), 20 * np.log10(np.abs(freq_response)))
        ax_filter_response.set_ylabel("dB")
        ax_filter_response.set_xlabel("f [Hz]")
        ax_filter_response.grid()
    if title is not None:
        ax_filter_response.set_title(title)
    fig_filter_response.tight_layout()
    fig_filter_response.show()

if __name__ == '__main__':
    # print(f'The order of the line supressor filter (50Hz) is: {len(line_supressor_50_coefficients_fir)}')
    # plot_freq_response_dlti([line_supressor_50_coefficients_fir, 1], SAMPLING_RATE, plot_phase=False)
    # print(f'The order of the line supressor filter (60Hz) is: {len(line_supressor_60_coefficients_fir)}')
    # plot_freq_response_dlti([line_supressor_60_coefficients_fir, 1], SAMPLING_RATE, plot_phase=False)
    # print(f'The order of the pass band filter is: {len(pass_band_ecg_coefficients_fir)}')
    # plot_freq_response_dlti([pass_band_ecg_coefficients_fir, 1], SAMPLING_RATE, plot_phase=False, zoom_area=[0, 3])\
    # plot_freq_response_dlti(pam_topkins_coefficients_iir, SAMPLING_RATE, input_type='sos', plot_phase=False, zoom_area=[0.5, 60])
    # print(len(pam_topkins_coefficients_iir))
    # print(pam_topkins_coefficients_iir)

    electrocardiogram_signal = sig.resample(electrocardiogram(), int(len(electrocardiogram()) * SAMPLING_RATE / 360))
    #electrocardiogram_signal_filtered = sig.sosfilt(pam_topkins_coefficients_iir, electrocardiogram_signal)
    electrocardiogram_signal_filtered = []
    # manually filter the signal using the difference equation
    sample_buffer = np.zeros(3)
    filter_buffers = [np.zeros(3) for _ in range(len(pam_topkins_coefficients_iir))]

    for sample in electrocardiogram_signal:
        sample_buffer[2] = sample_buffer[1]
        sample_buffer[1] = sample_buffer[0]
        sample_buffer[0] = sample
        for i, (b0, b1, b2, a_0, a1, a2) in enumerate(pam_topkins_coefficients_iir):
            if i == 0:
                filter_buffers[i][2] = filter_buffers[i][1]
                filter_buffers[i][1] = filter_buffers[i][0]
                filter_buffers[i][0] = b0 * sample_buffer[0] + b1 * sample_buffer[1] + b2 * sample_buffer[2] - a1 * filter_buffers[i][1] - a2 * filter_buffers[i][2]
            else:
                filter_buffers[i][2] = filter_buffers[i][1]
                filter_buffers[i][1] = filter_buffers[i][0]
                filter_buffers[i][0] = b0 * filter_buffers[i-1][0] + b1 * filter_buffers[i-1][1] + b2 * filter_buffers[i-1][2] - a1 * filter_buffers[i][1] - a2 * filter_buffers[i][2]
        electrocardiogram_signal_filtered.append(filter_buffers[-1][0])
    plt.plot(electrocardiogram_signal_filtered[:10*SAMPLING_RATE])
    plt.show()

    input()
