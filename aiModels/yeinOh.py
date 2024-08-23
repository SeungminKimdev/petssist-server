import numpy as np
import torch
import torch.nn as nn
import scipy.signal
from scipy.signal import find_peaks

########## 전처리 관련
def get_bcg_respiration_signal(bcg: np.ndarray, SR: int) -> np.ndarray:
    bcg = bcg.flatten()
    filter_coeffs = scipy.signal.butter(5, 0.7, 'low', fs=SR)
    return scipy.signal.filtfilt(*filter_coeffs, bcg)

def get_bcg_heartrate_signal(bcg: np.ndarray, SR: float) -> np.ndarray:
    bcg = bcg.flatten()
    filter_coeffs = scipy.signal.butter(5, [5, 15], 'band', fs=SR)
    return scipy.signal.filtfilt(*filter_coeffs, bcg)

def normalize_signal(signal: np.ndarray, window_size: int = 70) -> np.ndarray:
    normalized_signal = np.zeros_like(signal)
    
    for i in range(len(signal)):
        start_index = max(0, i - window_size + 1)
        window = signal[start_index:i+1]
        min_val = np.min(window)
        max_val = np.max(window)
        if max_val != min_val:
            normalized_signal[i] = (signal[i] - min_val) / (max_val - min_val)
        else:
            normalized_signal[i] = 0.5
    return normalized_signal

def calculate_checked_values(signal: np.ndarray, window_size: int = 10, threshold: float = 0.75):
    checked_values = np.zeros_like(signal)
    max_min_diff = np.zeros_like(signal)
    upto = np.zeros_like(signal)

    for i in range(len(signal)):
        if i >= window_size:
            window = signal[i-window_size+1:i+1]
            max_val = np.max(window)
            min_val = np.min(window)
            max_min_diff[i] = max_val - min_val
            if max_min_diff[i] >= threshold:
                checked_values[i] = max_val
                if checked_values[i-1] == 0:
                    upto[i] = max_val

    return checked_values, max_min_diff, upto

def calculate_upto_result(upto: np.ndarray):
    peaks = np.where(upto > 0)[0]
    
    if len(peaks) == 0:
        return np.zeros_like(upto)

    intervals = np.diff(peaks)

    if len(intervals) == 0:
        half_avg_interval = 0
    else:
        half_avg_interval = np.mean(intervals) / 2

    result = np.zeros_like(upto)
    
    for i in range(len(peaks)):
        if i == 0:
            result[peaks[i]] = upto[peaks[i]]

        elif (i>0) and (intervals[i-1] >= half_avg_interval):
            result[peaks[i]] = upto[peaks[i]]            

    return result

def calculate_permin(result: np.ndarray, sr: int):
    peaks = np.where(result > 0)[0]
    intervals = np.diff(peaks) / sr
    bpm = 60.0 / np.mean(intervals)
    return bpm

def find_minima_and_calculate_rr(signal: np.ndarray, sampling_rate: int):
    minima, _ = find_peaks(-signal)
    num_inflection_points = len(minima)
    time_duration = len(signal) / sampling_rate
    breaths = num_inflection_points
    respiratory_rate = breaths / time_duration * 60
    
    return respiratory_rate, minima


def preprocess_data(time, bcg, sampling_rate=100, normwindow=70, checkwindow=10, thereshold=0.75, run_model=False):
    filtered_hr = get_bcg_heartrate_signal(bcg, sampling_rate)
    filtered_rp = get_bcg_respiration_signal(bcg, sampling_rate)
    
    normalized_signal_h = normalize_signal(filtered_hr, window_size=normwindow)
    normalized_signal_r = normalize_signal(filtered_rp, window_size=normwindow)
    
    checked_values_h, max_min_diff_h, upto_h = calculate_checked_values(normalized_signal_h, window_size=checkwindow, threshold=0.75)
    peak_h = calculate_upto_result(upto_h)
    bpm_h = calculate_permin(peak_h, sampling_rate)
    
    bpm_r, minima_r = find_minima_and_calculate_rr(normalized_signal_r, sampling_rate)
    
    combined_matrix_for_s = np.column_stack((time, filtered_hr, filtered_rp))
    
    if run_model :
        combined_matrix_for_m = np.stack([normalized_signal_h, normalized_signal_r, peak_h], axis=-1)
        return bpm_h, bpm_r, combined_matrix_for_s, combined_matrix_for_m
    
    return bpm_h, bpm_r, combined_matrix_for_s, None


########## 모델 관련
class Encoder1D(nn.Module):
    def __init__(self, nc):
        super(Encoder1D, self).__init__()
        ndf = 32
        
        self.main = nn.Sequential(
            nn.Conv1d(nc, ndf, 4, 2, 1), 
            nn.LeakyReLU(0.2, inplace=True), 
            nn.Conv1d(ndf, ndf * 2, 4, 2, 1), 
            nn.BatchNorm1d(ndf * 2),     
            nn.LeakyReLU(0.2, inplace=True), 
            nn.Conv1d(ndf * 2, ndf * 4, 4, 2, 1), 
            nn.BatchNorm1d(ndf * 4),       
            nn.LeakyReLU(0.2, inplace=True), 
            nn.Conv1d(ndf * 4, ndf * 8, 4, 2, 1),
            nn.BatchNorm1d(ndf * 8),   
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv1d(ndf * 8, ndf * 16, 5, 2, 1),
            nn.BatchNorm1d(ndf * 16),      
            nn.LeakyReLU(0.2, inplace=True), 
            nn.Conv1d(ndf * 16, 50, 17, 1, 0),
        )

    def forward(self, input):
        output = self.main(input)
        return output

class Decoder1D(nn.Module):
    def __init__(self, nc):
        super(Decoder1D, self).__init__()
        ngf = 32
        self.main=nn.Sequential(
            nn.ConvTranspose1d(50, ngf*16, 17, 1, 0),
            nn.BatchNorm1d(ngf*16),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 16, ngf * 8, 5, 2, 1),
            nn.BatchNorm1d(ngf * 8),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 8, ngf * 4, 4, 2, 1),
            nn.BatchNorm1d(ngf * 4),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 4, ngf*2, 4, 2, 1),
            nn.BatchNorm1d(ngf*2),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf * 2, ngf , 4, 2, 1),
            nn.BatchNorm1d(ngf),
            nn.ReLU(True),
            nn.ConvTranspose1d(ngf, nc, 4, 2, 1),
            nn.Sigmoid()
        )

    def forward(self, input):
        output = self.main(input)
        return output
    
class TSRNet_time(nn.Module):
    def __init__(self, enc_in=3):
        super(TSRNet_time, self).__init__()

        self.channel = enc_in

        self.time_encoder = Encoder1D(enc_in)
        self.time_decoder = Decoder1D(enc_in+1)

    def forward(self, time_bcg):
        time_features = self.time_encoder(time_bcg.transpose(-1,1))

        gen_time = self.time_decoder(time_features)
        gen_time = gen_time.transpose(-1, 1)

        return  (gen_time[:,:,0:self.channel],gen_time[:,:,self.channel:self.channel+1])
    

def TRSNET(model_path, input, threshold):
    model = TSRNet_time(enc_in=3)
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    time_bcg = torch.from_numpy(input).float()
    time_bcg = time_bcg.unsqueeze(0)
    
    model.eval()
    anomalies_detected = False
    
    with torch.no_grad():
        (gen_time, time_var) = model(time_bcg)
        time_err = (gen_time - time_bcg) ** 2
        reconstruction_error = torch.mean(time_err).item()

        if reconstruction_error > threshold:
            anomalies_detected = True
            return anomalies_detected, reconstruction_error

    if not anomalies_detected:
        return anomalies_detected, None